#!/usr/bin/env python
"""21 - Phase 6 inference repair.

Adds the analyses that a methods reviewer checks before accepting the negative
result. Nothing here changes a gate or re-thresholds a frozen criterion; every
number is derived from registered run rows.

Outputs (``analysis/phase6``):

* ``cluster_robust.json`` - paired contrasts with context-clustered SEs and the
  design effect.
* ``token_vs_depth.json`` - ``J = a + b k`` against ``J = a + c T`` (prompt
  tokens) with cluster-robust SEs and information criteria.
* ``affine_ci.json`` - uncertainty on the affine intercept and slope (``k >= 1``).
* ``selection.json`` - cross-fitted selection of ``k*`` and the winner's curse.
* ``policy_ci.json`` - bootstrap interval for the P3 capture ratio.
* ``gold_rank.json`` - accuracy at fixed gold rank 1 versus depth.
* ``reader_subset.json`` - three readers on identical question IDs.
* ``price_of_guarantee.json`` - savings purchased by loosening the margin.
* ``cancellation.json`` - recall/precision decomposition per arm.
* ``report.md`` - human-readable summary.

CPU only; no GPU, no network, no new runs.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.stats.policy import _predict  # noqa: E402

P1 = "squad_qwen4b_p1"
READERS = ("squad_qwen4b_p1", "squad_qwen15b_p2", "squad_llama3b_p2")
READER_LABELS = {
    "squad_qwen4b_p1": "Qwen3.5-4B (primary)",
    "squad_qwen15b_p2": "Qwen2.5-1.5B",
    "squad_llama3b_p2": "Llama-3.2-3B",
}
SEED = 20261115
BOOT = 10000


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row.get("valid", "1") == "1"]


def _correct_by_depth(rows: list[dict[str, str]]) -> dict[str, dict[int, int]]:
    out: dict[str, dict[int, int]] = defaultdict(dict)
    for row in rows:
        out[str(row["question_id"])][int(row["k"])] = int(row["correct_em"])
    return dict(out)


def _cluster_robust_mean(values: list[float], clusters: list[str]) -> dict[str, float]:
    """Mean with iid and cluster-robust standard errors."""
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    mean = float(arr.mean())
    iid_var = float(arr.var(ddof=1) / n)
    groups: dict[str, list[float]] = defaultdict(list)
    for value, key in zip(values, clusters, strict=True):
        groups[key].append(value)
    g = len(groups)
    ss = 0.0
    for members in groups.values():
        residual = sum(members) - len(members) * mean
        ss += residual * residual
    # CR0 with the usual finite-sample factor.
    cluster_var = (g / (g - 1)) * (ss / (n * n)) if g > 1 else iid_var
    design_effect = cluster_var / iid_var if iid_var > 0 else float("nan")
    return {
        "n": n,
        "n_clusters": g,
        "mean": mean,
        "se_iid": math.sqrt(iid_var),
        "se_cluster": math.sqrt(cluster_var),
        "design_effect": design_effect,
        "ci_iid": [mean - 1.96 * math.sqrt(iid_var), mean + 1.96 * math.sqrt(iid_var)],
        "ci_cluster": [mean - 1.96 * math.sqrt(cluster_var), mean + 1.96 * math.sqrt(cluster_var)],
        "mean_cluster_size": n / g if g else float("nan"),
    }


def _ols(x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """OLS with classical and cluster-robust SEs (clusters supplied separately)."""
    xtx_inv = np.linalg.inv(x.T @ x)
    beta = xtx_inv @ (x.T @ y)
    resid = y - x @ beta
    n, p = x.shape
    ssr = float(resid @ resid)
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ssr / sst if sst > 0 else float("nan")
    sigma2 = ssr / (n - p)
    cov = sigma2 * xtx_inv
    aic = n * math.log(ssr / n) + 2 * p if ssr > 0 else float("-inf")
    bic = n * math.log(ssr / n) + p * math.log(n) if ssr > 0 else float("-inf")
    return {
        "beta": beta.tolist(),
        "se": np.sqrt(np.diag(cov)).tolist(),
        "resid": resid,
        "r2": r2,
        "rmse": math.sqrt(ssr / n),
        "aic": aic,
        "bic": bic,
        "n": n,
        "p": p,
    }


def _cluster_se(
    x: np.ndarray, resid: np.ndarray, beta: np.ndarray, clusters: list[str]
) -> list[float]:
    """CR0 sandwich standard errors."""
    xtx_inv = np.linalg.inv(x.T @ x)
    groups: dict[str, list[int]] = defaultdict(list)
    for index, key in enumerate(clusters):
        groups[key].append(index)
    g = len(groups)
    n, p = x.shape
    meat = np.zeros((p, p))
    for members in groups.values():
        idx = np.asarray(members)
        score = x[idx].T @ resid[idx]
        meat += np.outer(score, score)
    factor = (g / (g - 1)) * ((n - 1) / (n - p)) if g > 1 else 1.0
    cov = factor * xtx_inv @ meat @ xtx_inv
    return np.sqrt(np.diag(cov)).tolist()


def _bootstrap_capture(
    policy_depth: list[int],
    correct: list[dict[int, int]],
    energy: list[dict[int, float]],
    static_depth: int,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Bootstrap the capture ratio of the matched no-abstention oracle gap."""
    n = len(policy_depth)

    def _capture(indices: np.ndarray) -> float:
        total_j = sum(energy[i][policy_depth[i]] for i in indices)
        total_c = sum(correct[i][policy_depth[i]] for i in indices)
        static_j = sum(energy[i][static_depth] for i in indices)
        static_c = sum(correct[i][static_depth] for i in indices)
        # matched oracle: cheapest correct depth per question, no abstention
        base = [min(energy[i][k] for k in energy[i] if k >= 1) for i in indices]
        extras = []
        for i in indices:
            costs = [
                energy[i][k] - min(energy[i][j] for j in energy[i] if j >= 1)
                for k, ok in correct[i].items()
                if ok and k >= 1
            ]
            if costs:
                extras.append(min(costs))
        target = static_c
        extras.sort()
        if len(extras) < target:
            return float("nan")
        oracle_j = sum(base) + sum(extras[:target])
        oracle_e = oracle_j / target if target else float("nan")
        policy_e = total_j / total_c if total_c else float("nan")
        static_e = static_j / static_c if static_c else float("nan")
        gap = static_e - oracle_e
        if gap <= 0:
            return float("nan")
        return 100.0 * (static_e - policy_e) / gap

    point = _capture(np.arange(n))
    draws = []
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        value = _capture(idx)
        if math.isfinite(value):
            draws.append(value)
    draws_arr = np.asarray(draws)
    return {
        "point": point,
        "ci": [float(np.quantile(draws_arr, 0.025)), float(np.quantile(draws_arr, 0.975))],
        "n_valid": int(draws_arr.size),
    }


# --------------------------------------------------------------------------- #
# analyses
# --------------------------------------------------------------------------- #
def cluster_robust(root: Path) -> dict[str, Any]:
    split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    context = {str(row.qid): str(row.context_id) for row in split.questions.itertuples(index=False)}
    rows = _read_rows(root / "runs" / P1 / "raw.csv")
    by_q = _correct_by_depth(rows)
    qids = [qid for qid in split.ids if qid in by_q]
    out: dict[str, Any] = {"run_id": P1, "pairs": {"4-32": [], "1-32": [], "8-32": []}}
    for label, (a, b) in {"4-32": (4, 32), "1-32": (1, 32), "8-32": (8, 32)}.items():
        diffs = [by_q[q][a] - by_q[q][b] for q in qids]
        clusters = [context[q] for q in qids]
        stats = _cluster_robust_mean(diffs, clusters)
        stats["one_sided_lower_cluster"] = stats["mean"] - 1.645 * stats["se_cluster"]
        stats["one_sided_lower_iid"] = stats["mean"] - 1.645 * stats["se_iid"]
        stats["mcnemar_b"] = sum(1 for q in qids if by_q[q][a] == 1 and by_q[q][b] == 0)
        stats["mcnemar_c"] = sum(1 for q in qids if by_q[q][a] == 0 and by_q[q][b] == 1)
        out["pairs"][label] = stats
    sizes = defaultdict(int)
    for q in qids:
        sizes[context[q]] += 1
    out["cluster_size_min"] = min(sizes.values())
    out["cluster_size_max"] = max(sizes.values())
    out["cluster_size_median"] = float(np.median(list(sizes.values())))
    return out


def token_vs_depth(root: Path) -> dict[str, Any]:
    rows = _read_rows(root / "runs" / P1 / "raw.csv")
    k = np.asarray([float(r["k"]) for r in rows])
    tokens = np.asarray([float(r["prompt_tokens"]) for r in rows])
    energy = np.asarray([float(r["j_total"]) for r in rows])
    clusters = [str(r["question_id"]) for r in rows]

    designs = {
        "depth": np.column_stack([np.ones_like(k), k]),
        "tokens": np.column_stack([np.ones_like(k), tokens]),
        "both": np.column_stack([np.ones_like(k), k, tokens]),
    }
    out: dict[str, Any] = {
        "n_rows": int(len(rows)),
        "corr_depth_tokens": float(np.corrcoef(k, tokens)[0, 1]),
        "tokens_per_depth": {},
        "models": {},
    }
    for depth in sorted({int(x) for x in k}):
        mask = k == depth
        out["tokens_per_depth"][str(depth)] = {
            "mean_tokens": float(tokens[mask].mean()),
            "mean_j": float(energy[mask].mean()),
        }
    for name, design in designs.items():
        fit = _ols(design, energy)
        fit["se_cluster"] = _cluster_se(design, fit["resid"], np.asarray(fit["beta"]), clusters)
        fit.pop("resid")
        out["models"][name] = fit
    return out


def affine_ci(root: Path) -> dict[str, Any]:
    rows = _read_rows(root / "runs" / P1 / "raw.csv")
    per_depth: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        per_depth[int(row["k"])].append(float(row["j_total"]))
    depths = sorted(per_depth)
    keep = [d for d in depths if d >= 1]
    xs = np.asarray([float(d) for d in keep])
    means = np.asarray([float(np.mean(per_depth[d])) for d in keep])
    ses = np.asarray(
        [float(np.std(per_depth[d], ddof=1) / math.sqrt(len(per_depth[d]))) for d in keep]
    )
    weights = 1.0 / ses**2
    design = np.column_stack([np.ones_like(xs), xs])
    wls = np.linalg.inv(design.T @ (design * weights[:, None])) @ (design.T @ (weights * means))
    resid = means - design @ wls
    dof = len(xs) - 2
    s2 = float((weights * resid**2).sum() / dof)
    cov = s2 * np.linalg.inv(design.T @ (design * weights[:, None]))
    se = np.sqrt(np.diag(cov))
    sst = float((weights * (means - np.average(means, weights=weights)) ** 2).sum())
    ssr = float((weights * resid**2).sum())
    k0_rows = [r for r in rows if int(r["k"]) == 0]
    return {
        "depths_used": keep,
        "intercept_a": float(wls[0]),
        "slope_b": float(wls[1]),
        "se_a": float(se[0]),
        "se_b": float(se[1]),
        "ci_a": [float(wls[0] - 2.776 * se[0]), float(wls[0] + 2.776 * se[0])],
        "ci_b": [float(wls[1] - 2.776 * se[1]), float(wls[1] + 2.776 * se[1])],
        "r2_weighted": 1.0 - ssr / sst if sst > 0 else float("nan"),
        "k0_mean_j": float(np.mean([float(r["j_total"]) for r in k0_rows])),
        "k0_n": len(k0_rows),
        "k0_correct": int(sum(int(r["correct_em"]) for r in k0_rows)),
        "note": "k=0 is a floor and is excluded from the fit; report separately.",
    }


def cross_fitted_selection(root: Path, folds: int = 5) -> dict[str, Any]:
    split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    rows = _read_rows(root / "runs" / P1 / "raw.csv")
    by_q = _correct_by_depth(rows)
    energy: dict[str, dict[int, float]] = defaultdict(dict)
    for row in rows:
        energy[str(row["question_id"])][int(row["k"])] = float(row["j_total"])
    qids = [q for q in split.ids if q in by_q]
    depth_grid = [1, 2, 4, 8, 16, 32]

    def _fold(qid: str) -> int:
        # Stable fold assignment from the question id.
        return int(qid[-4:], 16) % folds

    fold_of = {q: _fold(q) for q in qids}
    selected: list[int] = []
    in_sample: list[float] = []
    held_out: list[float] = []
    for fold in range(folds):
        train = [q for q in qids if fold_of[q] != fold]
        test = [q for q in qids if fold_of[q] == fold]
        choice = 32
        for depth in depth_grid:
            diff = sum(by_q[q][depth] - by_q[q][32] for q in train) / len(train)
            ratio = sum(energy[q][32] for q in train) / sum(energy[q][depth] for q in train)
            if diff > -0.05 and ratio >= 1.20:
                choice = depth
                break
        selected.append(choice)
        in_sample.append(
            100.0
            * (
                1.0
                - (sum(energy[q][choice] for q in train) / sum(by_q[q][choice] for q in train))
                / (sum(energy[q][32] for q in train) / sum(by_q[q][32] for q in train))
            )
        )
        held_out.append(
            100.0
            * (
                1.0
                - (sum(energy[q][choice] for q in test) / sum(by_q[q][choice] for q in test))
                / (sum(energy[q][32] for q in test) / sum(by_q[q][32] for q in test))
            )
        )
    full_savings = 100.0 * (
        1.0
        - (sum(energy[q][4] for q in qids) / sum(by_q[q][4] for q in qids))
        / (sum(energy[q][32] for q in qids) / sum(by_q[q][32] for q in qids))
    )
    return {
        "folds": folds,
        "depth_grid": depth_grid,
        "selected_depth_by_fold": selected,
        "selected_depth_counts": {str(k): selected.count(k) for k in sorted(set(selected))},
        "in_sample_savings_pct_by_fold": in_sample,
        "held_out_savings_pct_by_fold": held_out,
        "mean_in_sample": float(np.mean(in_sample)),
        "mean_held_out": float(np.mean(held_out)),
        "sd_held_out": float(np.std(held_out, ddof=1)),
        "winner_curse_pp": float(np.mean(in_sample) - np.mean(held_out)),
        "full_sample_savings_at_k4_pct": full_savings,
        "rule": "smallest k with A(k)-A(32) > -5 pp and >=20% savings on the training folds",
        "note": "Selection is data-dependent; the held-out number is the honest object.",
    }


def policy_ci(root: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(
        "phase6_policy", root / "scripts" / "07_train_policy.py"
    )
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load 07_train_policy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    questions = {str(r.qid): str(r.question) for r in split.questions.itertuples(index=False)}
    wh_types = {str(r.qid): str(r.wh_type) for r in split.questions.itertuples(index=False)}
    rows = module._load_rows(root / "runs" / P1 / "raw.csv")
    k_grid = sorted({int(r["k"]) for r in rows.values()})
    index = RetrievalIndex.from_corpus(split.corpus)
    qids = list(split.ids)
    train_ids = [q for q in qids if module.assign_split(q, SEED) == "train"]
    val_ids = [q for q in qids if module.assign_split(q, SEED) == "validation"]
    test_ids = [q for q in qids if module.assign_split(q, SEED) == "test"]
    train = module._examples(train_ids, questions, wh_types, rows, index, k_grid)
    validation = module._examples(val_ids, questions, wh_types, rows, index, k_grid)
    test = module._examples(test_ids, questions, wh_types, rows, index, k_grid)
    static_rows = [
        dict(
            k=d,
            **dict(
                zip(("accuracy", "energy"), module._accuracy_energy(validation, d), strict=True)
            ),
        )
        for d in k_grid
    ]
    static_depth = min(static_rows, key=lambda r: r["energy"])["k"]
    static_val_acc = next(r["accuracy"] for r in static_rows if r["k"] == static_depth)
    policy = module.train_policy(train, validation)
    tuned = []
    for threshold in [i / 20 for i in range(21)]:
        result = module.evaluate_policy(policy, validation, static_depth, threshold)
        tuned.append((abs(result["accuracy"] - static_val_acc), threshold))
    _gap, threshold = min(tuned)
    depths = []
    for example in test:
        depth = _predict(policy, example, threshold)
        depths.append(static_depth if depth is None else depth)
    correct = [example.correct_by_depth for example in test]
    energy = [example.energy_by_depth for example in test]
    rng = np.random.default_rng(SEED)
    result = _bootstrap_capture(depths, correct, energy, static_depth, rng)
    result.update(
        {
            "n_test": len(test),
            "static_depth": static_depth,
            "threshold": threshold,
            "depth_histogram": {str(k): depths.count(k) for k in sorted(set(depths))},
            "note": "Capture of the matched no-abstention oracle gap; CI is a question bootstrap.",
        }
    )
    return result


def gold_rank(root: Path) -> dict[str, Any]:
    split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    rows = _read_rows(root / "runs" / P1 / "raw.csv")
    by_q = _correct_by_depth(rows)
    index = RetrievalIndex.from_corpus(split.corpus)
    questions = {str(r.qid): str(r.question) for r in split.questions.itertuples(index=False)}
    golds = {str(r.qid): str(r.gold) for r in split.questions.itertuples(index=False)}

    def norm(text: str) -> str:
        return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())

    rank1: list[str] = []
    for qid in split.ids:
        hits = index.search(qid, questions[qid], 1)
        if hits and norm(golds[qid]) in norm(hits[0].text):
            rank1.append(qid)
    rank1 = [q for q in rank1 if q in by_q]

    def pair(a: int, b: int) -> dict[str, float]:
        diffs = [by_q[q][a] - by_q[q][b] for q in rank1]
        n = len(diffs)
        mean = sum(diffs) / n
        var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
        return {
            "n": n,
            "mean_diff": mean,
            "se": math.sqrt(var / n),
            "ci": [mean - 1.96 * math.sqrt(var / n), mean + 1.96 * math.sqrt(var / n)],
            "accuracy_k_a": sum(by_q[q][a] for q in rank1) / n,
            "accuracy_k_b": sum(by_q[q][b] for q in rank1) / n,
        }

    all_q = [q for q in split.ids if q in by_q]
    return {
        "n_rank1": len(rank1),
        "share_rank1": len(rank1) / len(all_q),
        "gold_first_1_vs_32": pair(1, 32),
        "gold_first_4_vs_32": pair(4, 32),
        "gold_first_1_vs_8": pair(1, 8),
        "note": "Questions whose gold passage is retrieved at rank 1; adding distractors can only hurt.",
    }


def reader_subset(root: Path) -> dict[str, Any]:
    data = {}
    for run in READERS:
        rows = _read_rows(root / "runs" / run / "raw.csv")
        data[run] = _correct_by_depth(rows)
    shared = set.intersection(*(set(d) for d in data.values()))
    out: dict[str, Any] = {"n_shared": len(shared), "arms": {}}
    for run in READERS:
        d = data[run]
        diffs = [d[q][4] - d[q][32] for q in shared]
        mean = sum(diffs) / len(diffs)
        var = sum((x - mean) ** 2 for x in diffs) / (len(diffs) - 1)
        se = math.sqrt(var / len(diffs))
        out["arms"][run] = {
            "label": READER_LABELS[run],
            "mean_diff_4_32": mean,
            "se": se,
            "ci": [mean - 1.96 * se, mean + 1.96 * se],
            "accuracy_4": sum(d[q][4] for q in shared) / len(shared),
            "accuracy_32": sum(d[q][32] for q in shared) / len(shared),
        }
    return out


def price_of_guarantee(root: Path) -> dict[str, Any]:
    frontier = json.loads(
        (root / "analysis" / P1 / "margin_frontier.json").read_text(encoding="utf-8")
    )
    points = [
        {
            "margin_pp": row["margin_pp"],
            "selected_depth": row["selected_depth"],
            "savings_pct": row["savings_pct"],
        }
        for row in frontier["frontier"]
    ]
    points.sort(key=lambda row: row["margin_pp"])
    marginal = []
    for prev, cur in zip(points, points[1:], strict=False):
        marginal.append(
            {
                "from_margin_pp": prev["margin_pp"],
                "to_margin_pp": cur["margin_pp"],
                "savings_cost_pp": prev["savings_pct"] - cur["savings_pct"],
            }
        )
    return {"points": points, "marginal_cost": marginal}


def cancellation(root: Path) -> dict[str, Any]:
    rq = json.loads((root / "analysis" / "recall_precision.json").read_text(encoding="utf-8"))
    out: dict[str, Any] = {}
    for run, entry in rq.items():
        depths = entry["depths"]
        k4 = 4 if 4 in depths else None
        kmax = max(depths)
        if k4 is None:
            continue
        r4, rmax = entry["recall"][str(k4)], entry["recall"][str(kmax)]
        q4, qmax = entry["precision"][str(k4)], entry["precision"][str(kmax)]
        dr, dq = rmax - r4, qmax - q4
        recall_term = q4 * dr
        precision_term = rmax * dq
        out[run] = {
            "from_depth": k4,
            "to_depth": kmax,
            "delta_r": dr,
            "delta_q": dq,
            "recall_term": recall_term,
            "precision_term": precision_term,
            "net_delta_a": entry["accuracy"][str(kmax)] - entry["accuracy"][str(k4)],
            "sum_of_terms": recall_term + precision_term,
        }
    return out


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #
def _fmt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def write_report(out_dir: Path, payload: dict[str, Any]) -> None:
    cr = payload["cluster_robust"]["pairs"]["4-32"]
    tv = payload["token_vs_depth"]
    ac = payload["affine_ci"]
    sel = payload["selection"]
    pol = payload["policy_ci"]
    gold = payload["gold_rank"]["gold_first_1_vs_32"]
    sub = payload["reader_subset"]
    lines = [
        "# Phase 6 - inference repair",
        "",
        "Derived from registered run rows; no new measurements, no gate changes.",
        "",
        "## Cluster-robust contrast (A(4) - A(32))",
        "",
        f"- Mean {100 * cr['mean']:.2f} pp; iid SE {100 * cr['se_iid']:.2f} pp; "
        f"cluster SE {100 * cr['se_cluster']:.2f} pp.",
        f"- {cr['n']} questions in {cr['n_clusters']} contexts; design effect {cr['design_effect']:.2f}.",
        f"- Cluster 95% CI [{100 * cr['ci_cluster'][0]:.2f}, {100 * cr['ci_cluster'][1]:.2f}] pp; "
        f"one-sided lower {100 * cr['one_sided_lower_cluster']:.2f} pp.",
        "",
        "## Depth versus tokens",
        "",
        f"- Corr(k, prompt tokens) = {tv['corr_depth_tokens']:.3f}.",
        f"- Depth model: R2 {tv['models']['depth']['r2']:.4f}, BIC {tv['models']['depth']['bic']:.1f}.",
        f"- Token model: R2 {tv['models']['tokens']['r2']:.4f}, BIC {tv['models']['tokens']['bic']:.1f}.",
        "",
        "## Affine fit (k >= 1)",
        "",
        f"- a = {ac['intercept_a']:.3f} [{ac['ci_a'][0]:.3f}, {ac['ci_a'][1]:.3f}] J; "
        f"b = {ac['slope_b']:.3f} [{ac['ci_b'][0]:.3f}, {ac['ci_b'][1]:.3f}] J/passage.",
        f"- k=0 floor {ac['k0_mean_j']:.2f} J with {ac['k0_correct']}/{ac['k0_n']} correct.",
        "",
        "## Cross-fitted selection",
        "",
        f"- Selected depths by fold: {sel['selected_depth_by_fold']}.",
        f"- Mean held-out savings {sel['mean_held_out']:.2f}% (SD {sel['sd_held_out']:.2f}); "
        f"winner's curse {sel['winner_curse_pp']:.2f} pp.",
        "",
        "## Policy capture interval",
        "",
        f"- Capture {pol['point']:.2f}% with 95% CI [{pol['ci'][0]:.2f}, {pol['ci'][1]:.2f}] "
        f"on n={pol['n_test']}; depths {pol['depth_histogram']}.",
        "",
        "## Gold-first subset",
        "",
        f"- {gold['n']} questions with gold at rank 1; A(1) = {gold['accuracy_k_a']:.4f}, "
        f"A(32) = {gold['accuracy_k_b']:.4f}, diff {100 * gold['mean_diff']:.2f} pp "
        f"[{100 * gold['ci'][0]:.2f}, {100 * gold['ci'][1]:.2f}].",
        "",
        "## Three readers on identical questions",
        "",
    ]
    for entry in sub["arms"].values():
        lines.append(
            f"- {entry['label']}: A(4)-A(32) = {100 * entry['mean_diff_4_32']:.2f} pp "
            f"[{100 * entry['ci'][0]:.2f}, {100 * entry['ci'][1]:.2f}], n={sub['n_shared']}."
        )
    lines.append("")
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6 inference repair.")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root)
    out_dir = root / "analysis" / "phase6"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "cluster_robust": cluster_robust(root),
        "token_vs_depth": token_vs_depth(root),
        "affine_ci": affine_ci(root),
        "selection": cross_fitted_selection(root),
        "policy_ci": policy_ci(root),
        "gold_rank": gold_rank(root),
        "reader_subset": reader_subset(root),
        "price_of_guarantee": price_of_guarantee(root),
        "cancellation": cancellation(root),
    }
    for name, value in payload.items():
        (out_dir / f"{name}.json").write_text(json.dumps(value, indent=2), encoding="utf-8")
    write_report(out_dir, payload)
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
