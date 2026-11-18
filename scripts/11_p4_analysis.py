#!/usr/bin/env python
"""11 - P4 theory validation across registered arms.

Reads only registered raw CSVs; writes identity, coverage, margin, scoring, and
certification summaries under analysis/p4/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.stats.p4 import write_p4_analysis  # noqa: E402

ARMS = (
    "squad_qwen4b_p1",
    "squad_qwen15b_p2",
    "hotpot_qwen4b_p2",
    "squad_llama3b_p2",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="P4 theory validation summaries.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--out", default=None, help="Output directory.")
    args = parser.parse_args()
    root = Path(args.root)
    raw_paths = {arm: root / "runs" / arm / "raw.csv" for arm in ARMS}
    missing = [arm for arm, path in raw_paths.items() if not path.is_file()]
    if missing:
        raise SystemExit(f"missing raw CSVs: {missing}")
    out = Path(args.out) if args.out else root / "analysis" / "p4"
    print(f"P4 analysis: {write_p4_analysis(raw_paths, out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
