"""P1 confirmatory analysis.

This module implements the frozen analysis plan in ``prereg/analysis_plan.md``:
the ratio estimand ``E(k) = sum(J) / sum(C)``, the one-sided 5 pp
non-inferiority test at ``k = 4`` versus ``k = 32``, a paired question
bootstrap, the affine and quadratic energy fits, the optimal-depth identity,
the certification cost ``N*``, and the pre-registered margin/scoring
sensitivity.

Design rules that are enforced here, not left to the caller:

* The unit is a question. The primary test uses questions with valid rows at
  both depths; descriptive statistics use all valid rows at the depth.
* Invalid rows are excluded from sums and reported, never silently dropped.
* ``E = inf`` is retained when a depth has no correct answer.
* There are no outcome-based exclusions: no winsorizing, trimming, or
  imputation.
* Every bootstrap resamples questions, paired across depths, with a recorded
  seed.

The module is pure Python plus numpy/scipy and never touches a GPU.
"""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats as scipy_stats

CORRECT_KEYS: dict[str, str] = {
    "em": "correct_em",
    "lenient": "correct_lenient",
    "f1": "f1",
}
F1_THRESHOLD = 0.5
DEFAULT_SEED = 20261115


@dataclass(frozen=True)
class DepthSummary:
    """Per-depth descriptive statistics on the valid rows."""

    k: int
    n_valid: int
    n_invalid: int
    n_correct: int
    accuracy: float
    mean_j: float
    mean_gpu_j: float
    mean_retrieval_j: float
    e_per_correct: float

    def as_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["e_per_correct"] = (
            "inf" if math.isinf(self.e_per_correct) else round(self.e_per_correct, 6)
        )
        return row


@dataclass(frozen=True)
class PairedResult:
    """One-sided non-inferiority result for a paired binary contrast."""

    margin: float
    alpha: float
    n_pairs: int
    n_invalid_candidate: int
    n_invalid_reference: int
    mean_diff: float
    sd_diff: float
    se: float
    z: float
    p_value: float | None
    lower_bound: float
    upper_bound: float
    b: int
    c: int
    mcnemar_exact_p: float
    mcnemar_z_p: float
    non_inferior: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_bool(value: Any) -> bool:
    return str(value).strip() in {"1", "1.0", "True", "true"}


def _correct(row: dict[str, Any], key: str) -> int:
    if key == "f1":
        return int(float(row.get("f1", 0.0) or 0.0) >= F1_THRESHOLD)
    return int(_as_bool(row.get(CORRECT_KEYS[key], 0)))


def _is_valid(row: dict[str, Any]) -> bool:
    return str(row.get("valid", "1")).strip() in {"1", "1.0", "True", "true"}


def load_rows(raw_path: Path) -> list[dict[str, Any]]:
    """Load a raw sweep CSV as a list of dictionaries."""
    with Path(raw_path).open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def group_by_depth(rows: Iterable[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    """Group rows by depth, preserving input order within each depth."""
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["k"]), []).append(row)
    return dict(sorted(grouped.items()))


def summarize(rows: Sequence[dict[str, Any]], *, correct_key: str = "em") -> list[DepthSummary]:
    """Compute ``A(k)``, ``J(k)`` and ``E(k)`` from raw rows."""
    if not rows:
        raise ValueError("no raw rows")
    if correct_key not in CORRECT_KEYS:
        raise ValueError(f"unknown scoring rule {correct_key!r}")
    summaries: list[DepthSummary] = []
    for depth, depth_rows in group_by_depth(rows).items():
        valid = [row for row in depth_rows if _is_valid(row)]
        invalid = len(depth_rows) - len(valid)
        n_valid = len(valid)
        n_correct = sum(_correct(row, correct_key) for row in valid)
        sum_j = sum(float(row["j_total"]) for row in valid)
        sum_gpu = sum(float(row["j_gpu_calibrated"]) for row in valid)
        sum_retrieval = sum(float(row["j_retrieval_proxy"]) for row in valid)
        summaries.append(
            DepthSummary(
                k=int(depth),
                n_valid=n_valid,
                n_invalid=invalid,
                n_correct=n_correct,
                accuracy=(n_correct / n_valid) if n_valid else 0.0,
                mean_j=(sum_j / n_valid) if n_valid else 0.0,
                mean_gpu_j=(sum_gpu / n_valid) if n_valid else 0.0,
                mean_retrieval_j=(sum_retrieval / n_valid) if n_valid else 0.0,
                e_per_correct=(sum_j / n_correct) if n_correct else float("inf"),
            )
        )
    return summaries


def paired_questions(
    rows: Sequence[dict[str, Any]],
    candidate: int,
    reference: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Return paired valid rows for the two depths plus the excluded question IDs.

    A question is excluded from the primary test when it has no valid row at
    either depth. The exclusion list is reported; it is not an outcome-based
    exclusion.
    """
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        if _is_valid(row):
            by_key[(str(row["question_id"]), int(row["k"]))] = row
    candidate_rows: list[dict[str, Any]] = []
    reference_rows: list[dict[str, Any]] = []
    excluded: list[str] = []
    qids = sorted({str(row["question_id"]) for row in rows})
    for qid in qids:
        left = by_key.get((qid, candidate))
        right = by_key.get((qid, reference))
        if left is None or right is None:
            excluded.append(qid)
            continue
        candidate_rows.append(left)
        reference_rows.append(right)
    return candidate_rows, reference_rows, excluded


def noninferiority(
    candidate_correct: Sequence[int],
    reference_correct: Sequence[int],
    *,
    margin: float = 0.05,
    alpha: float = 0.05,
    n_invalid_candidate: int = 0,
    n_invalid_reference: int = 0,
) -> PairedResult:
    """One-sided paired non-inferiority test on paired binary outcomes.

    The null is ``E[C_candidate - C_reference] <= -margin``. The test statistic
    is the paired z statistic with the sample standard deviation of the
    differences. The one-sided lower confidence bound is reported alongside.
    An exact McNemar test against the no-difference null is reported as a
    secondary diagnostic; it is not the non-inferiority test.
    """
    if len(candidate_correct) != len(reference_correct):
        raise ValueError("candidate and reference must have the same length")
    if not candidate_correct:
        raise ValueError("at least one pair is required")
    if len(candidate_correct) < 2:
        raise ValueError("at least two pairs are required for a variance")
    if margin <= 0:
        raise ValueError("margin must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    a = np.asarray(candidate_correct, dtype=float)
    b = np.asarray(reference_correct, dtype=float)
    if not np.isin(a, (0.0, 1.0)).all() or not np.isin(b, (0.0, 1.0)).all():
        raise ValueError("correctness values must be 0/1")
    diff = a - b
    n = int(diff.size)
    mean_diff = float(diff.mean())
    sd = float(diff.std(ddof=1))
    se = sd / math.sqrt(n) if sd > 0 else 0.0
    z_alpha = float(scipy_stats.norm.ppf(1.0 - alpha))
    if se == 0.0:
        z_stat = math.inf if mean_diff + margin > 0 else -math.inf
        p_value = None
        lower = mean_diff
        upper = mean_diff
    else:
        z_stat = (mean_diff + margin) / se
        p_value = float(1.0 - scipy_stats.norm.cdf(z_stat))
        lower = mean_diff - z_alpha * se
        upper = mean_diff + z_alpha * se
    b_count = int(np.sum(diff > 0))
    c_count = int(np.sum(diff < 0))
    discordant = b_count + c_count
    if discordant == 0:
        exact_p = 1.0
        mcnemar_z = 1.0
    else:
        exact_p = float(
            scipy_stats.binomtest(b_count, discordant, 0.5, alternative="two-sided").pvalue
        )
        z0 = (abs(b_count - c_count) - 1.0) / math.sqrt(discordant)
        mcnemar_z = float(2.0 * (1.0 - scipy_stats.norm.cdf(max(z0, 0.0))))
    return PairedResult(
        margin=float(margin),
        alpha=float(alpha),
        n_pairs=n,
        n_invalid_candidate=int(n_invalid_candidate),
        n_invalid_reference=int(n_invalid_reference),
        mean_diff=mean_diff,
        sd_diff=sd,
        se=se,
        z=float(z_stat),
        p_value=None if p_value is None else float(p_value),
        lower_bound=float(lower),
        upper_bound=float(upper),
        b=b_count,
        c=c_count,
        mcnemar_exact_p=exact_p,
        mcnemar_z_p=mcnemar_z,
        non_inferior=bool(lower > -margin),
    )


def _percentile_interval(values: np.ndarray, confidence: float = 0.95) -> dict[str, Any]:
    """Percentile interval with explicit infinite and missing counts.

    A positive infinite tail forces an infinite upper bound and a negative
    infinite tail forces a negative infinite lower bound; neither is silently
    dropped. Missing (NaN) resamples are counted separately.
    """
    usable = values[np.isfinite(values)]
    n_pos_inf = int(np.isposinf(values).sum())
    n_neg_inf = int(np.isneginf(values).sum())
    n_missing = int(np.isnan(values).sum())
    if usable.size == 0:
        if n_neg_inf and n_pos_inf:
            lower, upper = float("-inf"), float("inf")
        elif n_neg_inf:
            lower, upper = float("-inf"), float("-inf")
        elif n_pos_inf:
            lower, upper = float("inf"), float("inf")
        else:
            lower, upper = None, None
        return {
            "lower": lower,
            "upper": upper,
            "n_inf": n_pos_inf + n_neg_inf,
            "n_missing": n_missing,
        }
    alpha = 1.0 - confidence
    lower = float(np.percentile(usable, 100.0 * alpha / 2.0))
    upper = float(np.percentile(usable, 100.0 * (1.0 - alpha / 2.0)))
    if n_pos_inf:
        upper = float("inf")
    if n_neg_inf:
        lower = float("-inf")
    return {
        "lower": lower,
        "upper": upper,
        "n_inf": n_pos_inf + n_neg_inf,
        "n_missing": n_missing,
    }


def _depth_matrices(
    rows: Sequence[dict[str, Any]], correct_key: str
) -> tuple[list[str], list[int], np.ndarray, np.ndarray]:
    """Build question-by-depth matrices with NaN for missing or invalid cells."""
    qids = sorted({str(row["question_id"]) for row in rows})
    depths = sorted({int(row["k"]) for row in rows})
    qid_index = {qid: index for index, qid in enumerate(qids)}
    depth_index = {depth: index for index, depth in enumerate(depths)}
    joules = np.full((len(qids), len(depths)), np.nan)
    correct = np.full((len(qids), len(depths)), np.nan)
    for row in rows:
        if not _is_valid(row):
            continue
        joules[qid_index[str(row["question_id"])], depth_index[int(row["k"])]] = float(
            row["j_total"]
        )
        correct[qid_index[str(row["question_id"])], depth_index[int(row["k"])]] = float(
            _correct(row, correct_key)
        )
    return qids, depths, joules, correct


def _affine_arrays(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    design = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(beta[0]), float(beta[1])


def bootstrap(
    rows: Sequence[dict[str, Any]],
    *,
    resamples: int = 10_000,
    seed: int = DEFAULT_SEED,
    margin: float = 0.05,
    correct_key: str = "em",
    candidate: int = 4,
    reference: int = 32,
    selected_depth: int | None = None,
) -> dict[str, Any]:
    """Paired question bootstrap for the P1 estimands.

    Questions are resampled with replacement; each resample keeps the same
    question across every depth, so the feasibility set, the optimal depth, and
    the certification cost are computed on a paired draw. A question missing a
    valid row at a depth contributes only to the depths where it is valid.
    """
    if resamples <= 0:
        raise ValueError("resamples must be positive")
    qids, depths, joules, correct = _depth_matrices(rows, correct_key)
    if candidate not in depths or reference not in depths:
        raise ValueError("candidate and reference depths must both be present")
    candidate_index = depths.index(candidate)
    reference_index = depths.index(reference)
    if selected_depth is None:
        selected_depth = candidate
    if selected_depth not in depths:
        raise ValueError("selected depth is not present")
    selected_index = depths.index(selected_depth)

    paired_mask = np.isfinite(joules[:, candidate_index]) & np.isfinite(joules[:, reference_index])
    paired_j_c = joules[paired_mask, candidate_index]
    paired_j_r = joules[paired_mask, reference_index]
    paired_c_c = correct[paired_mask, candidate_index]
    paired_c_r = correct[paired_mask, reference_index]
    if paired_j_c.size == 0:
        raise ValueError("no paired questions")
    n_pairs = int(paired_j_c.size)
    excluded = [qids[index] for index in np.flatnonzero(~paired_mask)]

    rng = np.random.default_rng(seed)
    n_questions = len(qids)
    n_depths = len(depths)
    accuracy = np.full((resamples, n_depths), np.nan)
    e_per_correct = np.full((resamples, n_depths), np.nan)
    savings = np.full(resamples, np.nan)
    difference = np.full(resamples, np.nan)
    identity = np.full(resamples, np.nan)
    n_star = np.full((resamples, n_depths), np.nan)
    depth_values = np.array(depths, dtype=float)
    order = np.argsort(depth_values)

    for r in range(resamples):
        idx = rng.integers(0, n_questions, size=n_questions)
        block_j = joules[idx]
        block_c = correct[idx]
        present = np.isfinite(block_j)
        counts = present.sum(axis=0)
        sum_j = np.where(present, block_j, 0.0).sum(axis=0)
        sum_c = np.where(present, block_c, 0.0).sum(axis=0)
        accuracy[r] = np.where(counts > 0, sum_c / counts, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            e_per_correct[r] = np.where(sum_c > 0, sum_j / sum_c, np.inf)

        both = np.isfinite(block_j[:, candidate_index]) & np.isfinite(block_j[:, reference_index])
        if both.any():
            # The paired contrast resamples the paired population itself, so the
            # paired n is fixed at n_pairs across resamples.
            paired_draw = rng.integers(0, n_pairs, size=n_pairs)
            c_c = paired_c_c[paired_draw]
            c_r = paired_c_r[paired_draw]
            difference[r] = c_c.mean() - c_r.mean()
            j_c = paired_j_c[paired_draw].sum()
            j_r = paired_j_r[paired_draw].sum()
            denominator_c = c_c.sum()
            denominator_r = c_r.sum()
            with np.errstate(divide="ignore", invalid="ignore"):
                e_c = j_c / denominator_c if denominator_c > 0 else np.inf
                e_r = j_r / denominator_r if denominator_r > 0 else np.inf
                savings[r] = 1.0 - e_c / e_r

        means = np.where(counts > 0, sum_j / counts, np.nan)
        finite = np.isfinite(means)
        if finite.sum() >= 2:
            a_fit, b_fit = _affine_arrays(depth_values[finite], means[finite])
            denominator = a_fit + b_fit * selected_depth
            e_j = selected_depth * b_fit / denominator if denominator != 0 else np.inf
            ordered = accuracy[r][order]
            position = int(np.where(order == selected_index)[0][0])
            if 0 < position < n_depths - 1:
                previous, following = position - 1, position + 1
                derivative = (ordered[following] - ordered[previous]) / (
                    depths[order[following]] - depths[order[previous]]
                )
            elif position == 0:
                derivative = (ordered[1] - ordered[0]) / (depths[order[1]] - depths[order[0]])
            else:
                derivative = (ordered[-1] - ordered[-2]) / (depths[order[-1]] - depths[order[-2]])
            a_selected = accuracy[r, selected_index]
            if np.isfinite(a_selected) and a_selected > 0:
                e_a = selected_depth * derivative / a_selected
                identity[r] = e_j - e_a

        total_energy = sum_j.sum()
        accuracy_row = accuracy[r]
        e_row = e_per_correct[r]
        delta_vector = e_row[reference_index] - e_row
        with np.errstate(divide="ignore", invalid="ignore"):
            n_star[r] = np.where(
                np.isfinite(total_energy)
                & np.isfinite(accuracy_row)
                & (accuracy_row > 0)
                & np.isfinite(delta_vector)
                & (delta_vector > 0),
                total_energy / (accuracy_row * delta_vector),
                np.nan,
            )

    feasible = accuracy >= (accuracy[:, reference_index : reference_index + 1] - margin)
    masked = np.where(feasible, e_per_correct, np.inf)
    best = np.argmin(masked, axis=1)
    no_selection = ~np.isfinite(masked).any(axis=1)
    best[no_selection] = -1
    p_optimal = {str(k): float(np.mean(best == index)) for index, k in enumerate(depths)}
    p_optimal["none"] = float(np.mean(no_selection))

    point_accuracy = {
        k: float(
            np.mean(
                [
                    _correct(row, correct_key)
                    for row in rows
                    if _is_valid(row) and int(row["k"]) == k
                ]
            )
        )
        for k in depths
    }
    point_e = {
        k: _ratio(
            np.array(
                [float(row["j_total"]) for row in rows if _is_valid(row) and int(row["k"]) == k]
            ),
            np.array(
                [
                    _correct(row, correct_key)
                    for row in rows
                    if _is_valid(row) and int(row["k"]) == k
                ]
            ),
        )
        for k in depths
    }

    return {
        "resamples": int(resamples),
        "seed": int(seed),
        "correct_key": correct_key,
        "margin": float(margin),
        "candidate": int(candidate),
        "reference": int(reference),
        "selected_depth": int(selected_depth),
        "n_pairs": n_pairs,
        "n_excluded": len(excluded),
        "excluded_question_ids": excluded,
        "savings_pct": {
            "point": float(
                100.0 * (1.0 - _ratio(paired_j_c, paired_c_c) / _ratio(paired_j_r, paired_c_r))
            ),
            "interval": _percentile_interval(savings * 100.0),
            "one_sided_lower": float(np.nanpercentile(savings * 100.0, 5.0))
            if np.isfinite(savings).any()
            else None,
            "n_undefined": int(np.isnan(savings).sum()),
        },
        "accuracy_difference": {
            "point": float(paired_c_c.mean() - paired_c_r.mean()),
            "interval": _percentile_interval(difference),
            "one_sided_lower": float(np.nanpercentile(difference, 5.0))
            if np.isfinite(difference).any()
            else None,
        },
        "e_per_correct": {
            str(k): {
                "point": point_e[k],
                "interval": _percentile_interval(e_per_correct[:, index]),
            }
            for index, k in enumerate(depths)
        },
        "accuracy": {
            str(k): {
                "point": point_accuracy[k],
                "interval": _percentile_interval(accuracy[:, index]),
            }
            for index, k in enumerate(depths)
        },
        "identity_gap": _percentile_interval(identity),
        "n_star": {
            str(k): _percentile_interval(n_star[:, index]) for index, k in enumerate(depths)
        },
        "p_k_optimal": p_optimal,
        "n_infinite_e_resamples": {
            str(k): int(np.isinf(e_per_correct[:, index]).sum()) for index, k in enumerate(depths)
        },
    }


def _ratio(joules: np.ndarray, correct: np.ndarray) -> float:
    denominator = float(correct.sum())
    return float(joules.sum() / denominator) if denominator > 0 else float("inf")


def affine_lack_of_fit(points: Sequence[tuple[int, float]]) -> dict[str, Any]:
    """Fit ``J(k) = a + b k`` and test a quadratic term.

    The lack-of-fit test compares the affine fit with a quadratic fit by an
    extra-sum-of-squares F test. With seven depths the quadratic has four
    residual degrees of freedom.
    """
    if len(points) < 4:
        raise ValueError("at least four points are required for a lack-of-fit test")
    x = np.array([float(k) for k, _ in points])
    y = np.array([float(value) for _, value in points])
    design_linear = np.column_stack([np.ones_like(x), x])
    design_quad = np.column_stack([np.ones_like(x), x, x**2])
    beta_linear, *_ = np.linalg.lstsq(design_linear, y, rcond=None)
    beta_quad, *_ = np.linalg.lstsq(design_quad, y, rcond=None)
    resid_linear = y - design_linear @ beta_linear
    resid_quad = y - design_quad @ beta_quad
    sse_linear = float(resid_linear @ resid_linear)
    sse_quad = float(resid_quad @ resid_quad)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    df_num = 1
    df_den = len(y) - design_quad.shape[1]
    if sse_quad <= 0.0:
        f_stat = math.inf if sse_linear > 0.0 else 0.0
        p_value = 0.0 if sse_linear > 0.0 else 1.0
    else:
        f_stat = max(0.0, ((sse_linear - sse_quad) / df_num) / (sse_quad / df_den))
        p_value = float(1.0 - scipy_stats.f.cdf(f_stat, df_num, df_den))
    return {
        "a": float(beta_linear[0]),
        "b": float(beta_linear[1]),
        "r2": float(1.0 - sse_linear / ss_tot) if ss_tot > 0 else 1.0,
        "quadratic_coefficient": float(beta_quad[2]),
        "lack_of_fit_f": float(f_stat),
        "lack_of_fit_p": p_value,
        "df_num": df_num,
        "df_den": df_den,
        "n": len(points),
        "residuals": [float(v) for v in resid_linear],
    }


def context_share(summaries: Sequence[DepthSummary], slope: float) -> dict[int, float]:
    """Context-side share ``S(k) = (J_ret + J_pre) / J`` with ``J_pre = b k``."""
    shares: dict[int, float] = {}
    for summary in summaries:
        denominator = summary.mean_j
        if denominator <= 0:
            shares[summary.k] = float("nan")
            continue
        prefill = slope * summary.k
        shares[summary.k] = (summary.mean_retrieval_j + prefill) / denominator
    return shares


def identity_gap(
    summaries: Sequence[DepthSummary],
    *,
    a: float,
    b: float,
    depth: int,
) -> dict[str, Any]:
    """Compute ``epsilon_J - epsilon_A`` at one depth by finite differences."""
    by_k = {summary.k: summary for summary in summaries}
    depths = sorted(by_k)
    if depth not in by_k:
        raise ValueError(f"depth {depth} is not in the estimates")
    index = depths.index(depth)
    energy_elasticity = depth * b / (a + b * depth) if (a + b * depth) != 0 else float("inf")
    if 0 < index < len(depths) - 1:
        previous, following = depths[index - 1], depths[index + 1]
        step = (following - previous) / 2.0
        derivative = (by_k[following].accuracy - by_k[previous].accuracy) / (following - previous)
        method = "central"
    elif index == 0:
        following = depths[1]
        step = following - depth
        derivative = (by_k[following].accuracy - by_k[depth].accuracy) / step
        method = "forward"
    else:
        previous = depths[-2]
        step = depth - previous
        derivative = (by_k[depth].accuracy - by_k[previous].accuracy) / step
        method = "backward"
    accuracy_elasticity = (
        depth * derivative / by_k[depth].accuracy if by_k[depth].accuracy else float("inf")
    )
    return {
        "depth": int(depth),
        "epsilon_j": float(energy_elasticity),
        "epsilon_a": float(accuracy_elasticity),
        "gap": float(energy_elasticity - accuracy_elasticity),
        "method": method,
        "step": float(step),
    }


def certification_cost(
    summaries: Sequence[DepthSummary],
    *,
    selected_depth: int,
    reference_depth: int = 32,
) -> dict[str, Any]:
    """Break-even ``N*`` from the measured sweep energy."""
    by_k = {summary.k: summary for summary in summaries}
    if selected_depth not in by_k or reference_depth not in by_k:
        raise ValueError("selected and reference depths must both be present")
    total_energy = sum(summary.mean_j * summary.n_valid for summary in summaries)
    selected = by_k[selected_depth]
    reference = by_k[reference_depth]
    delta = reference.e_per_correct - selected.e_per_correct
    if not math.isfinite(delta) or delta <= 0 or selected.accuracy <= 0:
        return {
            "selected_depth": selected_depth,
            "reference_depth": reference_depth,
            "total_sweep_j": float(total_energy),
            "delta_e_per_correct": float(delta),
            "n_star": None,
            "note": "No positive break-even; the selected depth is not cheaper per correct answer.",
        }
    n_star = total_energy / (selected.accuracy * delta)
    return {
        "selected_depth": selected_depth,
        "reference_depth": reference_depth,
        "total_sweep_j": float(total_energy),
        "delta_e_per_correct": float(delta),
        "n_star": float(n_star),
        "note": "Break-even calculation, not a deployment guarantee.",
    }


def margin_sensitivity(
    summaries: Sequence[DepthSummary],
    *,
    margins: Sequence[float] = (0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10),
    reference_depth: int = 32,
) -> list[dict[str, Any]]:
    """Select the cheapest feasible depth at each margin."""
    by_k = {summary.k: summary for summary in summaries}
    if reference_depth not in by_k:
        raise ValueError("reference depth is not present")
    reference_accuracy = by_k[reference_depth].accuracy
    rows: list[dict[str, Any]] = []
    for margin in margins:
        feasible = [
            summary for summary in summaries if summary.accuracy >= reference_accuracy - margin
        ]
        if not feasible:
            rows.append({"margin_pp": 100.0 * margin, "selected_depth": None, "savings_pct": None})
            continue
        selected = min(feasible, key=lambda summary: (summary.e_per_correct, summary.k))
        savings = (
            100.0 * (1.0 - selected.e_per_correct / by_k[reference_depth].e_per_correct)
            if math.isfinite(by_k[reference_depth].e_per_correct)
            else float("nan")
        )
        rows.append(
            {
                "margin_pp": 100.0 * margin,
                "selected_depth": selected.k,
                "accuracy": selected.accuracy,
                "e_per_correct": selected.e_per_correct,
                "savings_pct": savings,
                "feasible_depths": [summary.k for summary in feasible],
            }
        )
    return rows


def scoring_sensitivity(
    rows: Sequence[dict[str, Any]],
    *,
    margins: Sequence[float] = (0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10),
    reference_depth: int | None = None,
) -> dict[str, Any]:
    """Repeat selection and savings under EM, lenient span, and F1 >= 0.5."""
    results: dict[str, Any] = {}
    for key in CORRECT_KEYS:
        summaries = summarize(rows, correct_key=key)
        reference = (
            reference_depth
            if reference_depth is not None
            else max(summary.k for summary in summaries)
        )
        results[key] = margin_sensitivity(summaries, margins=margins, reference_depth=reference)
    return results


def evaluate_gates(
    summaries: Sequence[DepthSummary],
    *,
    fit: dict[str, Any],
    primary: PairedResult,
    savings_pct: float,
    p_k_optimal: dict[str, float],
    context_shares: dict[int, float],
    selected_depth: int,
    repeat: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate K1-K7 and G1-G5 against the frozen thresholds.

    The gates are evaluated once on the pre-specified population. Missing or
    undefined inputs are reported as ``None``, never as a pass.
    """
    thresholds = (config or {}).get("gates", {})
    by_k = {summary.k: summary for summary in summaries}
    depths = sorted(by_k)
    reference = by_k.get(32)
    baseline = by_k.get(1) or by_k.get(0)
    relative_effect = None
    if reference is not None and baseline is not None and math.isfinite(baseline.e_per_correct):
        relative_effect = reference.e_per_correct / baseline.e_per_correct - 1.0
    k1 = relative_effect is not None and relative_effect >= float(
        thresholds.get("k1_min_relative_energy_effect", 0.10)
    )

    boundary = selected_depth in (depths[0], depths[-1])
    k3 = float(p_k_optimal.get(str(selected_depth), 0.0)) >= float(
        thresholds.get("k3_min_posterior_prob", 0.80)
    )

    share_values = [context_shares.get(k) for k in depths]
    finite_shares = [value for value in share_values if value is not None]
    flat = bool(len(finite_shares) >= 2 and max(finite_shares) - min(finite_shares) < 0.05)
    k4_share = context_shares.get(selected_depth)
    k4 = k4_share is not None and not (
        k4_share < float(thresholds.get("k4_context_share_floor", 0.05)) and flat
    )

    probabilities = sorted(
        (
            (float(probability), int(depth))
            for depth, probability in p_k_optimal.items()
            if depth != "none"
        ),
        reverse=True,
    )
    chosen: list[int] = []
    cumulative = 0.0
    for probability, depth in probabilities:
        chosen.append(depth)
        cumulative += probability
        if cumulative >= 0.95:
            break
    span = max(chosen) - min(chosen) if chosen else None
    k5 = span is not None and span <= 1

    repeat_cv = None
    if repeat is not None:
        repeat_cv = repeat.get("cv_max")
        if repeat_cv is None:
            repeat_cv = repeat.get("cv_median")
    k7 = None
    if repeat_cv is not None and relative_effect is not None:
        k7 = bool(
            float(repeat_cv) <= float(thresholds.get("k7_max_cv", 0.20))
            and 2.0 * float(repeat_cv) < relative_effect
        )

    interior = not boundary
    g1 = bool(
        primary.non_inferior
        and savings_pct >= float(thresholds.get("g1_min_savings_pct", 20.0))
        and interior
    )
    increasing = bool(
        len(finite_shares) >= 2
        and all(
            following >= previous - 1e-12
            for previous, following in zip(finite_shares, finite_shares[1:], strict=False)
        )
    )

    return {
        "K1": {"value": relative_effect, "passed": bool(k1)},
        "K2": {
            "selected_depth": selected_depth,
            "boundary": bool(boundary),
            "fired": bool(boundary),
            "passed": bool(not boundary),
        },
        "K3": {"p_k_optimal": p_k_optimal.get(str(selected_depth)), "passed": bool(k3)},
        "K4": {
            "context_share": k4_share,
            "flat": flat,
            "passed": bool(k4),
        },
        "K5": {
            "span_95": span,
            "depths_95": chosen,
            "passed": bool(k5),
        },
        "K6": {"note": "oracle gain is a P3 analysis", "passed": None},
        "K7": {
            "repeat_cv_max": repeat_cv,
            "relative_effect": relative_effect,
            "passed": k7,
            "note": None if k7 is not None else "repeat.json is required for K7",
        },
        "G1": {
            "non_inferior": primary.non_inferior,
            "savings_pct": savings_pct,
            "interior": interior,
            "passed": g1,
        },
        "G2": {
            "upper_bound_on_loss_pp": -100.0 * primary.lower_bound,
            "p_k_optimal": p_k_optimal.get(str(selected_depth)),
            "passed": bool(
                -100.0 * primary.lower_bound <= float(thresholds.get("g2_max_upper_bound_pp", 5.0))
                and float(p_k_optimal.get(str(selected_depth), 0.0))
                >= float(thresholds.get("g2_min_posterior_prob", 0.80))
            ),
        },
        "G3": {
            "context_share": k4_share,
            "low": float(thresholds.get("g3_context_share_low", 0.10)),
            "high": float(thresholds.get("g3_context_share_high", 0.70)),
            "increasing": increasing,
            "passed": bool(
                k4_share is not None
                and float(thresholds.get("g3_context_share_low", 0.10))
                <= k4_share
                <= float(thresholds.get("g3_context_share_high", 0.70))
                and increasing
            ),
        },
        "G4": {"note": "policy capture is a P3 analysis", "passed": None},
        "G5": {"note": "replication is P2", "passed": None},
    }


def _load_prereg_config(root: Path | None) -> dict[str, Any]:
    if root is None:
        return {}
    path = root / "configs" / "analysis" / "prereg.toml"
    if not path.is_file():
        return {}
    try:
        import tomllib

        with path.open("rb") as handle:
            return tomllib.load(handle)
    except Exception:
        return {}


def _repeat_status(raw_path: Path) -> dict[str, Any] | None:
    repeat_path = raw_path.parent / "repeat.json"
    if not repeat_path.is_file():
        return None
    try:
        return json.loads(repeat_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _calibration_status(raw_path: Path) -> dict[str, Any]:
    blocks_path = raw_path.parent / "blocks.json"
    if not blocks_path.is_file():
        return {"measured": False, "applied": False, "all_passed": None, "depths": []}
    payload = json.loads(blocks_path.read_text(encoding="utf-8"))
    return {
        "measured": True,
        "applied": bool(payload.get("applied")),
        "all_passed": bool(payload.get("all_passed")),
        "depths": [
            {
                "k": item.get("k"),
                "factor_csv": item.get("factor_csv"),
                "factor_block": item.get("factor_block"),
                "consistency": item.get("consistency"),
                "passed": item.get("passed"),
            }
            for item in payload.get("depths", [])
        ],
    }


def write_p1_analysis(
    raw_path: Path,
    out_dir: Path,
    *,
    run_id: str,
    root: Path | None = None,
    config: dict[str, Any] | None = None,
    seed: int | None = None,
    resamples: int | None = None,
    candidate: int = 4,
    reference: int = 32,
    margin: float | None = None,
) -> Path:
    """Write the P1 confirmatory outputs for one registered run."""
    prereg = _load_prereg_config(root)
    seed = int(seed if seed is not None else prereg.get("seed", DEFAULT_SEED))
    resamples = int(
        resamples if resamples is not None else prereg.get("bootstrap", {}).get("resamples", 10_000)
    )
    margin = float(
        margin if margin is not None else prereg.get("primary", {}).get("margin_pp", 5.0) / 100.0
    )
    rows = load_rows(raw_path)
    primary_summaries = summarize(rows, correct_key="em")
    empty_depths = [summary.k for summary in primary_summaries if summary.n_valid == 0]
    if empty_depths:
        raise ValueError(f"depths with no valid rows: {empty_depths}")
    by_k = {summary.k: summary for summary in primary_summaries}
    if candidate not in by_k or reference not in by_k:
        raise ValueError("candidate and reference depths must both be present")
    fit = affine_lack_of_fit([(summary.k, summary.mean_j) for summary in primary_summaries])
    shares = context_share(primary_summaries, fit["b"])
    feasible = [
        summary
        for summary in primary_summaries
        if summary.accuracy >= by_k[reference].accuracy - margin
    ]
    if not feasible:
        raise ValueError("no depth is feasible at the pre-registered margin")
    selected_depth = min(feasible, key=lambda summary: (summary.e_per_correct, summary.k)).k

    cand_rows, ref_rows, excluded = paired_questions(rows, candidate, reference)
    n_invalid_candidate = sum(
        1 for row in rows if int(row["k"]) == candidate and not _is_valid(row)
    )
    n_invalid_reference = sum(
        1 for row in rows if int(row["k"]) == reference and not _is_valid(row)
    )
    primary = noninferiority(
        [_correct(row, "em") for row in cand_rows],
        [_correct(row, "em") for row in ref_rows],
        margin=margin,
        n_invalid_candidate=n_invalid_candidate,
        n_invalid_reference=n_invalid_reference,
    )
    bootstrap_result = bootstrap(
        rows,
        resamples=resamples,
        seed=seed,
        margin=margin,
        correct_key="em",
        candidate=candidate,
        reference=reference,
        selected_depth=selected_depth,
    )
    secondary = noninferiority(
        [_correct(row, "em") for row in cand_rows],
        [_correct(row, "em") for row in ref_rows],
        margin=0.02,
        n_invalid_candidate=n_invalid_candidate,
        n_invalid_reference=n_invalid_reference,
    )
    savings = float(bootstrap_result["savings_pct"]["point"])
    gaps = {
        str(summary.k): identity_gap(primary_summaries, a=fit["a"], b=fit["b"], depth=summary.k)
        for summary in primary_summaries
    }
    gaps[str(selected_depth)]["lower"] = bootstrap_result["identity_gap"]["lower"]
    gaps[str(selected_depth)]["upper"] = bootstrap_result["identity_gap"]["upper"]

    certification: dict[str, Any] = {}
    feasible_depths = {summary.k for summary in feasible}
    for summary in primary_summaries:
        point = certification_cost(
            primary_summaries, selected_depth=summary.k, reference_depth=reference
        )
        certification[str(summary.k)] = {
            **point,
            "feasible": summary.k in feasible_depths,
            "interval": (
                bootstrap_result["n_star"][str(summary.k)] if summary.k in feasible_depths else None
            ),
        }
    cert = certification[str(selected_depth)]

    margins = margin_sensitivity(primary_summaries)
    scoring = scoring_sensitivity(rows)
    calibration = _calibration_status(raw_path)
    repeat = _repeat_status(raw_path)
    gates = evaluate_gates(
        primary_summaries,
        fit=fit,
        primary=primary,
        savings_pct=savings,
        p_k_optimal=bootstrap_result["p_k_optimal"],
        context_shares=shares,
        selected_depth=selected_depth,
        repeat=repeat,
        config=config or prereg,
    )
    fit = {
        **fit,
        "b_positive": bool(fit["b"] > 0),
        "r2_at_least_0.95": bool(fit["r2"] >= 0.95),
        "lack_of_fit_not_rejected": bool(fit["lack_of_fit_p"] > 0.05),
        "h1_supported": bool(fit["b"] > 0 and fit["r2"] >= 0.95 and fit["lack_of_fit_p"] > 0.05),
        "context_share": {str(k): v for k, v in shares.items()},
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_estimates(out_dir / "estimates.csv", primary_summaries, shares)
    _write_identity(out_dir / "identity.csv", gaps)
    _write_json(
        out_dir / "noninferiority.json",
        {
            "run_id": run_id,
            "primary": primary.as_dict(),
            "secondary_2pp": {**secondary.as_dict(), "role": "estimation_only"},
            "paired_n": primary.n_pairs,
            "excluded_questions": len(excluded),
            "excluded_question_ids": excluded,
            "savings_pct": savings,
            "calibration": calibration,
            "decision": {
                "non_inferior": primary.non_inferior,
                "savings_at_least_20pct": savings >= 20.0,
                "supported": bool(primary.non_inferior and savings >= 20.0),
            },
        },
    )
    _write_json(out_dir / "bootstrap.json", bootstrap_result)
    _write_json(out_dir / "certification.json", certification)
    _write_json(out_dir / "fit.json", fit)
    _write_json(out_dir / "sensitivity.json", {"margins": margins, "scoring": scoring})
    _write_json(out_dir / "gates.json", gates)
    _write_json(
        out_dir / "metadata.json",
        {
            "run_id": run_id,
            "candidate_depth": candidate,
            "reference_depth": reference,
            "selected_depth": selected_depth,
            "margin": margin,
            "seed": seed,
            "resamples": resamples,
            "n_rows": len(rows),
            "n_valid": sum(summary.n_valid for summary in primary_summaries),
            "n_invalid": sum(summary.n_invalid for summary in primary_summaries),
            "calibrated": bool(calibration["applied"]),
            "calibration": calibration,
            "config_sha256": None,
            "prereg_sha256": None,
            "git_commit": None,
            "phase": None,
        },
    )
    _write_report(
        out_dir / "report.md",
        run_id=run_id,
        summaries=primary_summaries,
        fit=fit,
        primary=primary,
        savings=savings,
        p_k_optimal=bootstrap_result["p_k_optimal"],
        gates=gates,
        selected_depth=selected_depth,
        shares=shares,
        calibration=calibration,
        certification=cert,
    )
    metadata_path = out_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    manifest_path = raw_path.parent / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata.update(
            {
                "config_sha256": manifest.get("config_sha256"),
                "prereg_sha256": manifest.get("prereg_sha256"),
                "git_commit": manifest.get("git_commit"),
                "phase": manifest.get("phase"),
            }
        )
    _write_json(metadata_path, metadata)
    return out_dir


def _json_safe(value: Any) -> Any:
    """Convert non-finite floats to explicit strings so the JSON is valid."""
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return value
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(_json_safe(payload), indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def _write_estimates(
    path: Path, summaries: Sequence[DepthSummary], shares: dict[int, float]
) -> None:
    fields = [
        "k",
        "n_valid",
        "n_invalid",
        "n_correct",
        "accuracy",
        "mean_j",
        "mean_gpu_j",
        "mean_retrieval_j",
        "e_per_correct",
        "context_share",
        "retrieval_share",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for summary in summaries:
            row = summary.as_row()
            row["context_share"] = shares.get(summary.k)
            row["retrieval_share"] = (
                summary.mean_retrieval_j / summary.mean_j if summary.mean_j > 0 else None
            )
            writer.writerow(row)


def _write_identity(path: Path, gaps: dict[str, dict[str, Any]]) -> None:
    fields = ["depth", "epsilon_j", "epsilon_a", "gap", "lower", "upper", "method", "step"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for gap in gaps.values():
            writer.writerow({field: gap.get(field) for field in fields})


def _write_report(
    path: Path,
    *,
    run_id: str,
    summaries: Sequence[DepthSummary],
    fit: dict[str, Any],
    primary: PairedResult,
    savings: float,
    p_k_optimal: dict[str, float],
    gates: dict[str, Any],
    selected_depth: int,
    shares: dict[int, float],
    calibration: dict[str, Any],
    certification: dict[str, Any],
) -> None:
    lines = [
        f"# P1 confirmatory analysis - {run_id}",
        "",
        f"Calibration: **{'applied' if calibration.get('applied') else 'not applied'}** "
        f"(all depths passed: {calibration.get('all_passed')}).",
        "",
        "| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct | S(k) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        e_value = "inf" if math.isinf(summary.e_per_correct) else f"{summary.e_per_correct:.2f}"
        share = shares.get(summary.k)
        share_text = "n/a" if share is None else f"{share:.3f}"
        lines.append(
            f"| {summary.k} | {summary.n_valid} | {summary.n_invalid} | "
            f"{summary.accuracy:.4f} | {summary.mean_j:.2f} | {e_value} | {share_text} |"
        )
    lines.extend(
        [
            "",
            f"Affine fit: `J(k) = {fit['a']:.4f} + {fit['b']:.4f} k`, R² = {fit['r2']:.4f}.",
            f"Quadratic lack-of-fit: F = {fit['lack_of_fit_f']:.3f}, "
            f"p = {fit['lack_of_fit_p']:.4f}; H1 supported: {fit.get('h1_supported')}.",
            "",
            "## Primary 5 pp result",
            "",
            f"- Paired n = {primary.n_pairs}; discordant b = {primary.b}, c = {primary.c}; "
            f"invalid rows at k=4/k=32 = {primary.n_invalid_candidate}/"
            f"{primary.n_invalid_reference}.",
            f"- Mean difference A(4) - A(32) = {100.0 * primary.mean_diff:.2f} pp "
            f"(one-sided 95% lower bound {100.0 * primary.lower_bound:.2f} pp).",
            f"- McNemar exact p (no-difference null) = {primary.mcnemar_exact_p:.4g}; "
            f"continuity-corrected z p = {primary.mcnemar_z_p:.4g}.",
            f"- One-sided p = {primary.p_value:.4g}; non-inferior: {primary.non_inferior}."
            if primary.p_value is not None
            else f"- One-sided p = not defined (zero paired variance); non-inferior: {primary.non_inferior}.",
            f"- Energy savings = {savings:.2f}% (pre-registered floor 20%).",
            f"- Decision: {'SUPPORTED' if primary.non_inferior and savings >= 20.0 else 'NOT SUPPORTED'}.",
            "",
            f"Selected depth at the 5 pp gate: k = {selected_depth}.",
            f"Bootstrap P(k* optimal): {json.dumps(p_k_optimal)}.",
            f"N* at the selected depth: {json.dumps(certification)}.",
            "",
            "## Gates",
            "",
            "| Gate | Value | Passed |",
            "|---|---|---|",
        ]
    )
    for gate, payload in gates.items():
        lines.append(f"| {gate} | {json.dumps(payload)} | {payload.get('passed')} |")
    if not calibration.get("applied"):
        lines.extend(
            [
                "",
                "Absolute `J`, `E`, `N*`, and `S(k)` are **uncalibrated** and are not claimed. "
                "The primary savings and the accuracy contrast are the calibration-invariant result.",
            ]
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
