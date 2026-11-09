"""Run orchestration.

The runner owns the order of operations for one depth sweep:

1. load and validate the run config,
2. build the BM25 index once,
3. warm up, measure idle, run randomized blocks of questions at each depth,
4. attach the per-request nonce, record raw rows,
5. run block calibration and write ``blocks.json``,
6. register the run in ``runs/registry.csv``.

Implemented in P0. This scaffold exposes the contract only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag_energy.config import load_toml, validate_config


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    config_path: Path
    config: dict[str, Any]


def load_run_spec(config_path: Path) -> RunSpec:
    """Load and validate a run config, returning a typed spec."""
    problems = validate_config(config_path)
    if problems:
        raise ValueError("; ".join(problems))
    data = load_toml(config_path)
    return RunSpec(run_id=str(data["run_id"]), config_path=config_path, config=data)


def run_depth_sweep(config_path: Path) -> Path:
    """Execute one depth sweep and return the raw CSV path. Implemented in P0."""
    raise NotImplementedError(
        "run_depth_sweep is implemented in P0; see docs/IMPLEMENTATION_PLAN.md section 5."
    )


def run_block_calibration(config_path: Path) -> Path:
    """Run 20-query block calibration and return ``blocks.json``. Implemented in P0."""
    raise NotImplementedError("run_block_calibration is implemented in P0.")
