#!/usr/bin/env python
"""34 - Phase 8 Step 2 analysis: distractor dose-response curve.

Reads ``runs/squad_qwen4b_qc_distractor/distractor.json`` and writes
``analysis/qc_distractor/``: ``dose_curve.json`` (per-dose accuracy with binomial
CIs, repeated-measures trend, segment-paired contrasts vs dose 0, energy as a
range) and ``dose_curve.md``.

Substitution note (prereg amendment A-005): the prereg names "paired McNemar/GLM +
trend test", but the runner persisted segment aggregates, not per-question
outcomes, so McNemar's discordant pairs are unrecoverable. Segments are
contiguous 125-question chunks of one fixed qid order, hence question-aligned
across doses: the analysis uses the segment as the paired unit (repeated-measures
slope + segment-paired contrasts, i.e. the GLM-family half of the preregistered
pair). The slope estimate is identical to the run script's point summary; the
intervals are new.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_RUN_ID = "squad_qwen4b_qc_distractor"
TOST_PP = 0.02


def _wilson(x: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    p = x / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def _ols_slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / denom


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 Step 2 dose analysis.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)
    src = root / "runs" / args.run_id / "distractor.json"
    if not src.is_file():
        raise SystemExit(f"missing input: {src}")
    payload = json.loads(src.read_text(encoding="utf-8"))
    blocks = sorted(payload["blocks"], key=lambda b: int(b["dose"]))

    doses = [int(b["dose"]) for b in blocks]
    xs = [float((d + 1).bit_length() - 1) for d in doses]
    n_q = int(blocks[0]["n"])
    seg_size = int(blocks[0]["segments"][0]["n"])

    # Per-dose accuracy with Wilson CIs; energy as a range.
    per_dose: dict[str, Any] = {}
    for b in blocks:
        d = str(int(b["dose"]))
        correct, n = int(b["correct"]), int(b["n"])
        per_dose[d] = {
            "accuracy": correct / n,
            "wilson_ci95": _wilson(correct, n),
            "energy_per_query_j": float(b["energy_j"]) / n,
            "energy_per_correct_j": (float(b["energy_j"]) / n) / (correct / n) if correct else None,
            "idle_mean_w": float(b["idle_mean_w"]),
            "idle_cv": float(b["idle_cv"]),
            "segments": [
                {"accuracy": s["correct"] / s["n"], "correct": s["correct"], "n": s["n"]}
                for s in b["segments"]
            ],
        }

    # Repeated-measures trend: one OLS slope per segment, mean + t CI (df = n_seg - 1).
    n_seg = len(blocks[0]["segments"])
    seg_slopes = []
    for s in range(n_seg):
        ys = [b["segments"][s]["correct"] / b["segments"][s]["n"] for b in blocks]
        seg_slopes.append(_ols_slope(xs, ys))
    mean_slope = statistics.mean(seg_slopes)
    sd_slope = statistics.stdev(seg_slopes) if len(seg_slopes) > 1 else 0.0
    # t_{0.975,3} = 3.182.
    t_crit = 3.182 if n_seg == 4 else 2.0
    slope_ci = [mean_slope - t_crit * sd_slope / math.sqrt(n_seg),
                mean_slope + t_crit * sd_slope / math.sqrt(n_seg)]
    point_slope = _ols_slope(xs, [per_dose[str(d)]["accuracy"] for d in doses])

    # Segment-paired contrasts of each dose against dose 0.
    seg_acc0 = [s["correct"] / s["n"] for s in blocks[0]["segments"]]
    contrasts: dict[str, Any] = {}
    for b in blocks[1:]:
        seg_acc = [s["correct"] / s["n"] for s in b["segments"]]
        diffs = [a - a0 for a, a0 in zip(seg_acc, seg_acc0, strict=True)]
        mean_d = statistics.mean(diffs)
        sd_d = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
        contrasts[str(int(b["dose"]))] = {
            "paired_diff_pp": 100 * mean_d,
            "t_ci95_pp": [100 * (mean_d - t_crit * sd_d / math.sqrt(n_seg)),
                          100 * (mean_d + t_crit * sd_d / math.sqrt(n_seg))],
        }

    acc0 = per_dose[str(doses[0])]["accuracy"]
    acc_max = per_dose[str(doses[-1])]["accuracy"]
    rise_pp = 100 * (acc_max - acc0)

    out = {
        "run_id": args.run_id,
        "estimand": "A(dose) at gold rank 1; trend over log2(dose+1)",
        "n_per_dose": n_q,
        "n_segments": n_seg,
        "segment_size": seg_size,
        "per_dose": per_dose,
        "trend": {
            "point_slope_per_doubling": point_slope,
            "repeated_measures_slope": mean_slope,
            "repeated_measures_ci95": slope_ci,
            "segment_slopes": seg_slopes,
            "note": "McNemar impossible (no per-question file); segment is the paired unit (A-005).",
        },
        "contrasts_vs_dose0_pp": contrasts,
        "rise_dose0_to_dose31_pp": rise_pp,
        "tost_flat_bound_pp": 100 * TOST_PP,
        "h_overload_verdict": (
            "REJECTED: accuracy rises with dose (positive slope); "
            "reader overload at fixed gold rank 1 is not observed."
            if mean_slope > 0 and slope_ci[0] > 0
            else "slope CI includes zero or negative; see intervals"
        ),
    }
    out_dir = root / "analysis" / "qc_distractor"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dose_curve.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    lines = [
        "# Phase 8 Step 2 - distractor dose-response",
        "",
        f"Run `{args.run_id}`; {n_q} questions per dose, {n_seg} question-aligned segments.",
        "",
        "| dose | k-equiv | accuracy | 95% CI | J/query |",
        "|---:|---:|---:|---|---|---:|",
    ]
    for b in blocks:
        d = str(int(b["dose"]))
        p = per_dose[d]
        lines.append(
            f"| {d} | {int(b['dose']) + 1} | {p['accuracy']:.3f} | "
            f"[{p['wilson_ci95'][0]:.3f}, {p['wilson_ci95'][1]:.3f}] | "
            f"{p['energy_per_query_j']:.2f} |"
        )
    lines += [
        "",
        f"Trend: {100 * point_slope:.2f} pp per doubling (repeated-measures "
        f"{100 * mean_slope:.2f}, 95% CI [{100 * slope_ci[0]:.2f}, {100 * slope_ci[1]:.2f}]).",
        f"Rise dose 0 to 31: +{rise_pp:.1f} pp (flat bound +-2 pp).",
        "",
        f"H-overload: **{out['h_overload_verdict']}**",
        "",
    ]
    (out_dir / "dose_curve.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
