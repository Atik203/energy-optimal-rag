"""Closed-form theory for the depth decision.

Pure, dependency-free implementations of the statements proved in
``paper/theory_appendix.tex``. Nothing here touches a GPU, a run directory, or a
data file, so the appendix's formulas can be unit-tested directly.

Symbols and units follow the manuscript: depth ``k`` is a count of passages,
``J(k) = a + bk`` is mean energy per query in joules (``a`` in J/query, ``b`` in
J per passage per query), ``A(k)`` is accuracy as a proportion in ``(0, 1]``,
``E(k) = J(k)/A(k)`` is energy per correct answer in J/correct, and ``c_cert`` is
the certification cost in joules.

The five public functions are:

* :func:`is_unimodal` -- the sufficient conditions of Proposition 1 on a grid.
* :func:`comparative_statics` -- Corollary 1, ``dk*/da > 0`` and ``dk*/db < 0``.
* :func:`n_star_exact` -- Proposition 3(a), the per-query break-even in queries.
* :func:`n_star_bias` -- the per-correct-answer break-even relative to the exact one.
* :func:`boundary_threshold` -- Corollary 2, the ``b/a`` threshold for ``k* = 0``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "ComparativeStatics",
    "boundary_threshold",
    "comparative_statics",
    "is_unimodal",
    "n_star_bias",
    "n_star_exact",
]


@dataclass(frozen=True)
class ComparativeStatics:
    """Local comparative statics at an interior optimum of ``E(k) = J(k)/A(k)``.

    Attributes:
        dk_da: ``dk*/da``, in passages per (J/query). Positive under ``A' > 0``
            and ``A'' < 0``: a larger fixed per-query cost pushes the optimum deeper.
        dk_db: ``dk*/db``, in passages per (J per passage per query). Negative at a
            stationary point under ``A'' < 0``: a larger per-passage cost pushes the
            optimum shallower.
        epsilon_a: ``k A'(k)/A(k)``, the accuracy elasticity at ``k*`` (dimensionless).
        curvature: ``F_k = -(a + bk) A''(k)``, the implicit-function denominator
            [J/passage]. Positive is the second-order condition for a minimum.
        signs_certified: True when ``A' > 0`` and ``A'' < 0``, i.e. when the signs
            ``dk*/da > 0`` and ``dk*/db < 0`` are guaranteed by Corollary 1.
    """

    dk_da: float
    dk_db: float
    epsilon_a: float
    curvature: float
    signs_certified: bool


def is_unimodal(
    depths: list[float] | tuple[float, ...],
    accuracies: list[float] | tuple[float, ...],
    *,
    tolerance: float = 1e-12,
) -> bool:
    """Whether Proposition 1 certifies ``E(k) = J(k)/A(k)`` unimodal on a grid.

    The proposition assumes ``A`` nondecreasing and concave. On a possibly
    irregular depth grid those two properties are checked as: every secant slope
    is non-negative, and the secant slopes are non-increasing. A flat accuracy
    segment is allowed because it leaves ``N(k) = b A(k) - (a + bk) A'(k) = b A(k)``
    positive and does not affect the conclusion; the strictly increasing case
    ``A' > 0`` used in the main text is a special case.

    Args:
        depths: Strictly increasing non-negative depths (passages).
        accuracies: Accuracy at each depth, each in ``(0, 1]``.
        tolerance: Absolute slack on the slope comparisons.

    Returns:
        True when the sufficient conditions hold, so ``E`` has at most one interior
        stationary point and is nonincreasing then nondecreasing. False means "not
        certified by Proposition 1", not "not unimodal": the conditions are
        sufficient, not necessary, and a convex or non-monotone curve returns False.
    """
    if len(depths) != len(accuracies):
        raise ValueError("depths and accuracies must have the same length")
    if len(depths) < 3:
        raise ValueError("at least three grid depths are required")
    if any(k < 0 for k in depths):
        raise ValueError("depths must be non-negative")
    if any(later <= earlier for earlier, later in zip(depths, depths[1:], strict=False)):
        raise ValueError("depths must be strictly increasing")
    if any(not 0.0 < value <= 1.0 for value in accuracies):
        raise ValueError("accuracies must lie in (0, 1]")

    slopes = [
        (accuracies[index + 1] - accuracies[index]) / (depths[index + 1] - depths[index])
        for index in range(len(depths) - 1)
    ]
    if any(slope < -tolerance for slope in slopes):
        return False
    return all(
        later <= earlier + tolerance for earlier, later in zip(slopes, slopes[1:], strict=False)
    )


def comparative_statics(
    *,
    a: float,
    b: float,
    k: float,
    accuracy: float,
    derivative: float,
    second_derivative: float,
) -> ComparativeStatics:
    """Corollary 1: ``dk*/da > 0`` and ``dk*/db < 0`` at an interior optimum.

    The implicit function ``F(k, a, b) = b A(k) - (a + bk) A'(k) = 0`` is the
    first-order condition of Proposition 1. Its partials are ``F_k = -(a + bk) A''``,
    ``F_a = -A'`` and ``F_b = A - k A'``, so

        ``dk*/da = -A' / ((a + bk) A'')`` and
        ``dk*/db = (A - k A') / ((a + bk) A'')``.

    At a stationary point ``A - k A' = A (1 - epsilon_A) = A a / (a + bk) > 0``
    because the identity forces ``epsilon_A = epsilon_J = bk/(a + bk) < 1``.

    Args:
        a: Fixed cost per query [J/query], positive.
        b: Marginal cost per passage [J per passage per query], positive.
        k: The interior optimum [passages]; must satisfy the first-order condition.
        accuracy: ``A(k)`` in ``(0, 1]``.
        derivative: ``A'(k)`` [1/passage].
        second_derivative: ``A''(k)`` [1/passage^2]; nonzero.

    Returns:
        A :class:`ComparativeStatics` with both derivatives and the elasticity.

    Raises:
        ValueError: If a parameter is out of range or ``A''(k) == 0``, in which case
            the implicit-function theorem does not apply to this parametrization.
    """
    if a <= 0:
        raise ValueError("a must be positive")
    if b <= 0:
        raise ValueError("b must be positive")
    if k < 0:
        raise ValueError("k must be non-negative")
    if not 0.0 < accuracy <= 1.0:
        raise ValueError("accuracy must lie in (0, 1]")
    if second_derivative == 0:
        raise ValueError("A''(k) must be nonzero for the implicit-function step")

    j = a + b * k
    curvature = -j * second_derivative
    return ComparativeStatics(
        dk_da=-derivative / (j * second_derivative),
        dk_db=(accuracy - k * derivative) / (j * second_derivative),
        epsilon_a=k * derivative / accuracy,
        curvature=curvature,
        signs_certified=derivative > 0.0 and second_derivative < 0.0,
    )


def n_star_exact(c_cert: float, j_reference: float, j_selected: float) -> float:
    """Proposition 3(a): per-query energy break-even ``N* = C/(J(k0) - J(k*))``.

    Args:
        c_cert: One-off certification cost [J], non-negative.
        j_reference: ``J(k0)`` [J/query].
        j_selected: ``J(k*)`` [J/query].

    Returns:
        Break-even volume in queries. Infinite when the candidate is not cheaper,
        which is reported as an error rather than as ``inf`` so a caller cannot
        silently divide by zero downstream.

    Raises:
        ValueError: If ``c_cert < 0`` or ``J(k0) <= J(k*)``, i.e. no positive
            break-even exists.
    """
    if not math.isfinite(c_cert) or c_cert < 0:
        raise ValueError("c_cert must be finite and non-negative")
    delta = j_reference - j_selected
    if not math.isfinite(delta) or delta <= 0:
        raise ValueError("no positive break-even: the reference is not more expensive")
    return c_cert / delta


def n_star_bias(
    j_reference: float,
    j_selected: float,
    accuracy_reference: float,
    accuracy_selected: float,
) -> float:
    """Ratio of the per-correct-answer break-even to the exact per-query one.

    The paper's formula is ``N*_A = C / (A(k*)[E(k0) - E(k*)])``. With
    ``E = J/A`` its denominator is ``(A(k*)/A(k0)) J(k0) - J(k*)``, so

        ``N*_A / N*_J = (J(k0) - J(k*)) / ((A(k*)/A(k0)) J(k0) - J(k*))``,

    which equals one iff ``A(k*) = A(k0)``. The ratio exceeds one when the
    candidate is less accurate than the reference, in which case the
    per-correct-answer formula reports the longer break-even (it is the break-even
    in candidate-depth queries at the candidate's correct-answer rate, not in
    deployment queries at unchanged accuracy).

    Args:
        j_reference: ``J(k0)`` [J/query].
        j_selected: ``J(k*)`` [J/query].
        accuracy_reference: ``A(k0)`` in ``(0, 1]``.
        accuracy_selected: ``A(k*)`` in ``(0, 1]``.

    Returns:
        The dimensionless bias factor ``>= 0``; one means the two formulas agree.

    Raises:
        ValueError: If an accuracy is out of range, if ``J(k0) <= J(k*)``, or if
            the per-correct-answer denominator is non-positive (no break-even).
    """
    if not 0.0 < accuracy_reference <= 1.0:
        raise ValueError("accuracy_reference must lie in (0, 1]")
    if not 0.0 < accuracy_selected <= 1.0:
        raise ValueError("accuracy_selected must lie in (0, 1]")
    delta_j = j_reference - j_selected
    if not math.isfinite(delta_j) or delta_j <= 0:
        raise ValueError("no positive break-even: the reference is not more expensive")
    denominator = accuracy_selected * j_reference / accuracy_reference - j_selected
    if denominator <= 0:
        raise ValueError("per-correct-answer break-even is not positive")
    return delta_j / denominator


def boundary_threshold(a0: float, p: float) -> float:
    """Corollary 2: the ``b/a`` threshold above which the coverage optimum is zero.

    For ``A(k) = 1 - (1 - a0)(1 - p)^k`` the accuracy derivative at zero is
    ``A'(0) = (1 - a0)(-ln(1 - p))``, so ``E`` is nondecreasing -- and ``k* = 0`` --
    iff ``b/a >= (1 - a0)(-ln(1 - p))/a0``.

    Args:
        a0: ``A(0)``, the no-retrieval accuracy, in ``(0, 1)``.
        p: Per-passage coverage probability in ``(0, 1)``.

    Returns:
        The threshold in inverse passages, dimensionless when depth counts passages.
        Compare it against ``b/a`` (1/passage).
    """
    if not 0.0 < a0 < 1.0:
        raise ValueError("a0 must lie in (0, 1)")
    if not 0.0 < p < 1.0:
        raise ValueError("p must lie in (0, 1)")
    return (1.0 - a0) * (-math.log(1.0 - p)) / a0
