#!/usr/bin/env python
"""02 — Run a depth sweep."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.runner import run_depth_sweep  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one registered depth sweep.")
    parser.add_argument(
        "--config",
        default="configs/runs/squad_qwen4b_p0.toml",
        help="Run config path.",
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--processed", default=None, help="Prepared-data directory.")
    parser.add_argument("--out", default=None, help="Run output root.")
    parser.add_argument("--registry", default=None, help="Registry CSV path.")
    parser.add_argument("--limit", type=int, default=None, help="Limit questions.")
    parser.add_argument("--resume", action="store_true", help="Resume a partial run.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = run_depth_sweep(
        Path(args.config),
        root=Path(args.root),
        processed_dir=Path(args.processed) if args.processed else None,
        out_root=Path(args.out) if args.out else None,
        registry_path=Path(args.registry) if args.registry else None,
        limit_questions=args.limit,
        resume=args.resume,
    )
    print(f"Raw CSV: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
