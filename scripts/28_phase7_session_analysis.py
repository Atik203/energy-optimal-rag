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


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 session-variance analysis.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
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
    for depth in depths:
        block_values: list[float] = []
        groups: list[list[float]] = []
        accuracies: list[float] = []
        for session in sessions:
            block = next(b for b in session["blocks"] if int(b["k"]) == depth)
            block_values.append(float(block["energy_per_query_j"]))
            accuracies.append(int(block["correct"]) / int(block["n"]))
            groups.append([float(seg["energy_j"]) / (seg_size * 1.0) for seg in block["segments"]])
        icc = _icc_one_way(groups)
        mean = statistics.mean(block_values)
        sd = statistics.stdev(block_values) if len(block_values) > 1 else 0.0
        by_depth[str(depth)] = {
            "block_j_per_query": block_values,
            "block_mean_j_per_query": mean,
            "block_sd": sd,
            "between_session_cv": sd / mean if mean else None,
            "accuracy": accuracies,
            "segment_j_per_query": groups,
            **icc,
        }

    idles = [float(s["idle_mean_w"]) for s in sessions]
    idles_cv = [float(s["idle_cv"]) for s in sessions]

    out = {
        "run_id": args.run_id,
        "n_sessions": len(sessions),
        "questions_per_block": payload["questions_per_block"],
        "segments_per_block": payload["segments_per_block"],
        "segment_size": seg_size,
        "idle_mean_w": idles,
        "idle_cv": idles_cv,
        "by_depth": by_depth,
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
        "| k | block J/query | between-session CV | ICC(1,1) |",
        "|---:|---:|---:|---:|",
    ]
    for depth in depths:
        item = by_depth[str(depth)]
        lines.append(
            f"| {depth} | {item['block_mean_j_per_query']:.2f} | "
            f"{100 * item['between_session_cv']:.1f}% | {item['icc_truncated']:.3f} |"
        )
    lines += ["", out["note"], ""]
    (out_dir / "sessions.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
