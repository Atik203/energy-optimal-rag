"""Multiplicity control.

The design has exactly one primary test (5 pp non-inferiority). Every other
test is exploratory and must be labeled as such. If a secondary family is ever
promoted to confirmatory, Holm's step-down procedure is the default.
"""

from __future__ import annotations


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, preserving input order."""
    if not p_values:
        return []
    if any(not 0.0 <= p <= 1.0 for p in p_values):
        raise ValueError("p-values must lie in [0, 1]")

    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [1.0] * m
    running_max = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * p_values[index])
        running_max = max(running_max, candidate)
        adjusted[index] = running_max
    return adjusted


def reject_holm(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm rejections at family-wise ``alpha``."""
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    return [p <= alpha for p in holm_adjust(p_values)]
