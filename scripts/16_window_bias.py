#!/usr/bin/env python
"""16 - Window-bias diagnostics for per-query NVML energy.

Computes (a) the dependence of k=0 energy on the preceding row's depth and
(b) the ratio of measured energy to a generous physical power cap. Diagnostic
only; does not change any calibration gate.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = {
    "squad_qwen4b_p1": 15.794,
    "squad_qwen15b_p2": 16.129,
    "hotpot_qwen4b_p2": 16.0,
    "squad_llama3b_p2": 16.0,
}
P_MAX_W = 115.0


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description="Window-bias diagnostics.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.root)
    out = Path(args.out) if args.out else root / "analysis" / "calibration_bias.json"
    payload = {}
    for run_id, idle in ARMS.items():
        raw = root / "runs" / run_id / "raw.csv"
        if not raw.is_file():
            continue
        rows = _rows(raw)
        prev_by_depth = defaultdict(list)
        cap_by_depth = defaultdict(list)
        previous = None
        for row in rows:
            k = int(row["k"])
            j = float(row["j_gpu_raw"])
            latency = float(row.get("latency_s", 0.0) or 0.0)
            if k == 0 and previous is not None:
                prev_by_depth[int(previous["k"])].append(j)
            if latency > 0:
                cap_by_depth[k].append(j / (latency * (P_MAX_W - idle)))
            previous = row
        payload[run_id] = {
            "k0_by_previous_depth": {
                str(k): {
                    "n": len(values),
                    "mean_j": statistics.mean(values),
                    "median_j": statistics.median(values),
                }
                for k, values in sorted(prev_by_depth.items())
            },
            "cap_ratio_by_depth": {
                str(k): {
                    "n": len(values),
                    "mean_ratio": statistics.mean(values),
                    "median_ratio": statistics.median(values),
                }
                for k, values in sorted(cap_by_depth.items())
            },
        }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
