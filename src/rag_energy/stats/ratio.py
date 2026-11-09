"""The ratio estimand E(k) = E[J_k] / E[C_k].

The primary estimand is a ratio of expectations, not the mean of per-query
ratios. A ratio can be gamed by failing cheaply, so every reported E(k) is
reported with its accuracy A(k) and the correctness gate A_min.

Standard library only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def ratio_of_expectations(joules: Sequence[float], correct: Sequence[int]) -> float:
    """Return ``sum(joules) / sum(correct)``, i.e. joules per correct answer.

    Returns ``inf`` when no answer is correct. That is a real outcome, not an
    error: it means the depth has no usable accuracy on this sample.
    """
    if len(joules) != len(correct):
        raise ValueError("joules and correct must have the same length")
    if not joules:
        raise ValueError("at least one observation is required")
    if any(j < 0 for j in joules):
        raise ValueError("energy must be non-negative")
    if any(c not in (0, 1) for c in correct):
        raise ValueError("correct must contain 0/1 values")
    denominator = sum(correct)
    if denominator == 0:
        return math.inf
    return sum(float(j) for j in joules) / denominator


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _sample_variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return sum((v - mean) ** 2 for v in values) / (len(values) - 1)


def delta_method_variance(joules: Sequence[float], correct: Sequence[int]) -> float:
    """Per-observation delta-method variance of the ratio estimator.

    This is ``sigma_k^2`` in Theorem 3:

        Var(J)/A^2 + J^2 Var(C)/A^4 - 2 J Cov(J, C)/A^3

    Returns ``inf`` when ``A = 0``.
    """
    if len(joules) != len(correct):
        raise ValueError("joules and correct must have the same length")
    n = len(joules)
    if n < 2:
        raise ValueError("at least two observations are required")
    j = [float(x) for x in joules]
    c = [float(x) for x in correct]
    mean_j, mean_c = _mean(j), _mean(c)
    if mean_c == 0:
        return math.inf
    var_j = _sample_variance(j)
    var_c = _sample_variance(c)
    cov = sum((a - mean_j) * (b - mean_c) for a, b in zip(j, c, strict=False)) / (n - 1)
    return var_j / mean_c**2 + mean_j**2 * var_c / mean_c**4 - 2.0 * mean_j * cov / mean_c**3


def ratio_standard_error(joules: Sequence[float], correct: Sequence[int]) -> float:
    """Standard error of ``E_hat`` from the delta method."""
    variance = delta_method_variance(joules, correct)
    if math.isinf(variance):
        return math.inf
    return math.sqrt(max(variance, 0.0) / len(joules))


def energy_savings_pct(e_reference: float, e_candidate: float) -> float:
    """Percent energy saved by ``e_candidate`` relative to ``e_reference``."""
    if e_reference <= 0 or math.isinf(e_reference):
        raise ValueError("e_reference must be finite and positive")
    return 100.0 * (1.0 - float(e_candidate) / float(e_reference))
