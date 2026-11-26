"""Tests for the router eval-CI script (Task 6, CPU only)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_eval_ci_helpers():
    mod = _load("qc_router_eval", "41_qc_router_eval.py")
    assert mod._quantile([0.0, 0.10], 0.5) == 0.05
    assert mod.STOP_GAP == 0.10
    assert mod.N_BOOT == 10000
    assert mod.TOST_PP == 2.0
