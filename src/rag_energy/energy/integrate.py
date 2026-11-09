"""Trapezoidal power integration.

Energy in joules is the integral of power in watts over time in seconds. The
sampler timestamps are monotonic seconds; samples must be sorted by time.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def trapezoid_joules(samples: Iterable[tuple[float, float]]) -> float:
    """Integrate ``(t_s, power_w)`` samples with the trapezoidal rule.

    Args:
        samples: Iterable of ``(timestamp_s, power_w)`` pairs.

    Returns:
        Joules. Returns 0.0 for fewer than two samples.
    """
    points: Sequence[tuple[float, float]] = list(samples)
    if len(points) < 2:
        return 0.0
    total = 0.0
    for (t0, p0), (t1, p1) in zip(points, points[1:], strict=False):
        dt = float(t1) - float(t0)
        if dt < 0:
            raise ValueError("timestamps must be non-decreasing")
        total += 0.5 * (float(p0) + float(p1)) * dt
    return total


def idle_subtract(gross_j: float, duration_s: float, idle_power_w: float) -> float:
    """Subtract the idle baseline from a gross energy integral."""
    if duration_s < 0:
        raise ValueError("duration_s must be non-negative")
    return max(0.0, float(gross_j) - float(idle_power_w) * float(duration_s))


def mean_power(gross_j: float, duration_s: float) -> float:
    """Average power over a window, in watts."""
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    return float(gross_j) / float(duration_s)
