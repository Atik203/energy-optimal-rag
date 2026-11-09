"""Curve models: affine energy and noisy-coverage accuracy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AffineFit:
    slope: float
    intercept: float
    r_squared: float


def affine_fit(xs: list[float], ys: list[float]) -> AffineFit:
    """Ordinary least squares fit ``y = intercept + slope * x``.

    The pilot fit ``J(k) = 15.74 + 2.283k`` J with ``R^2 = 0.9990``.
    """
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have the same length")
    n = len(xs)
    if n < 2:
        raise ValueError("at least two points are required")
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("xs must not be constant")
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys, strict=False))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return AffineFit(slope=slope, intercept=intercept, r_squared=r_squared)


def coverage_accuracy(a0: float, p: float, k: int) -> float:
    """Stylized coverage model ``A(k) = 1 - (1 - A0)(1 - p)^k``.

    The pilot fit this poorly (R^2 = 0.332), which is why the empirical curve and
    the monotonicity test, not the model, are the falsification.
    """
    if not 0.0 <= a0 < 1.0:
        raise ValueError("a0 must lie in [0, 1)")
    if not 0.0 < p <= 1.0:
        raise ValueError("p must lie in (0, 1]")
    if k < 0:
        raise ValueError("k must be non-negative")
    return 1.0 - (1.0 - a0) * (1.0 - p) ** k


def coverage_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Fit the coverage model and return ``(a0, p, r_squared)``.

    Implemented in P4 with a constrained grid/least-squares search. The affine
    energy fit is the only model required for P1.
    """
    raise NotImplementedError("coverage_fit is implemented in P4.")
