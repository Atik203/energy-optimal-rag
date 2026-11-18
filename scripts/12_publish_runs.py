#!/usr/bin/env python
"""12 - Publish sanitized per-query tables.

Writes gzip CSVs that let a reader rebuild every energy/accuracy table without
redistributing question text, gold answers, predictions, or nonces.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNS = (
    "squad_qwen4b_p1",
    "squad_qwen15b_p2",
    "hotpot_qwen4b_p2",
    "squad_llama3b_p2",
    "fixed_a",
    "per_passage_b",
    "boundary_qwen4b_p2",
    "squad_qwen4b_ctx16k_p2",
    "squad_qwen4b_ctx4k_p2",
)

FIELDS = (
    "run_id",
    "question_id",
    "question_order",
    "k",
    "order_in_question",
    "correct_em",
    "correct_lenient",
    "f1",
    "j_gpu_raw",
    "j_gpu_calibrated",
    "j_retrieval_proxy",
    "j_total",
    "latency_s",
    "prompt_tokens",
    "output_tokens",
    "load_s",
    "valid",
    "invalid_reason",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Write sanitized per-query tables.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.root)
    out = Path(args.out) if args.out else root / "artifacts" / "release"
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for run_id in RUNS:
        raw = root / "runs" / run_id / "raw.csv"
        if not raw.is_file():
            print(f"skip {run_id}: no raw.csv")
            continue
        target = out / f"{run_id}_per_query.csv.gz"
        with raw.open("r", encoding="utf-8", newline="") as source, gzip.open(
            target, "wt", encoding="utf-8", newline=""
        ) as dest:
            reader = csv.DictReader(source)
            writer = csv.DictWriter(dest, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            for row in reader:
                writer.writerow(row)
        written.append(target)
    print(f"wrote {len(written)} files to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
