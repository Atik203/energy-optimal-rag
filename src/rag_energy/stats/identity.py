"""The optimal-depth identity.

At an interior optimum,

    k J'(k) / J(k) = k A'(k) / A(k).

For affine energy the left side is the variable energy share. The identity is
scale-free and is used as a diagnostic, not as proof of global optimality: it
cannot distinguish a local minimum from the global one (see the distractor
counterexample in docs/IMPLEMENTATION_PLAN.md).
"""

from __future__ import annotations


def elasticity(
    k: float, value: float, previous: float, following: float, step: float = 1.0
) -> float:
    """Central-difference elasticity ``k f'(k) / f(k)``.

    Args:
        k: Depth.
        value: ``f(k)``.
        previous: ``f(k - step)``.
        following: ``f(k + step)``.
        step: Grid step in depth.

    Returns:
        The elasticity. Returns ``inf`` when ``f(k) = 0``.
    """
    if step <= 0:
        raise ValueError("step must be positive")
    if value == 0:
        return float("inf")
    derivative = (following - previous) / (2.0 * step)
    return float(k) * derivative / float(value)


def identity_gap(energy_elasticity: float, accuracy_elasticity: float) -> float:
    """Return ``epsilon_J - epsilon_A``.

    The pilot measured +0.044 at k=2 (CI includes 0) and +0.700 at k=32
    (over-retrieval by the theory's own diagnostic).
    """
    return float(energy_elasticity) - float(accuracy_elasticity)
