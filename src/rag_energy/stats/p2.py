"""P2 replication analysis.

H7 is direction-only: it asks whether the paired accuracy contrast
``A(4) - A(32)`` has the same sign on the replication arm as it did on P1.
P1 observed a negative contrast (``A(4) < A(32)``). The replication supports
H7 when the one-sided 95% upper bound on ``A(4) - A(32)`` is below zero, i.e.
the whole directional interval lies in the same negative direction.

This module deliberately does **not** re-run the P1 gate family. The 5 pp
non-inferiority test is reported as a secondary estimate, never as a
certification, because the replication is not powered for it.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scipy import stats as scipy_stats

from rag_energy.stats.p1 import (
    DEFAULT_SEED,
    DepthSummary,
    _calibration_status,
    _correct,
    _is_valid,
    _write_estimates,
    _write_json,
    affine_lack_of_fit,
    bootstrap,
    context_share,
    load_rows,
    noninferiority,
    paired_questions,
    summarize,
)

P1_DIRECTION = "negative"


def _p1_contrast(root: Path | None) -> dict[str, Any] | None:
    if root is None:
        return None
    path = Path(root) / "analysis" / "squad_qwen4b_p1" / "noninferiority.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    primary = payload.get("primary", {})
    return {
        "run_id": "squad_qwen4b_p1",
        "mean_diff": primary.get("mean_diff"),
        "lower_bound": primary.get("lower_bound"),
        "upper_bound": primary.get("upper_bound"),
        "margin": primary.get("margin"),
        "direction": P1_DIRECTION if float(primary.get("mean_diff", 0.0)) < 0 else "positive",
    }


def _directional_test(
    candidate_correct: Sequence[int],
    reference_correct: Sequence[int],
    *,
    margin: float,
    n_invalid_candidate: int,
    n_invalid_reference: int,
) -> dict[str, Any]:
    result = noninferiority(
        candidate_correct,
        reference_correct,
        margin=margin,
        n_invalid_candidate=n_invalid_candidate,
        n_invalid_reference=n_invalid_reference,
    )
    if result.se > 0:
        # Null is contrast >= 0; a negative mean gives a small one-sided p.
        p_direction = float(scipy_stats.norm.cdf(result.mean_diff / result.se))
    else:
        p_direction = 0.0 if result.mean_diff < 0 else 1.0
    # ``upper_bound`` is the one-sided 95% upper bound on the contrast; below
    # zero means the whole directional interval is negative, matching P1.
    upper_one_sided = result.upper_bound
    return {
        "n_pairs": result.n_pairs,
        "n_invalid_candidate": result.n_invalid_candidate,
        "n_invalid_reference": result.n_invalid_reference,
        "mean_diff": result.mean_diff,
        "sd_diff": result.sd_diff,
        "se": result.se,
        "b": result.b,
        "c": result.c,
        "mcnemar_exact_p": result.mcnemar_exact_p,
        "mcnemar_z_p": result.mcnemar_z_p,
        "one_sided_lower_5pp": result.lower_bound,
        "one_sided_upper_5pp": result.upper_bound,
        "one_sided_upper_zero": upper_one_sided,
        "p_direction": p_direction,
        "p_5pp": result.p_value,
        "non_inferior_5pp": result.non_inferior,
        "point_direction_matches": result.mean_diff < 0,
        "h7_supported": bool(result.mean_diff < 0 and upper_one_sided < 0),
    }


def _write_report(
    path: Path,
    *,
    run_id: str,
    summaries: Sequence[DepthSummary],
    fit: dict[str, Any],
    shares: dict[int, float],
    direction: dict[str, Any],
    savings: dict[str, Any],
    calibration: dict[str, Any],
    p1: dict[str, Any] | None,
) -> None:
    lines = [
        f"# P2 replication analysis - {run_id}",
        "",
        f"Calibration: **{'applied' if calibration.get('applied') else 'not applied'}** "
        f"(all depths passed: {calibration.get('all_passed')}).",
        "",
        "| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct | S(k) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary.k} | {summary.n_valid} | {summary.n_invalid} | "
            f"{summary.accuracy:.4f} | {summary.mean_j:.2f} | "
            f"{summary.e_per_correct:.2f} | {shares.get(summary.k, float('nan')):.3f} |"
        )
    lines.extend(
        [
            "",
            f"Affine descriptive fit: `J(k) = {fit['a']:.4f} + {fit['b']:.4f} k`, "
            f"R2 = {fit['r2']:.4f}; quadratic lack-of-fit p = {fit['lack_of_fit_p']:.4f}.",
            "",
            "## H7 direction replication",
            "",
            f"- Paired n = {direction['n_pairs']}; discordant b = {direction['b']}, "
            f"c = {direction['c']}; invalid at k=4/k=32 = "
            f"{direction['n_invalid_candidate']}/{direction['n_invalid_reference']}.",
            f"- Mean difference A(4) - A(32) = {100 * direction['mean_diff']:.2f} pp "
            f"(one-sided 95% upper bound {100 * direction['one_sided_upper_zero']:.2f} pp).",
            f"- Directional one-sided p (null: contrast >= 0) = {direction['p_direction']:.6f}.",
            f"- Point estimate matches P1's negative direction: "
            f"{direction['point_direction_matches']}.",
            f"- **H7 supported (whole directional interval negative): "
            f"{direction['h7_supported']}.**",
            "",
            "The 5 pp non-inferiority test is secondary and not powered on this arm: "
            f"lower bound {100 * direction['one_sided_lower_5pp']:.2f} pp, "
            f"p = {direction['p_5pp']}, non-inferior = {direction['non_inferior_5pp']}.",
            "",
            "## Energy contrast",
            "",
            f"- Savings 1 - E(4)/E(32) = {savings['savings_pct']['point']:.2f}% "
            f"(95% CI {savings['savings_pct']['interval']['lower']:.2f} to "
            f"{savings['savings_pct']['interval']['upper']:.2f}%).",
            f"- P(k* optimal) = {json.dumps(savings['p_k_optimal'], sort_keys=True)}.",
        ]
    )
    if p1 is not None:
        lines.extend(
            [
                "",
                f"P1 reference: {100 * p1['mean_diff']:.2f} pp "
                f"(one-sided lower {100 * p1['lower_bound']:.2f} pp); "
                f"direction {p1['direction']}.",
            ]
        )
    lines.extend(
        [
            "",
            "H7 is direction-only. This arm does not certify 5 pp, does not set a universal "
            "k*, and does not change the P1 negative decision.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _completeness(
    rows: Sequence[dict[str, Any]],
    by_k: dict[int, DepthSummary],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Compare the row count with the registered question grid.

    The expected count comes from the run config (``n_questions`` x
    ``k_grid``), not from the analysis prereg, which describes P1. When the
    config omits the grid, completeness is reported as ``None`` and no
    completeness claim is made.
    """
    n_questions_config = int(config.get("n_questions", 0) or 0)
    depths_config = [int(k) for k in config.get("k_grid", [])] or sorted(by_k)
    expected_rows = n_questions_config * len(depths_config) if n_questions_config else None
    completeness = {
        "n_questions_config": n_questions_config or None,
        "n_questions_observed": len({str(row["question_id"]) for row in rows}),
        "depths_config": depths_config,
        "depths_observed": sorted(by_k),
        "expected_rows": expected_rows,
        "n_rows": len(rows),
        "complete": None if expected_rows is None else expected_rows == len(rows),
    }
    if completeness["complete"] is False:
        raise ValueError(
            f"incomplete run: {len(rows)} rows, expected {expected_rows} "
            f"(n_questions={n_questions_config} x {len(depths_config)} depths)"
        )
    return completeness


def write_p2_analysis(
    raw_path: Path,
    out_dir: Path,
    *,
    run_id: str,
    root: Path | None = None,
    config: dict[str, Any] | None = None,
    seed: int | None = None,
    resamples: int | None = None,
    candidate: int = 4,
    reference: int | None = None,
    margin: float | None = None,
) -> Path:
    """Write the P2 replication outputs for one registered run."""
    config = config or {}
    seed = int(seed if seed is not None else config.get("seed", DEFAULT_SEED))
    resamples = int(
        resamples if resamples is not None else config.get("bootstrap", {}).get("resamples", 10_000)
    )
    margin = float(
        margin if margin is not None else config.get("primary", {}).get("margin_pp", 5.0) / 100.0
    )
    rows = load_rows(raw_path)
    summaries = summarize(rows, correct_key="em")
    empty_depths = [summary.k for summary in summaries if summary.n_valid == 0]
    if empty_depths:
        raise ValueError(f"depths with no valid rows: {empty_depths}")
    by_k = {summary.k: summary for summary in summaries}
    if reference is None:
        reference = max(by_k)
    if candidate not in by_k or reference not in by_k:
        raise ValueError("candidate and reference depths must both be present")
    if candidate >= reference:
        raise ValueError("candidate must be shallower than reference")

    fit = affine_lack_of_fit([(summary.k, summary.mean_j) for summary in summaries])
    shares = context_share(summaries, fit["b"])
    cand_rows, ref_rows, _excluded = paired_questions(rows, candidate, reference)
    n_invalid_candidate = sum(
        1 for row in rows if int(row["k"]) == candidate and not _is_valid(row)
    )
    n_invalid_reference = sum(
        1 for row in rows if int(row["k"]) == reference and not _is_valid(row)
    )
    direction = _directional_test(
        [_correct(row, "em") for row in cand_rows],
        [_correct(row, "em") for row in ref_rows],
        margin=margin,
        n_invalid_candidate=n_invalid_candidate,
        n_invalid_reference=n_invalid_reference,
    )
    savings = bootstrap(
        rows,
        resamples=resamples,
        seed=seed,
        margin=margin,
        correct_key="em",
        candidate=candidate,
        reference=reference,
        selected_depth=candidate,
    )
    calibration = _calibration_status(raw_path)
    p1 = _p1_contrast(root)
    metadata = {
        "run_id": run_id,
        "candidate_depth": candidate,
        "reference_depth": reference,
        "margin": margin,
        "seed": seed,
        "resamples": resamples,
        "n_rows": len(rows),
        "n_valid": sum(1 for row in rows if _is_valid(row)),
        "n_invalid": sum(1 for row in rows if not _is_valid(row)),
        "calibrated": bool(calibration.get("applied")),
        "calibration": calibration,
        "p1_reference": p1,
        "h7_definition": (
            "H7 is supported when the paired mean A(4)-A(32) is negative and its "
            "one-sided 95% upper bound is below zero, matching P1's negative direction."
        ),
    }
    completeness = _completeness(rows, by_k, config)
    direction_payload = {
        "run_id": run_id,
        "candidate_depth": candidate,
        "reference_depth": reference,
        "p1_reference": p1,
        "definition": (
            "H7 is supported when the paired mean A(4)-A(32) is negative and its "
            "one-sided 95% upper bound is below zero, matching P1's negative direction."
        ),
        **direction,
    }
    payload = {
        "run_id": run_id,
        "candidate_depth": candidate,
        "reference_depth": reference,
        "h7_supported": direction["h7_supported"],
        "mean_diff": direction["mean_diff"],
        "one_sided_upper_zero": direction["one_sided_upper_zero"],
        "savings_pct": savings["savings_pct"]["point"],
        "p_k_optimal": savings["p_k_optimal"],
        "fit": fit,
        "calibration": calibration,
        "completeness": completeness,
        "p1_reference": p1,
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_estimates(out_dir / "estimates.csv", summaries, shares)
    _write_json(out_dir / "fit.json", fit)
    _write_json(out_dir / "direction.json", direction_payload)
    _write_json(out_dir / "bootstrap.json", savings)
    _write_json(out_dir / "metadata.json", metadata)
    _write_json(out_dir / "p2.json", payload)
    _write_report(
        out_dir / "report.md",
        run_id=run_id,
        summaries=summaries,
        fit=fit,
        shares=shares,
        direction=direction,
        savings=savings,
        calibration=calibration,
        p1=p1,
    )
    return out_dir
