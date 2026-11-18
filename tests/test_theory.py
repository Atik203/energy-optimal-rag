"""Tests for the closed-form theory in ``paper/theory_appendix.tex``."""

from __future__ import annotations

import math

import pytest

from rag_energy.stats.theory import (
    boundary_threshold,
    comparative_statics,
    is_unimodal,
    n_star_bias,
    n_star_exact,
)

# Registered P1 outputs (analysis/squad_qwen4b_p1 and analysis/identity_continuous.json).
P1_A = 24.0759199777782  # J/query
P1_B = 2.2771527658659148  # J per passage per query
P1_J4 = 36.253738493  # J/query at k=4
P1_J32 = 94.945020552  # J/query at k=32
P1_A4 = 0.450
P1_A32 = 0.493
P1_C_CERT = 311992.064094  # J, total sweep energy

# P1 accuracy at the seven grid depths (Table p1desc).
P1_DEPTHS = (0, 1, 2, 4, 8, 16, 32)
P1_ACCURACY = (0.001, 0.391, 0.417, 0.450, 0.467, 0.481, 0.493)


def _concave_accuracy(lam: float, k: float) -> tuple[float, float, float]:
    """``A = 1 - exp(-lam k)`` with its first two derivatives."""
    decay = math.exp(-lam * k)
    return 1.0 - decay, lam * decay, -(lam**2) * decay


def _optimum(a: float, b: float, lam: float) -> float:
    """Bisect ``N(k) = b A - (a + bk) A' = 0`` for the concave example."""

    def n_of_k(k: float) -> float:
        accuracy, derivative, _ = _concave_accuracy(lam, k)
        return b * accuracy - (a + b * k) * derivative

    low, high = 0.0, 1.0
    while n_of_k(high) < 0.0:
        high *= 2.0
    for _ in range(200):
        mid = 0.5 * (low + high)
        if n_of_k(mid) < 0.0:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def test_boundary_threshold_closed_form() -> None:
    # (1 - 0.31)(-ln 0.985)/0.31, the P4 coverage parameterisation.
    assert boundary_threshold(0.31, 0.015) == pytest.approx(0.03364003254494596, rel=1e-12)
    # The threshold is increasing in p and decreasing in a0.
    assert boundary_threshold(0.31, 0.03) > boundary_threshold(0.31, 0.015)
    assert boundary_threshold(0.5, 0.015) < boundary_threshold(0.31, 0.015)
    with pytest.raises(ValueError):
        boundary_threshold(0.0, 0.015)
    with pytest.raises(ValueError):
        boundary_threshold(0.31, 0.0)
    with pytest.raises(ValueError):
        boundary_threshold(0.31, 1.0)


@pytest.mark.parametrize("a0,p", [(0.31, 0.015), (0.10, 0.073), (0.34, 0.008)])
def test_boundary_threshold_separates_zero_and_interior_optima(a0: float, p: float) -> None:
    """Corollary 2: ``k* = 0`` iff ``b/a >= threshold`` on the coverage family."""
    threshold = boundary_threshold(a0, p)
    a = 24.0
    depths = [index * 0.01 for index in range(0, 3201)]

    def energy(b: float, k: float) -> float:
        accuracy = 1.0 - (1.0 - a0) * (1.0 - p) ** k
        return (a + b * k) / accuracy

    # At the threshold the curve is nondecreasing, so the minimiser is k = 0.
    at = [energy(threshold * a, k) for k in depths]
    assert at[0] == pytest.approx(min(at), rel=1e-9)
    # Just below it the minimiser moves into the interior.
    below = threshold * a * 0.9
    assert min(range(len(depths)), key=lambda i: energy(below, depths[i])) > 0


def test_n_star_exact_p1_break_even() -> None:
    n_star = n_star_exact(P1_C_CERT, P1_J32, P1_J4)
    assert n_star == pytest.approx(5315.816133993577, rel=1e-9)


def test_n_star_exact_is_linear_in_certification_cost() -> None:
    base = n_star_exact(1.0, 10.0, 4.0)
    assert base == pytest.approx(1.0 / 6.0)
    assert n_star_exact(3.0, 10.0, 4.0) == pytest.approx(3.0 * base)


def test_n_star_exact_rejects_a_non_cheaper_candidate() -> None:
    with pytest.raises(ValueError):
        n_star_exact(100.0, 10.0, 10.0)
    with pytest.raises(ValueError):
        n_star_exact(100.0, 10.0, 12.0)
    with pytest.raises(ValueError):
        n_star_exact(-1.0, 10.0, 4.0)


def test_n_star_bias_is_one_at_equal_accuracy() -> None:
    assert n_star_bias(10.0, 4.0, 0.5, 0.5) == pytest.approx(1.0)
    # Then the per-correct-answer break-even equals the per-query one.
    assert n_star_bias(10.0, 4.0, 0.5, 0.5) * n_star_exact(100.0, 10.0, 4.0) == pytest.approx(
        n_star_exact(100.0, 10.0, 4.0)
    )


def test_n_star_bias_p1_contrast() -> None:
    bias = n_star_bias(P1_J32, P1_J4, P1_A32, P1_A4)
    assert bias == pytest.approx(1.1642768624508222, rel=1e-9)
    # The paper's per-correct-answer break-even is the exact one times the bias.
    assert bias * n_star_exact(P1_C_CERT, P1_J32, P1_J4) == pytest.approx(6189.0817298515, rel=1e-9)


def test_n_star_bias_direction_depends_on_accuracy() -> None:
    # A less accurate candidate reports a longer per-correct-answer break-even.
    assert n_star_bias(10.0, 4.0, 0.50, 0.45) > 1.0
    # A more accurate candidate reports a shorter one.
    assert n_star_bias(10.0, 4.0, 0.40, 0.45) < 1.0


def test_n_star_bias_rejects_degenerate_inputs() -> None:
    with pytest.raises(ValueError):
        n_star_bias(10.0, 10.0, 0.5, 0.45)
    with pytest.raises(ValueError):
        n_star_bias(10.0, 4.0, 0.0, 0.45)
    with pytest.raises(ValueError):
        n_star_bias(10.0, 4.0, 0.5, 1.5)
    # A denominator that is non-positive has no break-even.
    with pytest.raises(ValueError):
        n_star_bias(10.0, 1.0, 1.0, 0.05)


@pytest.mark.parametrize(
    ("a", "b", "lam"), [(20.0, 2.0, 0.5), (24.0759, 2.2772, 1.0), (5.0, 3.0, 0.2)]
)
def test_comparative_statics_matches_finite_differences(a: float, b: float, lam: float) -> None:
    k_star = _optimum(a, b, lam)
    accuracy, derivative, second = _concave_accuracy(lam, k_star)
    statics = comparative_statics(
        a=a, b=b, k=k_star, accuracy=accuracy, derivative=derivative, second_derivative=second
    )

    step = 1e-4
    dk_da = (_optimum(a + step, b, lam) - _optimum(a - step, b, lam)) / (2.0 * step)
    dk_db = (_optimum(a, b + step, lam) - _optimum(a, b - step, lam)) / (2.0 * step)

    assert statics.dk_da == pytest.approx(dk_da, rel=1e-6)
    assert statics.dk_db == pytest.approx(dk_db, rel=1e-6)
    # At the optimum the identity forces epsilon_A = epsilon_J < 1.
    assert statics.epsilon_a == pytest.approx(b * k_star / (a + b * k_star), rel=1e-9)
    assert statics.epsilon_a < 1.0
    assert statics.signs_certified is True
    assert statics.curvature > 0.0


def test_comparative_statics_signs() -> None:
    lam, a, b = 0.5, 20.0, 2.0
    k_star = _optimum(a, b, lam)
    accuracy, derivative, second = _concave_accuracy(lam, k_star)
    statics = comparative_statics(
        a=a, b=b, k=k_star, accuracy=accuracy, derivative=derivative, second_derivative=second
    )
    assert statics.dk_da > 0.0
    assert statics.dk_db < 0.0


def test_comparative_statics_requires_curvature_and_positive_costs() -> None:
    with pytest.raises(ValueError):
        comparative_statics(
            a=20.0, b=2.0, k=2.0, accuracy=0.4, derivative=0.1, second_derivative=0.0
        )
    with pytest.raises(ValueError):
        comparative_statics(
            a=0.0, b=2.0, k=2.0, accuracy=0.4, derivative=0.1, second_derivative=-0.01
        )
    with pytest.raises(ValueError):
        comparative_statics(
            a=20.0, b=0.0, k=2.0, accuracy=0.4, derivative=0.1, second_derivative=-0.01
        )


def test_is_unimodal_accepts_the_p1_curve() -> None:
    assert is_unimodal(P1_DEPTHS, P1_ACCURACY) is True


def test_is_unimodal_rejects_the_non_monotone_arms() -> None:
    # Qwen2.5-1.5B and Llama 3.2 3B are non-monotone on P2 (docs/P4_RESULTS.md).
    qwen = (0.001, 0.300, 0.340, 0.360, 0.355, 0.350, 0.340)
    assert is_unimodal(P1_DEPTHS, qwen) is False


def test_is_unimodal_rejects_a_convex_accuracy_curve() -> None:
    convex = (0.10, 0.12, 0.18, 0.34, 0.66, 0.90, 0.99)
    assert is_unimodal(P1_DEPTHS, convex) is False


def test_is_unimodal_accepts_a_flat_shoulder() -> None:
    flat = (0.30, 0.42, 0.46, 0.48, 0.48, 0.48, 0.48)
    assert is_unimodal(P1_DEPTHS, flat) is True


def test_is_unimodal_validates_the_grid() -> None:
    with pytest.raises(ValueError):
        is_unimodal((0, 1, 2), (0.1, 0.2))
    with pytest.raises(ValueError):
        is_unimodal((0, 1), (0.1, 0.2))
    with pytest.raises(ValueError):
        is_unimodal((0, 2, 1), (0.1, 0.2, 0.3))
    with pytest.raises(ValueError):
        is_unimodal((0, 1, 2), (0.0, 0.2, 0.3))
    with pytest.raises(ValueError):
        is_unimodal((0, 1, 2), (0.1, 0.2, 1.3))
