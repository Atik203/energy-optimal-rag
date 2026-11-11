"""Arithmetic tests for the power calculations behind the 5 pp test.

These pin the planning table documented in ``docs/IMPLEMENTATION_PLAN.md`` and
``prereg/PREREGISTRATION.md``. The discordant rate of 0.08 and its implied SD of
about 0.283 are planning assumptions, not measured values.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from rag_energy.stats.power import (
    minimum_detectable_effect,
    noninferiority_power,
    paired_difference_se,
)

ROOT = Path(__file__).resolve().parents[1]
# sqrt(0.08): the SD of one paired difference implied by the planning rate.
PLANNING_SD = 0.2828427125


def _load_power_script() -> ModuleType:
    """Load ``scripts/06_power.py``, whose filename is not a valid identifier."""
    spec = importlib.util.spec_from_file_location(
        "power_table_script", ROOT / "scripts" / "06_power.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_paired_difference_se() -> None:
    # sqrt(0.08 / 1000) J-free proportion: about 0.9 pp at n=1,000.
    assert paired_difference_se(0.08, 1000) == pytest.approx(0.008944, rel=1e-4)


def test_mde_at_pilot_size() -> None:
    assert minimum_detectable_effect(200, PLANNING_SD) == pytest.approx(0.04966, abs=5e-4)


def test_mde_at_primary_size() -> None:
    assert minimum_detectable_effect(1000, PLANNING_SD) == pytest.approx(0.02222, abs=5e-4)


def test_power_at_zero_difference() -> None:
    assert noninferiority_power(1000, 0.0, 0.05, PLANNING_SD) > 0.99


def test_power_at_three_point_difference() -> None:
    assert noninferiority_power(1000, 0.03, 0.05, PLANNING_SD) == pytest.approx(0.72, abs=0.02)


def test_build_table_matches_documented_assumptions() -> None:
    script = _load_power_script()
    table = script.build_table([200, 1000], [0.0, 0.01, 0.02, 0.03], 0.05, 0.08, 0.05)
    assert "Assumed discordant rate = 0.080" in table
    assert "| 200 | 4.973% |" in table
    assert "| 1000 | 2.224% |" in table


@pytest.mark.parametrize("bad_rate", [-0.01, 1.01])
def test_paired_difference_se_rejects_bad_rate(bad_rate: float) -> None:
    with pytest.raises(ValueError):
        paired_difference_se(bad_rate, 1000)


@pytest.mark.parametrize("n", [0, -1])
def test_paired_difference_se_rejects_bad_n(n: int) -> None:
    with pytest.raises(ValueError):
        paired_difference_se(0.08, n)


@pytest.mark.parametrize("n", [0, -1])
def test_mde_rejects_bad_n(n: int) -> None:
    with pytest.raises(ValueError):
        minimum_detectable_effect(n, PLANNING_SD)


@pytest.mark.parametrize("sd", [0.0, -0.01])
def test_mde_rejects_bad_sd(sd: float) -> None:
    with pytest.raises(ValueError):
        minimum_detectable_effect(1000, sd)


@pytest.mark.parametrize("alpha", [0.0, 0.5, -0.01, 0.6])
def test_mde_rejects_bad_alpha(alpha: float) -> None:
    with pytest.raises(ValueError):
        minimum_detectable_effect(1000, PLANNING_SD, alpha=alpha)


@pytest.mark.parametrize("power", [0.5, 0.4, 1.0, 1.1])
def test_mde_rejects_bad_power(power: float) -> None:
    with pytest.raises(ValueError):
        minimum_detectable_effect(1000, PLANNING_SD, power=power)


@pytest.mark.parametrize("n", [0, -1])
def test_power_rejects_bad_n(n: int) -> None:
    with pytest.raises(ValueError):
        noninferiority_power(n, 0.0, 0.05, PLANNING_SD)


@pytest.mark.parametrize("margin", [0.0, -0.01])
def test_power_rejects_bad_margin(margin: float) -> None:
    with pytest.raises(ValueError):
        noninferiority_power(1000, 0.0, margin, PLANNING_SD)


@pytest.mark.parametrize("sd", [0.0, -0.01])
def test_power_rejects_bad_sd(sd: float) -> None:
    with pytest.raises(ValueError):
        noninferiority_power(1000, 0.0, 0.05, sd)


@pytest.mark.parametrize("alpha", [0.0, 0.5, -0.01, 0.6])
def test_power_rejects_bad_alpha(alpha: float) -> None:
    with pytest.raises(ValueError):
        noninferiority_power(1000, 0.0, 0.05, PLANNING_SD, alpha=alpha)
