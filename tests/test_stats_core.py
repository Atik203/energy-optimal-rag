"""Unit tests for the ratio estimand, curve models, identity, and multiplicity.

Standard library plus pytest only: no numpy, pandas, torch, or GPU.
"""

from __future__ import annotations

import math

import pytest

from rag_energy.stats.identity import elasticity, identity_gap
from rag_energy.stats.models import AffineFit, affine_fit, coverage_accuracy
from rag_energy.stats.multiplicity import holm_adjust, reject_holm
from rag_energy.stats.ratio import (
    delta_method_variance,
    energy_savings_pct,
    ratio_of_expectations,
    ratio_standard_error,
)

J = [1.0, 2.0, 3.0]
C = [0, 1, 1]


def test_ratio_of_expectations_divides_total_energy_by_correct_count() -> None:
    assert ratio_of_expectations([2.0, 4.0], [1, 0]) == pytest.approx(6.0)


def test_ratio_of_expectations_is_infinite_when_nothing_is_correct() -> None:
    assert ratio_of_expectations([2.0, 4.0], [0, 0]) == math.inf


@pytest.mark.parametrize(
    ("joules", "correct", "match"),
    [
        ([1.0, 2.0], [1], "same length"),
        ([1.0, -1.0], [1, 0], "non-negative"),
        ([1.0, 2.0], [1, 2], "0/1"),
        ([], [], "at least one"),
    ],
)
def test_ratio_of_expectations_rejects_invalid_input(
    joules: list[float], correct: list[int], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        ratio_of_expectations(joules, correct)


def test_delta_method_variance_matches_hand_computation() -> None:
    # mean(J) = 2, mean(C) = 2/3, Var(J) = 1, Var(C) = 1/3, Cov(J, C) = 1/2
    # Var = 1/(2/3)^2 + 4*(1/3)/(2/3)^4 - 2*2*(1/2)/(2/3)^3
    #     = 2.25 + 6.75 - 6.75 = 2.25
    assert delta_method_variance(J, C) == pytest.approx(2.25)


def test_ratio_standard_error_scales_variance_by_n() -> None:
    assert ratio_standard_error(J, C) == pytest.approx(math.sqrt(2.25 / 3.0))


def test_ratio_standard_error_requires_two_observations() -> None:
    with pytest.raises(ValueError, match="at least two"):
        ratio_standard_error([1.0], [1])


def test_delta_method_is_infinite_when_accuracy_is_zero() -> None:
    assert delta_method_variance([1.0, 2.0], [0, 0]) == math.inf
    assert ratio_standard_error([1.0, 2.0], [0, 0]) == math.inf


@pytest.mark.parametrize(
    ("joules", "correct"),
    [
        ([1.0], [1]),
        ([], []),
        ([1.0, 2.0], [1]),
    ],
)
def test_delta_method_rejects_invalid_input(joules: list[float], correct: list[int]) -> None:
    with pytest.raises(ValueError):
        delta_method_variance(joules, correct)


def test_delta_method_rejects_negative_energy() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        delta_method_variance([-1.0, 2.0], [1, 0])


def test_delta_method_rejects_non_binary_correctness() -> None:
    with pytest.raises(ValueError, match="0/1"):
        delta_method_variance([1.0, 2.0], [0, 2])


def test_energy_savings_pct_matches_pilot_reference_point() -> None:
    # 100 * (1 - 48.27 / 157.1) = 69.274... %
    assert energy_savings_pct(157.1, 48.27) == pytest.approx(69.28, abs=0.01)


def test_energy_savings_pct_is_zero_for_equal_energy() -> None:
    assert energy_savings_pct(50.0, 50.0) == pytest.approx(0.0)


@pytest.mark.parametrize("reference", [0.0, -1.0, math.inf])
def test_energy_savings_pct_rejects_invalid_reference(reference: float) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        energy_savings_pct(reference, 10.0)


def test_affine_fit_recovers_exact_line() -> None:
    fit = affine_fit([0.0, 1.0, 2.0], [1.0, 3.0, 5.0])
    assert isinstance(fit, AffineFit)
    assert fit.slope == pytest.approx(2.0)
    assert fit.intercept == pytest.approx(1.0)
    assert fit.r_squared == pytest.approx(1.0)


def test_affine_fit_reports_r_squared_below_one() -> None:
    # mean(y) = 2, SS_tot = 6, SS_res = 1.5 -> R^2 = 0.75
    fit = affine_fit([0.0, 1.0, 2.0], [1.0, 1.0, 4.0])
    assert fit.slope == pytest.approx(1.5)
    assert fit.intercept == pytest.approx(0.5)
    assert fit.r_squared == pytest.approx(0.75)


@pytest.mark.parametrize(
    ("xs", "ys", "match"),
    [
        ([0.0, 1.0, 2.0], [1.0, 3.0], "same length"),
        ([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], "constant"),
        ([0.0], [1.0], "at least two"),
        ([], [], "at least two"),
    ],
)
def test_affine_fit_rejects_invalid_input(xs: list[float], ys: list[float], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        affine_fit(xs, ys)


@pytest.mark.parametrize(
    ("a0", "p", "k", "expected"),
    [
        (0.5, 0.5, 0, 0.5),
        (0.5, 0.5, 2, 0.875),
        (0.8, 0.25, 1, 0.85),
        (0.0, 1.0, 3, 1.0),
        (0.2, 1.0, 5, 1.0),
        (0.0, 0.5, 0, 0.0),
    ],
)
def test_coverage_accuracy(a0: float, p: float, k: int, expected: float) -> None:
    assert coverage_accuracy(a0, p, k) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("a0", "p", "k", "match"),
    [
        (-0.1, 0.5, 1, "a0"),
        (1.0, 0.5, 1, "a0"),
        (0.5, 0.0, 1, "p must"),
        (0.5, 1.5, 1, "p must"),
        (0.5, 0.5, -1, "non-negative"),
    ],
)
def test_coverage_accuracy_rejects_invalid_input(a0: float, p: float, k: int, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        coverage_accuracy(a0, p, k)


def test_elasticity_central_difference() -> None:
    # derivative (12 - 8) / 2 = 2; elasticity = 2 * 2 / 10 = 0.4
    assert elasticity(2.0, 10.0, 8.0, 12.0) == pytest.approx(0.4)


def test_elasticity_with_step_two() -> None:
    # derivative (12 - 8) / 4 = 1; elasticity = 2 * 1 / 10 = 0.2
    assert elasticity(2.0, 10.0, 8.0, 12.0, step=2.0) == pytest.approx(0.2)


def test_elasticity_is_zero_for_constant_curve() -> None:
    assert elasticity(4.0, 10.0, 10.0, 10.0) == pytest.approx(0.0)


def test_elasticity_is_infinite_at_zero_value() -> None:
    assert elasticity(2.0, 0.0, 0.5, 0.5) == math.inf


@pytest.mark.parametrize("step", [0.0, -1.0])
def test_elasticity_rejects_non_positive_step(step: float) -> None:
    with pytest.raises(ValueError, match="step must be positive"):
        elasticity(2.0, 10.0, 8.0, 12.0, step=step)


def test_identity_gap_is_elasticity_difference() -> None:
    assert identity_gap(0.5, 0.2) == pytest.approx(0.3)
    assert identity_gap(0.1, 0.1) == pytest.approx(0.0)
    assert identity_gap(0.044, 0.700) == pytest.approx(-0.656)


def test_holm_adjust_matches_hand_computation() -> None:
    # sorted 0.01, 0.03, 0.04 -> 3*0.01=0.03, max(0.03, 2*0.03)=0.06,
    # max(0.06, 1*0.04)=0.06
    assert holm_adjust([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_holm_adjust_preserves_input_order() -> None:
    adjusted = holm_adjust([0.04, 0.01])
    assert adjusted == pytest.approx([0.04, 0.02])


def test_holm_adjust_caps_at_one() -> None:
    assert holm_adjust([0.5, 0.6]) == pytest.approx([1.0, 1.0])


def test_holm_adjust_of_empty_list() -> None:
    assert holm_adjust([]) == []


def test_reject_holm_uses_adjusted_threshold() -> None:
    assert reject_holm([0.01, 0.04, 0.03], 0.05) == [True, False, False]
    assert reject_holm([0.01, 0.04, 0.03], 0.07) == [True, True, True]


@pytest.mark.parametrize("p_values", [[-0.01], [1.01], [0.5, 1.2]])
def test_holm_rejects_invalid_p_values(p_values: list[float]) -> None:
    with pytest.raises(ValueError, match="p-values"):
        holm_adjust(p_values)


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.5, 2.0])
def test_reject_holm_rejects_invalid_alpha(alpha: float) -> None:
    with pytest.raises(ValueError, match="alpha"):
        reject_holm([0.01], alpha)
