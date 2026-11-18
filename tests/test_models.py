"""Tests for the affine and coverage curve models."""

from __future__ import annotations

import pytest

from rag_energy.stats.models import affine_fit, coverage_accuracy, coverage_fit


def test_affine_fit_recovers_a_line() -> None:
    fit = affine_fit([0, 1, 2, 4], [10.0, 12.0, 14.0, 18.0])
    assert fit.intercept == pytest.approx(10.0)
    assert fit.slope == pytest.approx(2.0)
    assert fit.r_squared == pytest.approx(1.0)


def test_coverage_accuracy_is_bounded() -> None:
    assert coverage_accuracy(0.3, 0.1, 0) == pytest.approx(0.3)
    assert 0.3 < coverage_accuracy(0.3, 0.1, 10) < 1.0


def test_coverage_fit_recovers_a_known_curve() -> None:
    xs = [0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
    ys = [coverage_accuracy(0.3, 0.1, int(k)) for k in xs]
    a0, p, r2 = coverage_fit(xs, ys)
    assert abs(a0 - 0.3) < 0.05
    assert abs(p - 0.1) < 0.02
    assert r2 > 0.99


def test_coverage_fit_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        coverage_fit([], [])
    with pytest.raises(ValueError):
        coverage_fit([0, 1], [0.1])
