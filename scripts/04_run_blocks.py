#!/usr/bin/env python
"""04 — Run block energy calibration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.runner import run_block_calibration  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calibrate per-depth energy blocks.")
    parser.add_argument(
        "--config",
        default="configs/runs/squad_qwen4b_p0.toml",
        help="Run config path.",
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--processed", default=None, help="Prepared-data directory.")
    parser.add_argument("--out", default=None, help="Run output root.")
    parser.add_argument("--cooldown", type=float, default=0.0, help="Cooldown seconds.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = run_block_calibration(
        Path(args.config),
        root=Path(args.root),
        processed_dir=Path(args.processed) if args.processed else None,
        out_root=Path(args.out) if args.out else None,
        cooldown_s=args.cooldown,
    )
    print(f"Blocks: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
