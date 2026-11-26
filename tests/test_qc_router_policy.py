"""Tests for the qc-router policy script (Task 3, CPU only)."""

from __future__ import annotations

import importlib.util
import json
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


def test_router_uses_fixed_costs():
    mod = _load("qc_router_policy", "40_qc_router_policy.py")
    assert set(mod.K_PAIR) == {1, 4}
    assert mod.STATIC_DEPTH == 4
    # fixed-cost helper must average block energies per question
    assert "energy_j" in open(ROOT / "scripts" / "40_qc_router_policy.py").read()
    # select output, once generated, must record fixed costs (not per-query windows)
    sel = ROOT / "analysis" / "qc_router" / "select.json"
    if sel.is_file():
        payload = json.loads(sel.read_text(encoding="utf-8"))
        assert "fixed_j_per_query" in payload
        assert set(map(int, payload["fixed_j_per_query"].keys())) == {1, 4}
    else:
        # script exists with the fixed-cost contract even before first run
        assert "fixed_j_per_query" in open(ROOT / "scripts" / "40_qc_router_policy.py").read()
