"""Block energy calibration.

Per-query windows miss the approximately 100 ms power ramp, most severely at
short depths. The pilot therefore integrated 20 back-to-back queries per depth
as a block and scaled the per-query integrals to the block total. Scale factors
were 1.041 (k=0), 1.100 (1), 1.188 (2), 1.128 (4), 1.118 (8), 1.081 (16),
1.073 (32).
"""

from __future__ import annotations

from collections.abc import Sequence


def block_scale_factors(
    per_query_j: Sequence[float],
    block_total_j: float,
) -> list[float]:
    """Scale per-query integrals so they sum to the calibrated block total.

    Args:
        per_query_j: Raw per-query integrals for the block, in joules.
        block_total_j: Idle-subtracted block energy, in joules.

    Returns:
        A scale factor per query. All factors are equal when the raw sum is
        positive; the function preserves the per-query shape.
    """
    values = [float(v) for v in per_query_j]
    if not values:
        raise ValueError("per_query_j must be non-empty")
    if any(v < 0 for v in values):
        raise ValueError("per-query energy must be non-negative")
    if block_total_j <= 0:
        raise ValueError("block_total_j must be positive")

    raw_total = sum(values)
    if raw_total <= 0:
        raise ValueError("raw per-query energy sum must be positive")
    factor = float(block_total_j) / raw_total
    return [factor for _ in values]


def calibrated_energy(per_query_j: Sequence[float], factor: float) -> list[float]:
    """Apply one scale factor to a vector of per-query energies."""
    if factor <= 0:
        raise ValueError("factor must be positive")
    return [float(v) * float(factor) for v in per_query_j]
