#!/usr/bin/env python
"""05 — Analyze a completed sweep.

P1 runs use the confirmatory analysis (non-inferiority, paired bootstrap,
identity, certification, gates). Other phases use the P0 descriptive analysis.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.config import load_toml  # noqa: E402
from rag_energy.runner import _prereg_sha256  # noqa: E402
from rag_energy.stats.p1 import write_p1_analysis  # noqa: E402
from rag_energy.stats.sweep import write_analysis  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze one registered sweep.")
    parser.add_argument("--run-id", required=True, help="Registered run identifier.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--raw", default=None, help="Raw CSV path override.")
    parser.add_argument("--out", default=None, help="Analysis output directory.")
    parser.add_argument(
        "--p1",
        action="store_true",
        help="Force the P1 confirmatory analysis (otherwise read from the manifest).",
    )
    parser.add_argument("--resamples", type=int, default=10_000, help="Bootstrap resamples.")
    return parser


def _is_p1(root: Path, run_id: str) -> bool:
    manifest = root / "runs" / run_id / "manifest.json"
    if not manifest.is_file():
        return False
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return str(payload.get("phase", "")).upper() == "P1"


def _check_prereg_hash(root: Path, run_id: str) -> str | None:
    """Refuse to analyze when the frozen prereg hash differs from the run manifest."""
    manifest = root / "runs" / run_id / "manifest.json"
    if not manifest.is_file():
        return None
    recorded = str(json.loads(manifest.read_text(encoding="utf-8")).get("prereg_sha256", ""))
    current = _prereg_sha256(root)
    if recorded and current and recorded != current:
        raise SystemExit(
            "prereg hash mismatch: the run manifest records "
            f"{recorded[:16]}..., the current frozen prereg hashes to {current[:16]}...; "
            "record an amendment before analyzing."
        )
    return current or None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    raw = Path(args.raw) if args.raw else root / "runs" / args.run_id / "raw.csv"
    out = Path(args.out) if args.out else root / "analysis" / args.run_id
    prereg_sha = _check_prereg_hash(root, args.run_id)
    if args.p1 or _is_p1(root, args.run_id):
        prereg_path = root / "configs" / "analysis" / "prereg.toml"
        prereg = load_toml(prereg_path) if prereg_path.is_file() else {}
        path = write_p1_analysis(
            raw,
            out,
            run_id=args.run_id,
            root=root,
            config=prereg,
            resamples=args.resamples,
        )
    else:
        path = write_analysis(raw, out, run_id=args.run_id)
    print(f"Analysis: {path}")
    if prereg_sha:
        print(f"Prereg SHA-256: {prereg_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
