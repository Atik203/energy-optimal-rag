"""Regression test for the Phase 7 block integrator.

The first live run failed because ``_block_energy`` passed ``PowerSample`` objects
to an integrator that expects ``(t_s, power_w)`` pairs. This test pins the
contract with a known answer: 10 s of constant 50 W above a 10 W idle floor is
400 J.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class _Sample:
    t_s: float
    power_w: float


def _load():
    spec = importlib.util.spec_from_file_location(
        "blocks_design", ROOT / "scripts" / "22_run_blocks_design.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def design():
    return _load()


def test_block_energy_constant_load(design):
    # 11 samples spanning 10 s at 50 W, idle 10 W -> (50-10)*10 = 400 J.
    samples = [_Sample(t_s=float(i), power_w=50.0) for i in range(11)]
    energy, power, duration = design._block_energy(samples, 10.0)
    assert energy == pytest.approx(400.0)
    assert power == pytest.approx(50.0)
    assert duration == pytest.approx(10.0)


def test_block_energy_clips_below_idle(design):
    samples = [_Sample(t_s=float(i), power_w=8.0) for i in range(3)]
    energy, _power, _duration = design._block_energy(samples, 10.0)
    assert energy == pytest.approx(0.0)


def test_block_energy_requires_two_samples(design):
    with pytest.raises(RuntimeError):
        design._block_energy([_Sample(t_s=0.0, power_w=50.0)], 10.0)


def test_block_energy_rejects_zero_duration(design):
    samples = [_Sample(t_s=1.0, power_w=50.0), _Sample(t_s=1.0, power_w=50.0)]
    with pytest.raises(RuntimeError):
        design._block_energy(samples, 10.0)
