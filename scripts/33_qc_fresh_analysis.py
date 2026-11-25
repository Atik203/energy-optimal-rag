#!/usr/bin/env python
"""33 - Phase 8 Step 1 analysis: fresh k=4 gap with paired CI and stop-rule verdict.

Reads ``runs/squad_qwen4b_qc_fresh/{blocks_design.json,raw.csv}`` and writes
``analysis/qc_fresh/``: ``estimates.json`` (per-depth accuracy, energy, savings of
k=1 vs k=4 with cluster-bootstrap CI) and ``gap.json`` (oracle headroom
``A_oracle{1,4} - A(4)`` with paired bootstrap CI plus the preregistered stop-rule
verdict). CPU only.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_RUN_ID = "squad_qwen4b_qc_fresh"
SEED = 20261115
N_BOOT = 10000
STOP_THRESHOLD = 0.10


def _blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "k": int(b["k"]),
            "replicate": int(b["replicate"]),
            "energy_j": float(b["energy_j"]),
            "correct": int(b["correct"]),
            "n": int(b["n"]),
        }
        for b in payload["blocks"]
    ]


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = q * (len(ordered) - 1)
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 Step 1 analysis.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)
    run_dir = root / "runs" / args.run_id
    blocks_path = run_dir / "blocks_design.json"
    raw_path = run_dir / "raw.csv"
    if not blocks_path.is_file():
        raise SystemExit(f"missing {blocks_path}")
    if not raw_path.is_file():
        raise SystemExit(f"missing {raw_path}")
    payload = json.loads(blocks_path.read_text(encoding="utf-8"))
    blocks = _blocks(payload)

    # Per-depth ratio-of-sums over blocks + cluster bootstrap for the saving.
    totals: dict[int, dict[str, float]] = {}
    for b in blocks:
        t = totals.setdefault(b["k"], {"j": 0.0, "c": 0, "n": 0})
        t["j"] += b["energy_j"]
        t["c"] += b["correct"]
        t["n"] += b["n"]
    acc = {k: v["c"] / v["n"] for k, v in totals.items()}
    epc = {k: (v["j"] / v["n"]) / (v["c"] / v["n"]) if v["c"] else None for k, v in totals.items()}

    rng = random.Random(SEED)
    by_k: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for b in blocks:
        by_k[b["k"]].append(b)

    def saving_of(sample: dict[int, list[dict[str, Any]]]) -> float:
        num = sum(b["energy_j"] for b in sample[1]) / sum(b["correct"] for b in sample[1])
        den = sum(b["energy_j"] for b in sample[4]) / sum(b["correct"] for b in sample[4])
        return 1 - num / den

    point = saving_of(by_k)
    boot = []
    for _ in range(N_BOOT):
        s = {k: [v[rng.randrange(len(v))] for _ in range(len(v))] for k, v in by_k.items()}
        if sum(b["correct"] for b in s[1]) and sum(b["correct"] for b in s[4]):
            boot.append(saving_of(s))
    boot.sort()

    # Oracle gap on paired questions.
    by_q: dict[str, dict[int, int]] = defaultdict(dict)
    with raw_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("valid", "1") == "1":
                by_q[row["question_id"]][int(row["k"])] = int(row["correct_em"])
    paired = {q: d for q, d in by_q.items() if 1 in d and 4 in d}
    if len(paired) < 100:
        raise SystemExit(f"too few paired questions: {len(paired)}")
    qs = list(paired)
    gap_point = sum(1 for q in qs if paired[q][1] or paired[q][4]) / len(qs) - sum(
        paired[q][4] for q in qs
    ) / len(qs)
    # One resample serves both terms: the gap is a paired contrast.
    gap_boot = []
    for _ in range(N_BOOT):
        sample = [qs[rng.randrange(len(qs))] for _ in range(len(qs))]
        gap_boot.append(
            sum(1 for q in sample if paired[q][1] or paired[q][4]) / len(sample)
            - sum(paired[q][4] for q in sample) / len(sample)
        )
    gap_boot.sort()

    estimates = {
        "run_id": args.run_id,
        "estimand": "E(k) = sum_b J_block / sum_b C, k in {1,4}; saving = 1 - E(1)/E(4)",
        "n_blocks": len(blocks),
        "accuracy": {str(k): acc[k] for k in sorted(acc)},
        "energy_per_query_j": {str(k): totals[k]["j"] / totals[k]["n"] for k in sorted(totals)},
        "energy_per_correct_j": {str(k): epc[k] for k in sorted(epc)},
        "saving_k1_vs_k4": {
            "point": point,
            "ci95": [_quantile(boot, 0.025), _quantile(boot, 0.975)],
            "n_boot": len(boot),
        },
    }
    gap = {
        "run_id": args.run_id,
        "estimand": "Gap = A_oracle{1,4} - A(4), paired within question",
        "n_paired": len(paired),
        "accuracy_k1": sum(paired[q][1] for q in qs) / len(qs),
        "accuracy_k4": sum(paired[q][4] for q in qs) / len(qs),
        "accuracy_oracle": sum(1 for q in qs if paired[q][1] or paired[q][4]) / len(qs),
        "gap_point": gap_point,
        "gap_ci95": [_quantile(gap_boot, 0.025), _quantile(gap_boot, 0.975)],
        "stop_threshold": STOP_THRESHOLD,
        "stop_verdict": "HALT" if gap_point < STOP_THRESHOLD else "PROCEED",
        "stop_rule": "Gap < 10% halts the distractor position conditions; the 6-dose main curve still runs.",
    }

    out_dir = root / "analysis" / "qc_fresh"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "estimates.json").write_text(json.dumps(estimates, indent=2), encoding="utf-8")
    (out_dir / "gap.json").write_text(json.dumps(gap, indent=2), encoding="utf-8")

    lines = [
        "# Phase 8 Step 1 - fresh k=4 gap",
        "",
        f"Run `{args.run_id}`; {len(blocks)} blocks, {len(paired)} paired questions.",
        "",
        f"A(1)={gap['accuracy_k1']:.4f} A(4)={gap['accuracy_k4']:.4f} "
        f"A_oracle={gap['accuracy_oracle']:.4f}.",
        f"Gap={gap_point:.4f} [{gap['gap_ci95'][0]:.4f}, {gap['gap_ci95'][1]:.4f}].",
        f"Saving k=1 vs k=4: {100 * point:.2f}% "
        f"[{100 * estimates['saving_k1_vs_k4']['ci95'][0]:.2f}, "
        f"{100 * estimates['saving_k1_vs_k4']['ci95'][1]:.2f}].",
        "",
        f"Stop rule (Gap < 10%): **{gap['stop_verdict']}** the position conditions.",
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
