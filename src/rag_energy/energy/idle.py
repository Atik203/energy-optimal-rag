"""Idle baseline estimation.

The pilot measured a 60 s pre-run idle baseline (15.56 W, CV 10.4%) and a 20 s
post-run baseline (17.63 W, CV 15.9%). Using the post-run value lowers every
energy by roughly 4% almost uniformly and changes E ratios by under 1%.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class IdleStats:
    mean_w: float
    sd_w: float
    cv: float
    n: int


def summarize_idle(samples_w: Sequence[float]) -> IdleStats:
    """Return mean, sample standard deviation, and coefficient of variation."""
    values = [float(v) for v in samples_w]
    n = len(values)
    if n < 2:
        raise ValueError("at least two idle samples are required")
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    sd = math.sqrt(variance)
    cv = sd / mean if mean > 0 else float("inf")
    return IdleStats(mean_w=mean, sd_w=sd, cv=cv, n=n)
