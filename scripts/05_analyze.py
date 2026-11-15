#!/usr/bin/env python
"""05 — Analyze a completed sweep.

P1 runs use the confirmatory analysis (non-inferiority, paired bootstrap,
identity, certification, gates). P2 runs use the direction-only replication
analysis (H7). Other phases use the P0 descriptive analysis.
A P1/P2 run must be registered `completed`; `--allow-partial` is for development
only and is labeled in the output.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.config import load_toml  # noqa: E402
from rag_energy.runner import _prereg_sha256  # noqa: E402
from rag_energy.stats.p1 import write_p1_analysis  # noqa: E402
from rag_energy.stats.p2 import write_p2_analysis  # noqa: E402
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
        help="Force the P1 confirmatory analysis (otherwise read from the registry/manifest).",
    )
    parser.add_argument("--resamples", type=int, default=10_000, help="Bootstrap resamples.")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Development only: analyze an incomplete or unregistered run.",
    )
    return parser


def _registry_row(root: Path, run_id: str) -> dict[str, str] | None:
    path = root / "runs" / "registry.csv"
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("run_id") == run_id:
                return dict(row)
    return None


def _manifest(root: Path, run_id: str) -> dict | None:
    path = root / "runs" / run_id / "manifest.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _phase(root: Path, run_id: str) -> str:
    manifest = _manifest(root, run_id)
    if manifest and manifest.get("phase"):
        return str(manifest["phase"]).upper()
    row = _registry_row(root, run_id)
    return str(row.get("phase", "")).upper() if row else ""


def _check_prereg_hash(root: Path, run_id: str) -> str | None:
    """Refuse to analyze when the frozen prereg hash differs from the run record."""
    recorded = ""
    manifest = _manifest(root, run_id)
    if manifest:
        recorded = str(manifest.get("prereg_sha256", ""))
    if not recorded:
        row = _registry_row(root, run_id)
        recorded = str(row.get("prereg_sha256", "")) if row else ""
    current = _prereg_sha256(root)
    if not current:
        raise SystemExit(
            "prereg config is not frozen; set configs/analysis/prereg.toml frozen=true "
            "and tag the freeze before a P1 analysis."
        )
    if recorded and recorded != current:
        raise SystemExit(
            "prereg hash mismatch: the run records "
            f"{recorded[:16]}..., the current frozen prereg hashes to {current[:16]}...; "
            "record an amendment before analyzing."
        )
    if not recorded:
        raise SystemExit(
            "run has no recorded prereg hash; register the frozen hash before analyzing."
        )
    return current


def _check_complete(root: Path, run_id: str, raw: Path) -> None:
    row = _registry_row(root, run_id)
    if row is None:
        raise SystemExit(f"{run_id} is not registered; use --allow-partial for development.")
    if row.get("status") != "completed":
        raise SystemExit(
            f"{run_id} is registered {row.get('status')!r}, not 'completed'; "
            "finish the run or use --allow-partial."
        )
    expected = int(row["n_questions"]) * len(str(row["k_grid"]).split("|"))
    with raw.open("r", encoding="utf-8", newline="") as handle:
        actual = sum(1 for _ in csv.DictReader(handle))
    if actual != expected:
        raise SystemExit(
            f"{run_id}: raw.csv has {actual} rows, expected {expected} "
            f"(n_questions x k_grid); use --allow-partial for development."
        )


def _run_config(root: Path, run_id: str) -> dict:
    """Load the run config recorded in the registry, if it still exists."""
    row = _registry_row(root, run_id) or {}
    config_path = str(row.get("config_path", "")).strip()
    if not config_path:
        return {}
    path = root / config_path
    return load_toml(path) if path.is_file() else {}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    raw = Path(args.raw) if args.raw else root / "runs" / args.run_id / "raw.csv"
    out = Path(args.out) if args.out else root / "analysis" / args.run_id
    phase = _phase(root, args.run_id)
    is_p1 = args.p1 or phase == "P1"
    if is_p1:
        if not args.allow_partial:
            _check_complete(root, args.run_id, raw)
        prereg_sha = _check_prereg_hash(root, args.run_id)
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
        print(f"Prereg SHA-256: {prereg_sha}")
    elif phase == "P2":
        if not args.allow_partial:
            _check_complete(root, args.run_id, raw)
        prereg_sha = _check_prereg_hash(root, args.run_id)
        prereg_path = root / "configs" / "analysis" / "prereg.toml"
        prereg = load_toml(prereg_path) if prereg_path.is_file() else {}
        margin_pp = prereg.get("primary", {}).get("margin_pp")
        path = write_p2_analysis(
            raw,
            out,
            run_id=args.run_id,
            root=root,
            config=_run_config(root, args.run_id),
            resamples=args.resamples,
            margin=None if margin_pp is None else float(margin_pp) / 100.0,
        )
        print(f"Prereg SHA-256: {prereg_sha}")
    else:
        path = write_analysis(raw, out, run_id=args.run_id)
    print(f"Analysis: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
