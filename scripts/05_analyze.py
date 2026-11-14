#!/usr/bin/env python
"""05 — Analyze a completed sweep: A(k), J(k), E(k), fit, and P0 check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.stats.sweep import write_analysis  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze one registered sweep.")
    parser.add_argument("--run-id", required=True, help="Registered run identifier.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--raw", default=None, help="Raw CSV path override.")
    parser.add_argument("--out", default=None, help="Analysis output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    raw = Path(args.raw) if args.raw else root / "runs" / args.run_id / "raw.csv"
    out = Path(args.out) if args.out else root / "analysis" / args.run_id
    path = write_analysis(raw, out, run_id=args.run_id)
    print(f"Analysis: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
