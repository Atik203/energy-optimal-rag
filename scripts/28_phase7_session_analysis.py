#!/usr/bin/env python
"""28 - Phase 7 session-variance analysis (ICC).

Decomposes the energy variance in ``sessions.json`` into a between-session component
and a within-session component, per depth. The within-session replicates are the
contiguous segment integrals written by ``26_phase7_sessions.py``: a segment is an
ordinary block estimate over a shorter span, so it is a valid measurement.

ICC(1,1) is the one-way random-effects form. With three sessions the between-session
estimate is coarse, and that is stated in the output rather than smoothed over.

CPU only.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_RUN_ID = "squad_qwen4b_p7_sessions"
CANDIDATE = 4
REFERENCE = 32


def _icc_one_way(groups: list[list[float]]) -> dict[str, float]:
    """One-way random-effects ICC(1,1) from a list of per-session segment values."""
    groups = [g for g in groups if len(g) > 1]
    k = len(groups)
    if k < 2:
        return {"icc": float("nan"), "ms_between": float("nan"), "ms_within": float("nan")}
    n_i = [len(g) for g in groups]
    grand = sum(sum(g) for g in groups) / sum(n_i)
    ss_between = sum(
        n * (statistics.mean(g) - grand) ** 2 for n, g in zip(n_i, groups, strict=True)
    )
    ss_within = sum(sum((v - statistics.mean(g)) ** 2 for v in g) for g in groups)
    df_between = k - 1
    df_within = sum(n_i) - k
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within if df_within else float("nan")
    m = sum(n_i) / k
    denom = ms_between + (m - 1) * ms_within
    icc = (ms_between - ms_within) / denom if denom else float("nan")
    return {
        "icc": icc,
        # The estimator is negative when between-session variance is near zero. That is
        # the correct algebra (-1/(m-1) when it is exactly zero), but a negative
        # intraclass correlation has no interpretation, so the reported value is
        # truncated at zero and the raw value is kept beside it.
        "icc_truncated": max(0.0, icc) if icc == icc else float("nan"),
        "ms_between": ms_between,
        "ms_within": ms_within,
        "n_sessions": float(k),
        "segments_per_session": m,
    }


def _harmonize(energy_j: float, duration_s: float, idle_w: float, reference_w: float) -> float:
    """Re-express a block or segment integral at a common idle baseline.

    ``measured = gross - idle_w * duration``, so ``gross`` can be reconstructed and
    re-subtracted at ``reference_w``. This matters because idle power on the host is not
    stationary: a block measured behind a 20 W baseline is biased low relative to one
    behind 14.5 W, by ``(idle_w - reference_w) * duration``.
    """
    if duration_s <= 0:
        return energy_j
    gross = energy_j + idle_w * duration_s
    return gross - reference_w * duration_s


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 session-variance analysis.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument(
        "--compare-run-id",
        default="squad_qwen4b_p7_blocks_full",
        help="Block run measured on the same questions for the cross-occasion comparison.",
    )
    parser.add_argument("--compare-replicate", type=int, default=0)
    args = parser.parse_args()
    root = Path(args.root)
    src = root / "runs" / args.run_id / "sessions.json"
    if not src.is_file():
        raise SystemExit(f"missing input: {src}")
    payload = json.loads(src.read_text(encoding="utf-8"))
    sessions = payload["sessions"]
    depths = [int(k) for k in payload["depths"]]
    seg_size = int(payload["segment_size"])

    by_depth: dict[str, Any] = {}
    # A common idle baseline for the harmonised comparison: the median of every block's
    # measured idle. The median avoids privileging the cleanest session.
    all_idles = sorted(
        float(block["idle_mean_w"]) for session in sessions for block in session["blocks"]
    )
    reference_idle = statistics.median(all_idles)

    for depth in depths:
        block_values: list[float] = []
        harmonized_values: list[float] = []
        groups: list[list[float]] = []
        harmonized_groups: list[list[float]] = []
        accuracies: list[float] = []
        for session in sessions:
            block = next(b for b in session["blocks"] if int(b["k"]) == depth)
            block_values.append(float(block["energy_per_query_j"]))
            accuracies.append(int(block["correct"]) / int(block["n"]))
            groups.append([float(seg["energy_j"]) / (seg_size * 1.0) for seg in block["segments"]])

            duration = float(block["duration_s"])
            idle_w = float(block["idle_mean_w"])
            n_questions = int(block["n"])
            harmonized_values.append(
                _harmonize(float(block["energy_j"]), duration, idle_w, reference_idle) / n_questions
            )
            harmonized_groups.append(
                [
                    _harmonize(
                        float(seg["energy_j"]),
                        float(seg["end_s"]) - float(seg["start_s"]),
                        idle_w,
                        reference_idle,
                    )
                    / (seg_size * 1.0)
                    for seg in block["segments"]
                ]
            )
        icc = _icc_one_way(groups)
        icc_harmonized = _icc_one_way(harmonized_groups)
        mean = statistics.mean(block_values)
        sd = statistics.stdev(block_values) if len(block_values) > 1 else 0.0
        mean_h = statistics.mean(harmonized_values)
        sd_h = statistics.stdev(harmonized_values) if len(harmonized_values) > 1 else 0.0
        by_depth[str(depth)] = {
            "block_j_per_query": block_values,
            "block_mean_j_per_query": mean,
            "block_sd": sd,
            "between_session_cv": sd / mean if mean else None,
            "accuracy": accuracies,
            "segment_j_per_query": groups,
            "idle_harmonized": {
                "reference_idle_w": reference_idle,
                "block_j_per_query": harmonized_values,
                "block_mean_j_per_query": mean_h,
                "between_session_cv": sd_h / mean_h if mean_h else None,
                "icc": icc_harmonized["icc"],
                "icc_truncated": icc_harmonized["icc_truncated"],
            },
            **icc,
        }

    idles = [float(s["idle_mean_w"]) for s in sessions]
    idles_cv = [float(s["idle_cv"]) for s in sessions]

    # Cross-occasion comparison: the session run used the same first 200 questions as the
    # block run's replicate 0, so the two are directly comparable. This is what makes the
    # "level moves, ratio does not" statement traceable to a registered output.
    cross: dict[str, Any] = {}
    compare_dir = root / "runs" / args.compare_run_id
    compare_path = compare_dir / "blocks_design.json"
    if compare_path.is_file():
        compare = json.loads(compare_path.read_text(encoding="utf-8"))
        # Reproduce the session question set: the first `questions_per_block` questions,
        # which is replicate 0 of a disjoint block design.
        j_tot: dict[int, float] = {}
        c_tot: dict[int, int] = {}
        n_tot: dict[int, int] = {}
        for block in compare["blocks"]:
            if int(block["replicate"]) != args.compare_replicate:
                continue
            k = int(block["k"])
            j_tot[k] = j_tot.get(k, 0.0) + float(block["energy_j"])
            c_tot[k] = c_tot.get(k, 0) + int(block["correct"])
            n_tot[k] = n_tot.get(k, 0) + int(block["n"])
        per_depth: dict[str, Any] = {}
        for depth in depths:
            if depth not in j_tot or not c_tot.get(depth):
                continue
            cmp_jq = j_tot[depth] / n_tot[depth]
            sess_jq = by_depth[str(depth)]["block_mean_j_per_query"]
            per_depth[str(depth)] = {
                "compare_j_per_query": cmp_jq,
                "session_mean_j_per_query": sess_jq,
                "offset_pct": 100 * (sess_jq / cmp_jq - 1),
                "compare_accuracy": c_tot[depth] / n_tot[depth],
                "session_accuracy": statistics.mean(by_depth[str(depth)]["accuracy"]),
            }
        savings: dict[str, Any] = {}
        if CANDIDATE in j_tot and REFERENCE in j_tot:
            cmp_e4 = (j_tot[CANDIDATE] / n_tot[CANDIDATE]) / (c_tot[CANDIDATE] / n_tot[CANDIDATE])
            cmp_e32 = (j_tot[REFERENCE] / n_tot[REFERENCE]) / (c_tot[REFERENCE] / n_tot[REFERENCE])
            session_savings = []
            for session in sessions:
                b4 = next(b for b in session["blocks"] if int(b["k"]) == CANDIDATE)
                b32 = next(b for b in session["blocks"] if int(b["k"]) == REFERENCE)
                e4 = b4["energy_per_query_j"] / (b4["correct"] / b4["n"])
                e32 = b32["energy_per_query_j"] / (b32["correct"] / b32["n"])
                session_savings.append(100 * (1 - e4 / e32))
            savings = {
                "compare_saving_pct": 100 * (1 - cmp_e4 / cmp_e32),
                "session_saving_pct": session_savings,
                "session_saving_mean_pct": statistics.mean(session_savings),
                "session_saving_spread_pp": max(session_savings) - min(session_savings),
                "difference_pp": statistics.mean(session_savings) - 100 * (1 - cmp_e4 / cmp_e32),
            }
        cross = {
            "compare_run_id": args.compare_run_id,
            "compare_replicate": args.compare_replicate,
            "by_depth": per_depth,
            "savings": savings,
        }

    out = {
        "run_id": args.run_id,
        "n_sessions": len(sessions),
        "questions_per_block": payload["questions_per_block"],
        "segments_per_block": payload["segments_per_block"],
        "segment_size": seg_size,
        "idle_mean_w": idles,
        "idle_cv": idles_cv,
        "by_depth": by_depth,
        "cross_occasion": cross,
        "note": (
            "ICC(1,1) with three sessions is coarse; it is reported as a descriptive "
            "decomposition, not as a precise variance component."
        ),
    }

    out_dir = root / "analysis" / "measurement_hardening" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sessions.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    lines = [
        "# Phase 7 - session variance",
        "",
        f"Run `{args.run_id}`; {len(sessions)} sessions, "
        f"{payload['questions_per_block']} questions per block, "
        f"{payload['segments_per_block']} segments of {seg_size}.",
        "",
        f"Idle across sessions: {', '.join(f'{v:.2f} W' for v in idles)}.",
        "",
        "| k | J/query | between-session CV | ICC(1,1) | harmonised J/query | "
        "harmonised CV | harmonised ICC |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for depth in depths:
        item = by_depth[str(depth)]
        h = item["idle_harmonized"]
        lines.append(
            f"| {depth} | {item['block_mean_j_per_query']:.2f} | "
            f"{100 * item['between_session_cv']:.1f}% | {item['icc_truncated']:.3f} | "
            f"{h['block_mean_j_per_query']:.2f} | {100 * h['between_session_cv']:.1f}% | "
            f"{h['icc_truncated']:.3f} |"
        )
    lines += [
        "",
        f"Harmonised to a common idle of {reference_idle:.2f} W (median of measured idles).",
        "",
    ]
    lines += ["", out["note"], ""]
    (out_dir / "sessions.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
