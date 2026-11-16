#!/usr/bin/env python
"""03 - Run an energy-tax condition.

Calibrates a dummy GPU workload to the configured delta, injects it into a
standard depth sweep, then runs block calibration, repeat CV, and descriptive
analysis. The dummy work runs inside the per-query NVML window, so its energy
is measured rather than asserted.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import tomllib as _tomllib  # noqa: E402

from rag_energy.runner import (  # noqa: E402
    run_block_calibration,
    run_depth_sweep,
    run_repeat_cv,
)
from rag_energy.stats.sweep import write_analysis  # noqa: E402
from rag_energy.tax import TaxedReader, _calibrate_dummy  # noqa: E402


def _make_run_config(tax_config: dict, tax_id: str, root: Path) -> Path:
    template = (root / "configs" / "runs" / "squad_qwen4b.toml").read_text(encoding="utf-8")
    template = template.replace('run_id = "squad_qwen4b_p1"', f'run_id = "{tax_id}"')
    template = template.replace("n_questions = 1000", f"n_questions = {int(tax_config['n_questions'])}")
    template = template.replace(
        "k_grid = [0, 1, 2, 4, 8, 16, 32]",
        "k_grid = " + str(tax_config["k_grid"]).replace(" ", ""),
    )
    template = template.replace('id_split = "p1_primary"', 'id_split = "replication"')
    template = template.replace('phase = "P1"', 'phase = "P2"')
    # Remove grid reference; tax runs do not use a named grid.
    template = template.replace('grid_id = "primary_k7"\n', '')
    template = template.replace(
        'purpose = "Powered SQuAD rerun (n=1000, 7 depths). Primary 5pp non-inferiority."',
        f'purpose = "Energy tax arm: {tax_id}."',
    )
    out = root / "configs" / "runs" / f"{tax_id}.toml"
    out.write_text(template, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one energy-tax condition.")
    parser.add_argument("--config", required=True, help="Tax config TOML.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--processed", default=None, help="Prepared-data directory.")
    parser.add_argument("--out", default=None, help="Run output root.")
    parser.add_argument("--cooldown", type=float, default=0.0, help="Cooldown seconds.")
    args = parser.parse_args()

    root = Path(args.root)
    tax_config = tomllib.loads((root / args.config).read_text(encoding="utf-8"))
    tax_id = str(tax_config["tax_id"])
    tax_kind = str(tax_config["tax_kind"])

    if tax_kind == "fixed":
        target = float(tax_config["delta_a_j"])
    else:
        target = float(tax_config["delta_b_j_per_passage"])

    print(f"Calibrating dummy work for {tax_id} to {target:.4f} J ...")
    dummy_fn, iters, measured = _calibrate_dummy(target)
    print(f"Calibrated: iters={iters}, measured={measured:.4f} J (target {target:.4f} J)")

    run_config_path = _make_run_config(tax_config, tax_id, root)

    base_reader = None
    from rag_energy.runner import _default_reader

    import tomllib as _t

    merged = _t.loads(run_config_path.read_text(encoding="utf-8"))
    # Merge base.toml manually by using resolve? Simpler: use load_run_spec via runner.
    from rag_energy.runner import load_run_spec

    spec = load_run_spec(run_config_path, root=root)
    base_reader = _default_reader(spec.config)
    taxed_reader = TaxedReader(base_reader, tax_kind, dummy_fn)

    processed_dir = Path(args.processed) if args.processed else None
    out_root = Path(args.out) if args.out else None

    raw_path = run_depth_sweep(
        run_config_path,
        root=root,
        processed_dir=processed_dir,
        out_root=out_root,
        reader=taxed_reader,
        limit_questions=int(tax_config["n_questions"]),
    )
    print(f"Raw CSV: {raw_path}")

    blocks_path = run_block_calibration(
        run_config_path,
        root=root,
        processed_dir=processed_dir,
        out_root=out_root,
        reader=taxed_reader,
        cooldown_s=args.cooldown,
    )
    print(f"Blocks: {blocks_path}")

    repeat_path = run_repeat_cv(
        run_config_path,
        root=root,
        processed_dir=processed_dir,
        out_root=out_root,
        reader=taxed_reader,
        cooldown_s=args.cooldown,
    )
    print(f"Repeat: {repeat_path}")

    out_dir = (out_root or root / "runs") / tax_id
    analysis_dir = root / "analysis" / tax_id
    analysis_dir.mkdir(parents=True, exist_ok=True)
    from rag_energy.stats.sweep import write_analysis

    write_analysis(raw_path, analysis_dir, tax_id)
    print(f"Analysis: {analysis_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY