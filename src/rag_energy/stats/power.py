"""Power for the 5 pp non-inferiority test.

The pilot's minimum detectable effect was roughly 4-5 pp at n=200, which is why
a 2 pp margin could not be certified. At n=1000 and a discordant-pair rate near
0.145, the standard error of the paired difference is about 1.2 pp; a 5 pp
one-sided non-inferiority test is well powered when the true difference is small,
and a 2 pp margin remains estimation-only.
"""

from __future__ import annotations

import math
from statistics import NormalDist


def paired_difference_se(discordant_rate: float, n: int) -> float:
    """Approximate SE of a paired accuracy difference.

    For paired binary outcomes, ``Var(diff) = (p_b + p_c - (p_b - p_c)^2) / n``.
    With a discordant rate ``d = p_b + p_c`` and a small true difference, the
    variance is approximately ``d / n``.
    """
    if not 0.0 <= discordant_rate <= 1.0:
        raise ValueError("discordant_rate must lie in [0, 1]")
    if n <= 0:
        raise ValueError("n must be positive")
    return math.sqrt(discordant_rate / n)


def noninferiority_power(
    n: int,
    true_difference: float,
    margin: float,
    sd_difference: float,
    alpha: float = 0.05,
) -> float:
    """Power of a one-sided non-inferiority test.

    Args:
        n: Number of paired questions.
        true_difference: True accuracy difference (candidate - reference).
            Negative means the candidate is worse.
        margin: Non-inferiority margin as a positive proportion (0.05 = 5 pp).
        sd_difference: Standard deviation of the paired difference.
        alpha: One-sided type-I rate.

    Returns:
        Power in ``[0, 1]``.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if margin <= 0:
        raise ValueError("margin must be positive")
    if sd_difference <= 0:
        raise ValueError("sd_difference must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")

    se = sd_difference / math.sqrt(n)
    z_alpha = NormalDist().inv_cdf(1.0 - alpha)
    return NormalDist().cdf((margin - true_difference) / se - z_alpha)


def minimum_detectable_effect(
    n: int,
    sd_difference: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """Smallest one-sided detectable difference at the given power."""
    if n <= 0:
        raise ValueError("n must be positive")
    if sd_difference <= 0:
        raise ValueError("sd_difference must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    if not 0.5 < power < 1.0:
        raise ValueError("power must lie in (0.5, 1)")
    z_alpha = NormalDist().inv_cdf(1.0 - alpha)
    z_power = NormalDist().inv_cdf(power)
    return (z_alpha + z_power) * sd_difference / math.sqrt(n)
