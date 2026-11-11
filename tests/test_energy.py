"""Unit tests for energy integration, idle baseline, blocks, meter, and nonce.

Standard library plus pytest only: no numpy, pandas, torch, or GPU. Nonces are
random, so tests assert the shape and alphabet, never a fixed value.
"""

from __future__ import annotations

import re

import pytest

from rag_energy.energy.blocks import block_scale_factors, calibrated_energy
from rag_energy.energy.idle import IdleStats, summarize_idle
from rag_energy.energy.integrate import idle_subtract, mean_power, trapezoid_joules
from rag_energy.energy.meter import WallMeterReading, calibration_factor, wall_meter_joules
from rag_energy.energy.nonce import DEFAULT_HEX_CHARS, make_nonce, nonce_line

HEX_RE = re.compile(r"^[0-9a-f]+$")


def test_trapezoid_joules_integrates_triangle() -> None:
    # two trapezoids of width 1 and heights (0, 2) then (2, 0)
    assert trapezoid_joules([(0.0, 0.0), (1.0, 2.0), (2.0, 0.0)]) == pytest.approx(2.0)


def test_trapezoid_joules_integrates_constant_power() -> None:
    # 4 W held for 2 s
    assert trapezoid_joules([(0.0, 4.0), (2.0, 4.0)]) == pytest.approx(8.0)


def test_trapezoid_joules_accepts_an_iterable() -> None:
    samples = ((t, 3.0) for t in (0.0, 1.0, 2.0))
    assert trapezoid_joules(samples) == pytest.approx(6.0)


@pytest.mark.parametrize("samples", [[], [(0.0, 5.0)]])
def test_trapezoid_joules_returns_zero_below_two_samples(
    samples: list[tuple[float, float]],
) -> None:
    assert trapezoid_joules(samples) == 0.0


def test_trapezoid_joules_rejects_decreasing_timestamps() -> None:
    with pytest.raises(ValueError, match="non-decreasing"):
        trapezoid_joules([(0.0, 1.0), (2.0, 1.0), (1.0, 1.0)])


def test_idle_subtract_removes_baseline_energy() -> None:
    # 2 s at 3 W idle = 6 J of baseline, leaving 4 J
    assert idle_subtract(10.0, 2.0, 3.0) == pytest.approx(4.0)


def test_idle_subtract_clips_at_zero() -> None:
    assert idle_subtract(5.0, 10.0, 1.0) == 0.0


def test_idle_subtract_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        idle_subtract(10.0, -1.0, 3.0)


def test_mean_power_divides_energy_by_duration() -> None:
    assert mean_power(10.0, 2.0) == pytest.approx(5.0)


@pytest.mark.parametrize("duration", [0.0, -1.0])
def test_mean_power_rejects_non_positive_duration(duration: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        mean_power(10.0, duration)


def test_summarize_idle_computes_mean_sd_and_cv() -> None:
    stats = summarize_idle([10.0, 12.0, 14.0])
    assert isinstance(stats, IdleStats)
    assert stats.n == 3
    assert stats.mean_w == pytest.approx(12.0)
    assert stats.sd_w == pytest.approx(2.0)
    assert stats.cv == pytest.approx(1.0 / 6.0)


def test_summarize_idle_is_constant_for_constant_samples() -> None:
    stats = summarize_idle([17.63, 17.63, 17.63, 17.63])
    assert stats.mean_w == pytest.approx(17.63)
    assert stats.sd_w == pytest.approx(0.0)
    assert stats.cv == pytest.approx(0.0)


@pytest.mark.parametrize("samples", [[], [12.0]])
def test_summarize_idle_requires_two_samples(samples: list[float]) -> None:
    with pytest.raises(ValueError, match="at least two"):
        summarize_idle(samples)


def test_block_scale_factors_scale_raw_sum_to_block_total() -> None:
    assert block_scale_factors([1.0, 2.0], 6.0) == pytest.approx([2.0, 2.0])


def test_block_scale_factors_preserve_per_query_shape() -> None:
    factors = block_scale_factors([1.0, 3.0, 4.0], 16.0)
    assert factors == pytest.approx([2.0, 2.0, 2.0])


@pytest.mark.parametrize(
    ("per_query", "block_total", "match"),
    [
        ([], 6.0, "non-empty"),
        ([1.0, -1.0], 6.0, "non-negative"),
        ([1.0, 2.0], 0.0, "positive"),
        ([1.0, 2.0], -6.0, "positive"),
        ([0.0, 0.0], 6.0, "raw per-query"),
    ],
)
def test_block_scale_factors_reject_invalid_input(
    per_query: list[float], block_total: float, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        block_scale_factors(per_query, block_total)


def test_calibrated_energy_applies_factor() -> None:
    assert calibrated_energy([1.0, 2.0], 2.0) == pytest.approx([2.0, 4.0])


@pytest.mark.parametrize("factor", [0.0, -1.0])
def test_calibrated_energy_rejects_non_positive_factor(factor: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        calibrated_energy([1.0, 2.0], factor)


def test_wall_meter_joules_converts_watt_hours() -> None:
    assert wall_meter_joules(1.0) == pytest.approx(3600.0)
    assert wall_meter_joules(0.5) == pytest.approx(1800.0)


def test_wall_meter_joules_rejects_negative_energy() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        wall_meter_joules(-0.1)


def test_calibration_factor_is_system_over_integrated() -> None:
    assert calibration_factor(100.0, 80.0) == pytest.approx(1.25)


@pytest.mark.parametrize("integrated", [0.0, -80.0])
def test_calibration_factor_rejects_non_positive_integrated(integrated: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        calibration_factor(100.0, integrated)


def test_wall_meter_reading_average_power() -> None:
    # 0.5 Wh over 60 s = 1800 J / 60 s = 30 W
    reading = WallMeterReading(condition="k8", n_queries=30, duration_s=60.0, energy_wh=0.5)
    assert reading.average_power_w == pytest.approx(30.0)


def test_wall_meter_reading_rejects_non_positive_duration() -> None:
    reading = WallMeterReading(condition="k8", n_queries=30, duration_s=0.0, energy_wh=0.5)
    with pytest.raises(ValueError, match="positive"):
        _ = reading.average_power_w


def test_make_nonce_has_default_hex_length() -> None:
    nonce = make_nonce()
    assert DEFAULT_HEX_CHARS == 10
    assert len(nonce) == 10
    assert HEX_RE.fullmatch(nonce)


@pytest.mark.parametrize("hex_chars", [2, 4, 10])
def test_make_nonce_respects_requested_length(hex_chars: int) -> None:
    nonce = make_nonce(hex_chars)
    assert len(nonce) == hex_chars
    assert HEX_RE.fullmatch(nonce)


def test_make_nonce_repeated_draws_stay_well_formed() -> None:
    nonces = [make_nonce(10) for _ in range(20)]
    assert all(len(nonce) == 10 and HEX_RE.fullmatch(nonce) for nonce in nonces)


@pytest.mark.parametrize("hex_chars", [0, -2, 1, 3, 5])
def test_make_nonce_rejects_invalid_length(hex_chars: int) -> None:
    with pytest.raises(ValueError, match="positive even"):
        make_nonce(hex_chars)


def test_nonce_line_formats_first_line() -> None:
    assert nonce_line("abc") == "[request abc]"


def test_nonce_line_rejects_empty_nonce() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        nonce_line("")
