"""Exploratory inference layer for the paired P1 design.

Claim boundary
--------------
``prereg-freeze-v1`` defines exactly one confirmatory test: the one-sided 5 pp
non-inferiority test of ``A(4) - A(32)`` together with the 20% savings floor.
Everything in this module is **secondary, exploratory or sensitivity** work.
Nothing here can promote the preregistered P1 verdict, certify a margin that
failed, or create a new ``k*``. The preregistered verdict is copied into the
output unchanged and is never recomputed into a different claim.

What is implemented
-------------------
* :func:`ni_score_test` - restricted-maximum-likelihood score test for the
  paired binary non-inferiority null ``p_b - p_c <= -margin``.
* :func:`ni_exact_sensitivity` - exact conditional and exact unconditional
  (maximised over the nuisance discordance) p-values.
* :func:`tost` - two one-sided tests for equivalence at ``+/- margin``.
* :func:`realized_power`, :func:`required_n`, :func:`mde` - design precision
  for a one-sided paired non-inferiority test at the observed discordance.
* :func:`bca_interval` and the :func:`bca_mean_difference` and
  :func:`bca_savings` wrappers - bias-corrected and accelerated bootstrap
  intervals.
* :func:`joint_question_bootstrap` - one question resample, joint
  recomputation of ``A(k)``, ``E(k)``, savings, selection and the NI decision.
* :func:`cluster_bootstrap` - the same quantity with clusters resampled when a
  ``context_id`` column is present (the P1 CSV has none; the function reports
  that instead of inventing a clustering).
* :func:`build_inference_payload` - assembles the exploratory payload for one
  registered run.

Formulas
--------
Paired binary differences ``d_i = C_i4 - C_i32`` take values in {-1, 0, +1}.
With ``b`` discordant pairs where the candidate is right and ``c`` where the
reference is right, ``n`` pairs, ``m = b + c`` and ``D = b - c``:

* ``E[d] = D / n`` and ``Var(d_i) = pi_d - E[d]^2`` where ``pi_d = m / n`` is
  the discordance. This identity is exact, not an approximation.
* Pearson variance of the estimator: ``sigma^2 / n``.
* One-sided power: ``Phi((d + margin) / (sigma / sqrt(n)) - z_{1-alpha})``.

Score test. Under ``H0: p_b - p_c = -margin`` the restricted multinomial MLE
satisfies ``p_b + p_c = pi`` with ``pi`` the feasible root of

    ``n pi^2 - (m - margin * D) pi - margin * (D + a * margin) = 0``,

where ``a = n - b - c``. Writing ``p_b = (pi - margin) / 2`` and
``p_c = (pi + margin) / 2``, the efficient score for ``psi = p_b - p_c`` is

    ``U_psi = (pi D + margin * m) / (pi^2 - margin^2)``

and the efficient information (profiling out ``pi``) is

    ``I_eff = I_psi - I_cross^2 / I_pi``

with ``K = n / (pi^2 - margin^2)``, ``I_psi = K pi``, ``I_cross = K margin``
and ``I_pi = I_psi + n / (1 - pi)``. The score statistic is
``z = U_psi / sqrt(I_eff)``. At ``margin = 0`` this reduces exactly to
``D / sqrt(m)``, the McNemar z without continuity correction.

The module is pure Python plus numpy/scipy and never touches a GPU.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from scipy import optimize
from scipy import stats as scipy_stats

from rag_energy.stats.p1 import (
    DEFAULT_SEED,
    _correct,
    _depth_matrices,
    _percentile_interval,
    noninferiority,
    paired_questions,
)

__all__ = [
    "bca_interval",
    "bca_mean_difference",
    "bca_savings",
    "build_inference_payload",
    "cluster_bootstrap",
    "joint_question_bootstrap",
    "mde",
    "ni_exact_sensitivity",
    "ni_score_test",
    "paired_difference_sd",
    "realized_power",
    "required_n",
    "tost",
]

CLAIM_BOUNDARY = (
    "Exploratory/sensitivity only. The preregistered 5 pp non-inferiority test is the "
    "single confirmatory test and its verdict is unchanged. Nothing here certifies a "
    "margin, creates a new k*, or supports a universal depth."
)


# ---------------------------------------------------------------------------
# Paired binary helpers
# ---------------------------------------------------------------------------


def _binary_pair_arrays(
    candidate_correct: Sequence[int],
    reference_correct: Sequence[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Validate and coerce paired 0/1 correctness vectors."""
    candidate = np.asarray(candidate_correct, dtype=float)
    reference = np.asarray(reference_correct, dtype=float)
    if candidate.shape != reference.shape:
        raise ValueError("candidate and reference must have the same length")
    if candidate.ndim != 1:
        raise ValueError("correctness values must be one-dimensional")
    if candidate.size == 0:
        raise ValueError("at least one pair is required")
    for values in (candidate, reference):
        if not np.isin(values, (0.0, 1.0)).all():
            raise ValueError("correctness values must be 0/1")
    return candidate, reference


def _discordant_counts(candidate: np.ndarray, reference: np.ndarray) -> tuple[int, int, int]:
    """Return ``(b, c, n)`` for paired binary vectors."""
    b_count = int(np.sum(candidate > reference))
    c_count = int(np.sum(candidate < reference))
    return b_count, c_count, int(candidate.size)


def _restricted_mle(b: int, c: int, n: int, margin: float) -> tuple[float, float, float, bool]:
    """Restricted MLE of ``(p_b, p_c)`` under ``p_b - p_c = -margin``.

    The nuisance ``pi = p_b + p_c`` solves the quadratic in the module
    docstring. ``boundary`` is True when the feasible maximum sits on the edge
    of the parameter space rather than at the interior root.
    """
    a = n - b - c
    m = b + c
    d = b - c
    linear = m - margin * d
    constant = -margin * (d + a * margin)
    discriminant = linear * linear - 4.0 * n * constant
    boundary = False
    if discriminant < 0.0:
        # No interior stationary point: the profile maximum is on the boundary.
        pi = max(margin, 1e-12)
        boundary = True
    else:
        pi = (linear + math.sqrt(discriminant)) / (2.0 * n)
        if pi < margin:
            pi = margin
            boundary = True
        if pi >= 1.0:
            pi = 1.0 - 1e-12
            boundary = True
    p_b = (pi - margin) / 2.0
    p_c = (pi + margin) / 2.0
    return pi, p_b, p_c, boundary


def ni_score_test(
    candidate_correct: Sequence[int],
    reference_correct: Sequence[int],
    *,
    margin: float = 0.05,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Restricted-MLE score test for paired binary non-inferiority.

    The null is ``p_b - p_c <= -margin`` and the alternative is
    ``p_b - p_c > -margin``, where ``p_b`` is the probability that only the
    candidate is correct and ``p_c`` the probability that only the reference
    is correct. The nuisance discordance ``p_b + p_c`` is profiled out at its
    restricted MLE, so the test does not condition the variance on the
    observed difference.

    Args:
        candidate_correct: Paired 0/1 correctness for the shallow depth.
        reference_correct: Paired 0/1 correctness for the reference depth.
        margin: Non-inferiority margin as a positive proportion (0.05 = 5 pp).
        alpha: One-sided type-I rate.

    Returns:
        A JSON-safe dictionary with the counts, the restricted MLE, the
        efficient score, the z statistic, the one-sided p-value and the
        decision.
    """
    if margin < 0.0:
        raise ValueError("margin must be non-negative")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    candidate, reference = _binary_pair_arrays(candidate_correct, reference_correct)
    b_count, c_count, n_pairs = _discordant_counts(candidate, reference)
    diff = candidate - reference
    mean_diff = float(diff.mean())
    discordance = (b_count + c_count) / n_pairs
    pi, p_b, p_c, boundary = _restricted_mle(b_count, c_count, n_pairs, margin)

    payload: dict[str, Any] = {
        "method": "restricted-MLE score test (paired binary, one-sided)",
        "margin": float(margin),
        "alpha": float(alpha),
        "n_pairs": n_pairs,
        "b": b_count,
        "c": c_count,
        "discordance": float(discordance),
        "mean_diff": mean_diff,
        "restricted_discordance": float(pi),
        "restricted_p_candidate_only": float(p_b),
        "restricted_p_reference_only": float(p_c),
        "boundary_mle": bool(boundary),
        "score": None,
        "efficient_information": None,
        "z": None,
        "p_value": None,
        "non_inferior": None,
        "note": None,
    }

    if b_count == 0 and c_count == 0:
        payload["note"] = (
            "No discordant pairs: the paired comparison carries no information and the "
            "score statistic is undefined."
        )
        return payload

    if b_count == 0 or c_count == 0:
        # One discordant cell is empty, so the restricted profile sits on the
        # boundary p_b = 0 or p_c = 0. Report the limiting one-sided answer.
        z_limit = float("-inf") if b_count == 0 else float("inf")
        p_limit = 1.0 if b_count == 0 else 0.0
        payload.update(
            {
                "z": z_limit,
                "p_value": p_limit,
                "non_inferior": bool(p_limit <= alpha),
                "boundary_mle": True,
                "note": (
                    "A single discordant cell is non-empty, so the restricted profile is "
                    "on the boundary; the reported z is the limiting value."
                ),
            }
        )
        return payload

    variance_term = pi * pi - margin * margin
    if variance_term <= 0.0:
        payload["note"] = "Degenerate restricted MLE: pi^2 <= margin^2."
        return payload

    scale = n_pairs / variance_term
    info_psi = scale * pi
    info_cross = scale * margin
    info_nuisance = info_psi + n_pairs / (1.0 - pi)
    if info_nuisance <= 0.0:
        payload["note"] = "Degenerate efficient information."
        return payload
    efficient_information = info_psi - info_cross * info_cross / info_nuisance
    if efficient_information <= 0.0:
        payload["note"] = "Degenerate efficient information."
        return payload

    score = (pi * (b_count - c_count) + margin * (b_count + c_count)) / variance_term
    z_stat = score / math.sqrt(efficient_information)
    p_value = float(scipy_stats.norm.sf(z_stat))
    payload.update(
        {
            "score": float(score),
            "efficient_information": float(efficient_information),
            "z": float(z_stat),
            "p_value": p_value,
            "non_inferior": bool(p_value <= alpha),
        }
    )
    return payload


def _exact_unconditional_p(
    b: int,
    c: int,
    n: int,
    margin: float,
    *,
    grid: int,
    refine: bool,
) -> tuple[float, float]:
    """Exact unconditional p-value maximised over the nuisance discordance.

    Conditioning on ``m = b + c`` discordant pairs, ``b ~ Binomial(m, theta)``
    with ``theta = (pi - margin) / (2 pi)`` and ``m ~ Binomial(n, pi)``. The
    ordering statistic is the observed difference ``D = b - c``; large ``D``
    is evidence against ``H0: p_b - p_c <= -margin``. The p-value is

        ``sup_{pi in [margin, 1]} P(D >= D_obs; pi)``,

    which is the Berger-Boos exact unconditional construction.
    """
    observed = b - c
    m_counts = np.arange(n + 1)
    m_float = m_counts.astype(float)
    required = np.ceil((observed + m_float) / 2.0).astype(int)

    def tail_probability(prediscordance: float) -> float:
        pi = float(prediscordance)
        theta = (pi - margin) / (2.0 * pi) if pi > 0.0 else 0.0
        log_mass = scipy_stats.binom.logpmf(m_counts, n, pi)
        tail = scipy_stats.binom.sf(required - 1, m_counts, theta)
        return float(np.sum(np.exp(log_mass) * tail))

    points = np.linspace(max(margin, 0.0), 1.0, int(grid))
    values = np.array([tail_probability(point) for point in points])
    best = int(np.argmax(values))
    p_max = float(values[best])
    pi_max = float(points[best])
    if refine and points.size >= 3:
        lower = float(points[max(best - 1, 0)])
        upper = float(points[min(best + 1, points.size - 1)])
        if upper > lower:
            result = optimize.minimize_scalar(
                lambda value: -tail_probability(value),
                bounds=(lower, upper),
                method="bounded",
                options={"xatol": 1e-6},
            )
            if -result.fun > p_max:
                p_max = float(-result.fun)
                pi_max = float(result.x)
    return p_max, pi_max


def ni_exact_sensitivity(
    candidate_correct: Sequence[int],
    reference_correct: Sequence[int],
    *,
    margin: float = 0.05,
    alpha: float = 0.05,
    grid: int = 201,
    refine: bool = True,
) -> dict[str, Any]:
    """Exact and McNemar-based sensitivity p-values for paired binary NI.

    Three quantities are reported, all one-sided against ``d <= -margin``
    unless stated otherwise:

    * ``exact_unconditional_p`` - exact p-value maximised over the nuisance
      discordance (the defensible exact answer).
    * ``exact_conditional_p`` - McNemar conditional p-value with the nuisance
      fixed at its restricted MLE (approximate, reported for continuity).
    * ``mcnemar_p_zero_*`` - the classic McNemar tests against ``d = 0``,
      which answer a different question and are sensitivity only.

    Args:
        candidate_correct: Paired 0/1 correctness for the shallow depth.
        reference_correct: Paired 0/1 correctness for the reference depth.
        margin: Non-inferiority margin as a positive proportion.
        alpha: One-sided type-I rate.
        grid: Number of nuisance values in the exact search.
        refine: Refine the grid maximum with a bounded scalar search.
    """
    if margin <= 0.0:
        raise ValueError("margin must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    if grid < 3:
        raise ValueError("grid must be at least 3")
    candidate, reference = _binary_pair_arrays(candidate_correct, reference_correct)
    b_count, c_count, n_pairs = _discordant_counts(candidate, reference)
    discordant = b_count + c_count
    if discordant == 0:
        return {
            "method": "exact sensitivity",
            "margin": float(margin),
            "alpha": float(alpha),
            "n_pairs": n_pairs,
            "b": b_count,
            "c": c_count,
            "exact_unconditional_p": None,
            "exact_unconditional_discordance": None,
            "exact_conditional_p": None,
            "mcnemar_p_zero_two_sided": 1.0,
            "mcnemar_p_zero_candidate_worse": 1.0,
            "mcnemar_p_zero_candidate_better": 1.0,
            "sensitive_to_verdict": None,
            "note": "No discordant pairs: no exact test is defined.",
        }

    _, p_b, p_c, _boundary = _restricted_mle(b_count, c_count, n_pairs, margin)
    exact_p, exact_pi = _exact_unconditional_p(
        b_count, c_count, n_pairs, margin, grid=grid, refine=refine
    )
    pair_total = p_b + p_c
    theta_zero = p_b / pair_total if pair_total > 0.0 else 0.5
    conditional_p = float(scipy_stats.binom.sf(b_count - 1, discordant, theta_zero))
    p_zero_two = float(scipy_stats.binomtest(b_count, discordant, 0.5).pvalue)
    p_zero_worse = float(scipy_stats.binomtest(b_count, discordant, 0.5, alternative="less").pvalue)
    p_zero_better = float(
        scipy_stats.binomtest(b_count, discordant, 0.5, alternative="greater").pvalue
    )
    return {
        "method": "exact sensitivity",
        "margin": float(margin),
        "alpha": float(alpha),
        "n_pairs": n_pairs,
        "b": b_count,
        "c": c_count,
        "discordance": float(discordant / n_pairs),
        "exact_unconditional_p": float(exact_p),
        "exact_unconditional_discordance": float(exact_pi),
        "exact_conditional_p": conditional_p,
        "exact_conditional_null_split": float(theta_zero),
        "mcnemar_p_zero_two_sided": p_zero_two,
        "mcnemar_p_zero_candidate_worse": p_zero_worse,
        "mcnemar_p_zero_candidate_better": p_zero_better,
        "sensitive_to_verdict": bool(min(exact_p, conditional_p) <= alpha),
        "note": (
            "exact_unconditional_p is the Berger-Boos supremum over the nuisance "
            "discordance and is the primary exact sensitivity. exact_conditional_p fixes "
            "the nuisance at the restricted MLE and is approximate. The McNemar values "
            "test d = 0, not d = -margin."
        ),
    }


# ---------------------------------------------------------------------------
# Equivalence (TOST)
# ---------------------------------------------------------------------------


def tost(
    candidate_correct: Sequence[int],
    reference_correct: Sequence[int],
    *,
    margin: float = 0.05,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Two one-sided tests for equivalence of paired binary accuracy.

    Rejects ``d <= -margin`` (lower arm) and ``d >= +margin`` (upper arm) at
    level ``alpha`` each. Equivalence is declared when both reject, which is
    the same as the ``1 - 2 alpha`` interval lying strictly inside
    ``(-margin, +margin)``. The paired z uses the sample standard deviation of
    the differences, matching :func:`rag_energy.stats.p1.noninferiority`.
    """
    if margin <= 0.0:
        raise ValueError("margin must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    candidate, reference = _binary_pair_arrays(candidate_correct, reference_correct)
    diff = candidate - reference
    n_pairs = int(diff.size)
    if n_pairs < 2:
        raise ValueError("at least two pairs are required for a variance")
    mean_diff = float(diff.mean())
    sd_diff = float(diff.std(ddof=1))
    se = sd_diff / math.sqrt(n_pairs) if sd_diff > 0.0 else 0.0
    z_alpha = float(scipy_stats.norm.ppf(1.0 - alpha))
    if se == 0.0:
        p_lower = 0.0 if mean_diff > -margin else 1.0
        p_upper = 0.0 if mean_diff < margin else 1.0
        lower = upper = mean_diff
    else:
        p_lower = float(scipy_stats.norm.sf((mean_diff + margin) / se))
        p_upper = float(scipy_stats.norm.cdf((mean_diff - margin) / se))
        lower = mean_diff - z_alpha * se
        upper = mean_diff + z_alpha * se
    p_tost = max(p_lower, p_upper)
    return {
        "method": "two one-sided tests (paired z)",
        "margin": float(margin),
        "alpha": float(alpha),
        "n_pairs": n_pairs,
        "mean_diff": mean_diff,
        "sd_diff": sd_diff,
        "se": se,
        "p_lower": p_lower,
        "p_upper": p_upper,
        "p_tost": p_tost,
        "p_value": p_tost,
        "ci_level": float(1.0 - 2.0 * alpha),
        "lower_bound": float(lower),
        "upper_bound": float(upper),
        "equivalent": bool(p_tost <= alpha),
        "equivalent_from_interval": bool(lower > -margin and upper < margin),
        "failing_arm": (None if p_tost <= alpha else ("upper" if p_upper >= p_lower else "lower")),
    }


# ---------------------------------------------------------------------------
# Power, required n, MDE
# ---------------------------------------------------------------------------


def paired_difference_sd(discordance: float, difference: float = 0.0) -> float:
    """Standard deviation of a paired binary difference.

    ``d_i`` takes values in {-1, 0, +1}, so ``E[d_i^2] = P(discordant)`` and
    ``Var(d_i) = P(discordant) - E[d_i]^2``. This is an exact identity, not an
    approximation.

    Args:
        discordance: ``p_b + p_c`` in ``[0, 1]``.
        difference: ``p_b - p_c``.
    """
    if not 0.0 <= discordance <= 1.0:
        raise ValueError("discordance must lie in [0, 1]")
    variance = discordance - difference * difference
    if variance < 0.0:
        raise ValueError("discordance must be at least difference^2")
    return math.sqrt(variance)


def _resolve_sd(sd: float | None, discordance: float | None, difference: float) -> float:
    if sd is not None and discordance is not None:
        raise ValueError("pass either sd or discordance, not both")
    if sd is None and discordance is None:
        raise ValueError("pass sd or discordance")
    if sd is None:
        assert discordance is not None
        return paired_difference_sd(discordance, difference)
    if sd <= 0.0:
        raise ValueError("sd must be positive")
    return float(sd)


def realized_power(
    *,
    n: int,
    margin: float,
    true_diff: float,
    alpha: float = 0.05,
    sd: float | None = None,
    discordance: float | None = None,
) -> float:
    """Power of the one-sided paired NI test at a given true difference.

    ``power = Phi((d + margin) / (sigma / sqrt(n)) - z_{1-alpha})``.

    This is a design-precision statement at the observed discordance. It is
    not evidence about the hypothesis and must not be reported as such.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if margin <= 0.0:
        raise ValueError("margin must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    sigma = _resolve_sd(sd, discordance, true_diff)
    se = sigma / math.sqrt(n)
    z_alpha = float(scipy_stats.norm.ppf(1.0 - alpha))
    return float(scipy_stats.norm.cdf((true_diff + margin) / se - z_alpha))


def required_n(
    *,
    margin: float,
    true_diff: float,
    power: float = 0.8,
    alpha: float = 0.05,
    sd: float | None = None,
    discordance: float | None = None,
    max_n: int = 100_000_000,
) -> int | None:
    """Pairs required for a one-sided paired NI test at the given power.

    Inverts the power formula:

    ``n = ceil(((z_{1-alpha} + z_{power}) * sigma / (margin + true_diff))^2)``.

    Returns ``None`` when ``margin + true_diff <= 0`` (no sample size reaches
    the target power) or when the answer exceeds ``max_n``.
    """
    if margin <= 0.0:
        raise ValueError("margin must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    if not 0.5 <= power < 1.0:
        raise ValueError("power must lie in [0.5, 1)")
    gap = margin + true_diff
    if gap <= 0.0:
        return None
    sigma = _resolve_sd(sd, discordance, true_diff)
    z_alpha = float(scipy_stats.norm.ppf(1.0 - alpha))
    z_power = float(scipy_stats.norm.ppf(power))
    needed = ((z_alpha + z_power) * sigma / gap) ** 2
    if not math.isfinite(needed) or needed > max_n:
        return None
    return int(math.ceil(needed))


def mde(
    *,
    n: int,
    margin: float,
    alpha: float = 0.05,
    power: float = 0.8,
    sd: float | None = None,
    discordance: float | None = None,
) -> dict[str, Any]:
    """Minimum detectable difference for the paired NI design.

    The smallest true difference that still rejects the NI null with
    probability ``power``:

    ``d_mde = (z_{1-alpha} + z_{power}) * sigma / sqrt(n) - margin``.

    ``d_mde`` is negative when the design is under-powered. ``mde_loss_pp``
    is the corresponding maximum tolerable true loss, in percentage points,
    that the design can still certify at ``margin``.

    With a fixed ``sd`` the formula is direct. With ``discordance`` the
    variance follows the exact identity ``sigma(d)^2 = pi_d - d^2``, so the
    reported value solves

    ``d + margin = (z_{1-alpha} + z_{power}) * sqrt(pi_d - d^2) / sqrt(n)``

    for the root with ``d + margin > 0``. That keeps :func:`mde` and
    :func:`required_n` on the same variance convention.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if margin <= 0.0:
        raise ValueError("margin must be positive")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must lie in (0, 0.5)")
    if not 0.5 <= power < 1.0:
        raise ValueError("power must lie in [0.5, 1)")
    if sd is not None and discordance is not None:
        raise ValueError("pass either sd or discordance, not both")
    if sd is None and discordance is None:
        raise ValueError("pass sd or discordance")

    z_alpha = float(scipy_stats.norm.ppf(1.0 - alpha))
    z_power = float(scipy_stats.norm.ppf(power))
    if sd is not None:
        if sd <= 0.0:
            raise ValueError("sd must be positive")
        sigma = float(sd)
        se = sigma / math.sqrt(n)
        difference = (z_alpha + z_power) * se - margin
        convention = "fixed sd"
    else:
        assert discordance is not None
        if not 0.0 <= discordance <= 1.0:
            raise ValueError("discordance must lie in [0, 1]")
        scale = (z_alpha + z_power) / math.sqrt(n)
        quadratic_a = 1.0 + scale * scale
        quadratic_b = 2.0 * margin
        quadratic_c = margin * margin - scale * scale * discordance
        discriminant = quadratic_b * quadratic_b - 4.0 * quadratic_a * quadratic_c
        if discriminant < 0.0:
            return {
                "n_pairs": int(n),
                "margin": float(margin),
                "alpha": float(alpha),
                "power": float(power),
                "sd": None,
                "se": None,
                "mde_difference": None,
                "mde_difference_pp": None,
                "mde_loss_pp": None,
                "convention": "discordance identity",
                "note": "No real solution: the design cannot reach the target power.",
            }
        difference = (-quadratic_b + math.sqrt(discriminant)) / (2.0 * quadratic_a)
        sigma = paired_difference_sd(discordance, difference)
        se = sigma / math.sqrt(n)
        convention = "discordance identity Var(d) = pi_d - d^2"

    return {
        "n_pairs": int(n),
        "margin": float(margin),
        "alpha": float(alpha),
        "power": float(power),
        "sd": sigma,
        "se": se,
        "mde_difference": float(difference),
        "mde_difference_pp": float(100.0 * difference),
        "mde_loss_pp": float(-100.0 * difference),
        "convention": convention,
        "note": (
            "mde_loss_pp is the largest true loss (in pp) that this design can still "
            "certify as non-inferior at the given margin and power."
        ),
    }


# ---------------------------------------------------------------------------
# BCa bootstrap
# ---------------------------------------------------------------------------


def _quantile(values: np.ndarray, q: float) -> float:
    """Empirical quantile that keeps explicit infinite tails.

    All-finite input uses :func:`numpy.quantile`. With infinite values the
    inverse-ECDF index is used so that an infinite tail is never silently
    dropped.
    """
    finite = np.sort(values[np.isfinite(values)])
    n_negative = int(np.isneginf(values).sum())
    n_positive = int(np.isposinf(values).sum())
    total = int(values.size)
    if n_negative == 0 and n_positive == 0:
        return float(np.quantile(values, q))
    index = min(total - 1, max(0, int(math.ceil(q * (total - 1)))))
    if index < n_negative:
        return float("-inf")
    if index >= total - n_positive:
        return float("inf")
    return float(finite[index - n_negative])


def bca_interval(
    n_observations: int,
    statistic: Callable[[np.ndarray], float],
    *,
    resamples: int = 2000,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Bias-corrected and accelerated (BCa) bootstrap interval.

    ``statistic`` receives an array of observation indices and returns a
    scalar, so the same routine serves a mean and a ratio of sums. The
    acceleration comes from the delete-one jackknife.

    Args:
        n_observations: Number of independent units (questions).
        statistic: Callable mapping an index array to a scalar.
        resamples: Bootstrap resamples.
        seed: Recorded RNG seed.
        alpha: Two-sided error rate; the interval has level ``1 - alpha``.
    """
    if n_observations < 2:
        raise ValueError("at least two observations are required")
    if resamples <= 0:
        raise ValueError("resamples must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    n = int(n_observations)
    indices = np.arange(n)
    point = float(statistic(indices))

    rng = np.random.default_rng(seed)
    draws = np.empty(resamples, dtype=float)
    for r in range(resamples):
        draws[r] = statistic(rng.integers(0, n, size=n))

    jackknife = np.empty(n, dtype=float)
    for i in range(n):
        jackknife[i] = statistic(np.delete(indices, i))
    finite_jackknife = np.isfinite(jackknife)
    n_infinite_jackknife = int((~finite_jackknife).sum())
    if int(finite_jackknife.sum()) >= 2:
        usable_jackknife = jackknife[finite_jackknife]
        jack_mean = float(usable_jackknife.mean())
        deviations = usable_jackknife - jack_mean
        denominator = 6.0 * float(np.sum(deviations**2)) ** 1.5
        acceleration = float(np.sum(deviations**3)) / denominator if denominator > 0.0 else 0.0
    else:
        acceleration = 0.0

    usable = ~np.isnan(draws)
    p_less = float(np.mean(draws[usable] < point)) if usable.any() else 0.5
    clipped = min(max(p_less, 1.0 / (resamples + 1.0)), 1.0 - 1.0 / (resamples + 1.0))
    z_0 = float(scipy_stats.norm.ppf(clipped))

    def adjust(level: float) -> float:
        z_level = float(scipy_stats.norm.ppf(level))
        shifted = z_0 + z_level
        scale = 1.0 - acceleration * shifted
        if scale == 0.0:
            return 0.5
        return float(scipy_stats.norm.cdf(z_0 + shifted / scale))

    alpha_low = adjust(alpha / 2.0)
    alpha_high = adjust(1.0 - alpha / 2.0)
    return {
        "method": "BCa",
        "level": float(1.0 - alpha),
        "alpha": float(alpha),
        "n_observations": n,
        "resamples": int(resamples),
        "seed": int(seed),
        "point": point,
        "lower": _quantile(draws, alpha_low),
        "upper": _quantile(draws, alpha_high),
        "alpha_low": alpha_low,
        "alpha_high": alpha_high,
        "bias_correction": z_0,
        "acceleration": acceleration,
        "percentile_interval": _percentile_interval(draws),
        "n_infinite": int(np.isinf(draws).sum()),
        "n_missing": int(np.isnan(draws).sum()),
        "n_infinite_jackknife": n_infinite_jackknife,
    }


def bca_mean_difference(
    differences: Sequence[float],
    *,
    resamples: int = 2000,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """BCa interval for the mean of paired differences."""
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1:
        raise ValueError("differences must be one-dimensional")
    result = bca_interval(
        values.size,
        lambda index: float(values[index].mean()),
        resamples=resamples,
        seed=seed,
        alpha=alpha,
    )
    result["estimand"] = "paired mean difference"
    return result


def bca_savings(
    candidate_joules: Sequence[float],
    candidate_correct: Sequence[int],
    reference_joules: Sequence[float],
    reference_correct: Sequence[int],
    *,
    resamples: int = 2000,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """BCa interval for ``1 - E(candidate) / E(reference)`` (ratio of sums)."""
    j_c = np.asarray(candidate_joules, dtype=float)
    c_c = np.asarray(candidate_correct, dtype=float)
    j_r = np.asarray(reference_joules, dtype=float)
    c_r = np.asarray(reference_correct, dtype=float)
    sizes = {j_c.size, c_c.size, j_r.size, c_r.size}
    if len(sizes) != 1:
        raise ValueError("all four vectors must have the same length")
    if j_c.size < 2:
        raise ValueError("at least two pairs are required")

    def statistic(index: np.ndarray) -> float:
        return _savings_from_sums(
            float(j_c[index].sum()),
            float(c_c[index].sum()),
            float(j_r[index].sum()),
            float(c_r[index].sum()),
        )

    result = bca_interval(j_c.size, statistic, resamples=resamples, seed=seed, alpha=alpha)
    result["estimand"] = "savings 1 - E(candidate)/E(reference)"
    return result


def _savings_from_sums(
    sum_j_candidate: float,
    sum_c_candidate: float,
    sum_j_reference: float,
    sum_c_reference: float,
) -> float:
    """``1 - E_c / E_r`` with ``E = inf`` when nothing is correct.

    Matches the arithmetic in :func:`rag_energy.stats.p1.bootstrap`: an
    infinite reference ``E`` gives savings of 1, an infinite candidate ``E``
    gives ``-inf``, and two infinite values give ``nan``.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        e_candidate = (
            np.float64(sum_j_candidate) / np.float64(sum_c_candidate)
            if sum_c_candidate > 0.0
            else np.float64(np.inf)
        )
        e_reference = (
            np.float64(sum_j_reference) / np.float64(sum_c_reference)
            if sum_c_reference > 0.0
            else np.float64(np.inf)
        )
        return float(1.0 - e_candidate / e_reference)


# ---------------------------------------------------------------------------
# Joint question bootstrap
# ---------------------------------------------------------------------------


def _bootstrap_distributions(
    rows: Sequence[dict[str, Any]],
    *,
    candidate: int,
    reference: int,
    margin: float,
    savings_floor: float,
    resamples: int,
    seed: int,
    alpha: float,
    sampler: Callable[[np.random.Generator], np.ndarray],
    unit: str,
) -> dict[str, Any]:
    """Shared engine for the joint and cluster bootstraps.

    Each resample recomputes, from one draw of questions: ``A(k)`` and
    ``E(k)`` at every depth, the feasible set at ``margin``, the selected
    depth, the paired savings ``1 - E(4)/E(32)`` on the paired population, and
    the one-sided NI decision ``mean - z_{1-alpha} se > -margin``. The joint
    indicator is ``NI and savings >= savings_floor``.
    """
    qids, depths, joules, correct = _depth_matrices(rows, "em")
    n_questions, n_depths = joules.shape
    if candidate not in depths or reference not in depths:
        raise ValueError("candidate and reference depths must both be present")
    if n_questions < 2:
        raise ValueError("at least two questions are required")
    candidate_index = depths.index(candidate)
    reference_index = depths.index(reference)

    present = np.isfinite(joules)
    present_f = present.astype(float)
    joules_masked = np.where(present, joules, 0.0)
    correct_masked = np.where(present, correct, 0.0)
    z_alpha = float(scipy_stats.norm.ppf(1.0 - alpha))

    point_sums_j = joules_masked.sum(axis=0)
    point_sums_c = correct_masked.sum(axis=0)
    point_counts = present_f.sum(axis=0)
    point_accuracy = np.where(
        point_counts > 0, point_sums_c / np.where(point_counts > 0, point_counts, 1.0), np.nan
    )
    point_e = np.full(n_depths, np.inf)
    positive = point_sums_c > 0
    point_e[positive] = point_sums_j[positive] / point_sums_c[positive]

    accuracy_draws = np.full((resamples, n_depths), np.nan)
    savings_draws = np.full(resamples, np.nan)
    difference_draws = np.full(resamples, np.nan)
    selected = np.empty(resamples, dtype=int)
    non_inferior = np.zeros(resamples, dtype=bool)
    savings_met = np.zeros(resamples, dtype=bool)
    paired_counts = np.zeros(resamples, dtype=int)

    rng = np.random.default_rng(seed)
    for r in range(resamples):
        index = sampler(rng)
        block_j = joules_masked[index]
        block_c = correct_masked[index]
        block_present = present_f[index]
        sums_j = block_j.sum(axis=0)
        sums_c = block_c.sum(axis=0)
        counts = block_present.sum(axis=0)
        accuracy = np.where(counts > 0, sums_c / np.where(counts > 0, counts, 1.0), np.nan)
        energy = np.full(n_depths, np.inf)
        feasible_energy = sums_c > 0
        energy[feasible_energy] = sums_j[feasible_energy] / sums_c[feasible_energy]
        accuracy_draws[r] = accuracy

        left = correct[index, candidate_index]
        right = correct[index, reference_index]
        both = np.isfinite(left) & np.isfinite(right)
        n_pairs = int(both.sum())
        paired_counts[r] = n_pairs
        if n_pairs >= 2:
            differences = left[both] - right[both]
            mean_diff = float(differences.mean())
            se = float(differences.std(ddof=1)) / math.sqrt(n_pairs)
            difference_draws[r] = mean_diff
            non_inferior[r] = bool(mean_diff - z_alpha * se > -margin)
        elif n_pairs == 1:
            mean_diff = float(left[both] - right[both])
            difference_draws[r] = mean_diff
            non_inferior[r] = bool(mean_diff > -margin)

        if n_pairs >= 1:
            savings_draws[r] = _savings_from_sums(
                float(joules_masked[index, candidate_index][both].sum()),
                float(correct_masked[index, candidate_index][both].sum()),
                float(joules_masked[index, reference_index][both].sum()),
                float(correct_masked[index, reference_index][both].sum()),
            )
            savings_met[r] = bool(
                not math.isnan(savings_draws[r]) and savings_draws[r] >= savings_floor
            )

        reference_accuracy = accuracy[reference_index]
        if np.isfinite(reference_accuracy):
            feasible = accuracy >= reference_accuracy - margin
            masked = np.where(feasible, energy, np.inf)
            if np.isfinite(masked).any():
                selected[r] = int(np.argmin(masked))
            else:
                selected[r] = -1
        else:
            selected[r] = -1

    interior = (selected >= 0) & (selected > 0) & (selected < n_depths - 1)
    joint = non_inferior & savings_met
    p_k_optimal = {
        str(depth): float(np.mean(selected == index)) for index, depth in enumerate(depths)
    }
    p_k_optimal["none"] = float(np.mean(selected == -1))

    point_savings = _savings_from_sums(
        float(joules_masked[:, candidate_index][present[:, candidate_index]].sum()),
        float(correct_masked[:, candidate_index][present[:, candidate_index]].sum()),
        float(joules_masked[:, reference_index][present[:, reference_index]].sum()),
        float(correct_masked[:, reference_index][present[:, reference_index]].sum()),
    )
    point_pairs = int((present[:, candidate_index] & present[:, reference_index]).sum())

    return {
        "unit": unit,
        "resamples": int(resamples),
        "seed": int(seed),
        "alpha": float(alpha),
        "margin": float(margin),
        "savings_floor": float(savings_floor),
        "n_questions": n_questions,
        "n_pairs_point": point_pairs,
        "candidate": int(candidate),
        "reference": int(reference),
        "point": {
            "accuracy": {str(k): float(point_accuracy[i]) for i, k in enumerate(depths)},
            "e_per_correct": {
                str(k): (None if not math.isfinite(point_e[i]) else float(point_e[i]))
                for i, k in enumerate(depths)
            },
            "savings": None if math.isnan(point_savings) else float(point_savings),
        },
        "paired_n": {
            "median": float(np.median(paired_counts)),
            "min": int(paired_counts.min()),
            "max": int(paired_counts.max()),
        },
        "p_non_inferior": float(np.mean(non_inferior)),
        "p_savings_floor": float(np.mean(savings_met)),
        "p_joint": float(np.mean(joint)),
        "p_joint_interior": float(np.mean(joint & interior)),
        "p_selected_interior": float(np.mean(interior)),
        "p_k_optimal": p_k_optimal,
        "difference_interval": _percentile_interval(difference_draws),
        "savings_interval": _percentile_interval(savings_draws),
        "definition": (
            "Each resample draws questions once and recomputes A(k), E(k), the 5 pp "
            "feasible set, the selected depth, the paired savings and the one-sided NI "
            "decision (mean - 1.645 se > -margin). p_joint is the resample fraction with "
            "NI and savings >= the floor."
        ),
    }


def joint_question_bootstrap(
    rows: Sequence[dict[str, Any]],
    *,
    candidate: int = 4,
    reference: int = 32,
    margin: float = 0.05,
    savings_floor: float = 0.20,
    resamples: int = 2000,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Joint question-level bootstrap of the decision quantities.

    One resample of questions drives accuracy, ``E(k)``, savings, selection and
    the NI decision together, so the reported joint probability respects their
    dependence. The unit is a question and questions are paired across depths.
    """
    if resamples <= 0:
        raise ValueError("resamples must be positive")
    qids, _depths, joules, _correct = _depth_matrices(rows, "em")
    n_questions = len(qids)
    if n_questions < 2:
        raise ValueError("at least two questions are required")

    def sampler(rng: np.random.Generator) -> np.ndarray:
        return rng.integers(0, n_questions, size=n_questions)

    payload = _bootstrap_distributions(
        rows,
        candidate=candidate,
        reference=reference,
        margin=margin,
        savings_floor=savings_floor,
        resamples=resamples,
        seed=seed,
        alpha=alpha,
        sampler=sampler,
        unit="question",
    )
    payload["clustering"] = "none"
    return payload


def cluster_bootstrap(
    rows: Sequence[dict[str, Any]],
    *,
    cluster_key: str = "context_id",
    candidate: int = 4,
    reference: int = 32,
    margin: float = 0.05,
    savings_floor: float = 0.20,
    resamples: int = 2000,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Cluster bootstrap by ``cluster_key`` when the column exists.

    P1 has no external context grouping: every question is independent. When
    the column is absent the function returns ``supported: False`` with the
    observed columns and does not invent a clustering. When present, clusters
    are resampled with replacement and every member question travels with its
    cluster.
    """
    if resamples <= 0:
        raise ValueError("resamples must be positive")
    if not rows:
        raise ValueError("no rows")
    columns = list(rows[0].keys())
    if cluster_key not in columns:
        return {
            "supported": False,
            "cluster_key": cluster_key,
            "status": "skipped",
            "reason": (
                f"the raw CSV has no {cluster_key!r} column; P1 questions are independent "
                "and no clustering is defined"
            ),
            "columns_observed": columns,
            "resamples": 0,
        }

    qids, _depths, _joules, _correct_values = _depth_matrices(rows, "em")
    question_cluster: dict[str, str] = {}
    for row in rows:
        question_cluster.setdefault(str(row["question_id"]), str(row.get(cluster_key, "")))
    members: dict[str, list[int]] = {}
    for index, qid in enumerate(qids):
        members.setdefault(question_cluster[qid], []).append(index)
    arrays = [np.asarray(items, dtype=int) for _key, items in sorted(members.items()) if items]
    if len(arrays) < 2:
        return {
            "supported": False,
            "cluster_key": cluster_key,
            "status": "skipped",
            "reason": "fewer than two clusters carry rows",
            "columns_observed": columns,
            "resamples": 0,
        }

    def sampler(rng: np.random.Generator) -> np.ndarray:
        picks = rng.integers(0, len(arrays), size=len(arrays))
        return np.concatenate([arrays[pick] for pick in picks])

    payload = _bootstrap_distributions(
        rows,
        candidate=candidate,
        reference=reference,
        margin=margin,
        savings_floor=savings_floor,
        resamples=resamples,
        seed=seed,
        alpha=alpha,
        sampler=sampler,
        unit="cluster",
    )
    payload.update(
        {
            "supported": True,
            "cluster_key": cluster_key,
            "status": "computed",
            "n_clusters": len(arrays),
            "clustering": cluster_key,
        }
    )
    return payload


# ---------------------------------------------------------------------------
# Payload assembly
# ---------------------------------------------------------------------------


def _default_power_differences(observed: float) -> list[float]:
    """Grid of alternatives for the power table, always including the observed."""
    targets = {0.0, -0.01, -0.02, -0.03, round(float(observed), 6)}
    return sorted(targets, reverse=True)


def build_inference_payload(
    rows: Sequence[dict[str, Any]],
    *,
    run_id: str,
    candidate: int = 4,
    reference: int = 32,
    margin: float = 0.05,
    alpha: float = 0.05,
    resamples: int = 2000,
    savings_floor: float = 0.20,
    power_differences: Sequence[float] | None = None,
    cluster_key: str = "context_id",
    registered: dict[str, Any] | None = None,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Assemble the exploratory inference payload for one registered run."""
    if not rows:
        raise ValueError("no rows")
    candidate_rows, reference_rows, excluded = paired_questions(rows, candidate, reference)
    candidate_correct = [_correct(row, "em") for row in candidate_rows]
    reference_correct = [_correct(row, "em") for row in reference_rows]
    if not candidate_correct:
        raise ValueError("no paired questions")

    primary = noninferiority(candidate_correct, reference_correct, margin=margin)
    score = ni_score_test(candidate_correct, reference_correct, margin=margin, alpha=alpha)
    exact = ni_exact_sensitivity(candidate_correct, reference_correct, margin=margin, alpha=alpha)
    tost_5 = tost(candidate_correct, reference_correct, margin=0.05, alpha=alpha)
    tost_2 = tost(candidate_correct, reference_correct, margin=0.02, alpha=alpha)

    differences = np.asarray(candidate_correct, dtype=float) - np.asarray(
        reference_correct, dtype=float
    )
    bca_difference = bca_mean_difference(differences, resamples=resamples, seed=seed, alpha=alpha)
    bca_saving = bca_savings(
        [float(row["j_total"]) for row in candidate_rows],
        candidate_correct,
        [float(row["j_total"]) for row in reference_rows],
        reference_correct,
        resamples=resamples,
        seed=seed,
        alpha=alpha,
    )

    discordance = (primary.b + primary.c) / primary.n_pairs
    targets = (
        list(power_differences)
        if power_differences is not None
        else _default_power_differences(primary.mean_diff)
    )
    power_rows: list[dict[str, Any]] = []
    for target in targets:
        power_rows.append(
            {
                "true_diff": float(target),
                "true_diff_pp": float(100.0 * target),
                "realized_power": realized_power(
                    n=primary.n_pairs,
                    margin=margin,
                    true_diff=float(target),
                    alpha=alpha,
                    discordance=discordance,
                ),
                "required_n_50pct": required_n(
                    margin=margin,
                    true_diff=float(target),
                    power=0.5,
                    alpha=alpha,
                    discordance=discordance,
                ),
                "required_n_80pct": required_n(
                    margin=margin,
                    true_diff=float(target),
                    power=0.8,
                    alpha=alpha,
                    discordance=discordance,
                ),
                "required_n_80pct_sample_sd": required_n(
                    margin=margin,
                    true_diff=float(target),
                    power=0.8,
                    alpha=alpha,
                    sd=primary.sd_diff,
                ),
            }
        )

    mde_payload = mde(
        n=primary.n_pairs, margin=margin, alpha=alpha, power=0.8, discordance=discordance
    )
    mde_payload["power_50pct"] = mde(
        n=primary.n_pairs, margin=margin, alpha=alpha, power=0.5, discordance=discordance
    )

    joint = joint_question_bootstrap(
        rows,
        candidate=candidate,
        reference=reference,
        margin=margin,
        savings_floor=savings_floor,
        resamples=resamples,
        seed=seed,
        alpha=alpha,
    )
    cluster = cluster_bootstrap(
        rows,
        cluster_key=cluster_key,
        candidate=candidate,
        reference=reference,
        margin=margin,
        savings_floor=savings_floor,
        resamples=resamples,
        seed=seed,
        alpha=alpha,
    )

    consistency: dict[str, Any] | None = None
    if registered is not None:
        registered_primary = registered.get("primary", {})
        checks = {
            "n_pairs": (primary.n_pairs, registered_primary.get("n_pairs")),
            "mean_diff": (primary.mean_diff, registered_primary.get("mean_diff")),
            "lower_bound": (primary.lower_bound, registered_primary.get("lower_bound")),
            "non_inferior": (primary.non_inferior, registered_primary.get("non_inferior")),
        }
        consistent = True
        details: dict[str, Any] = {}
        for key, (observed, recorded) in checks.items():
            if isinstance(observed, bool) or isinstance(recorded, bool):
                matches = bool(observed) == bool(recorded)
            elif recorded is None:
                matches = None
            else:
                matches = abs(float(observed) - float(recorded)) <= 1e-9
            details[key] = {"observed": observed, "registered": recorded, "matches": matches}
            if matches is False:
                consistent = False
        consistency = {
            "checked_against": "analysis/squad_qwen4b_p1/noninferiority.json",
            "consistent": consistent,
            "details": details,
        }

    return {
        "run_id": run_id,
        "layer": "exploratory/sensitivity",
        "claim_boundary": CLAIM_BOUNDARY,
        "design": {
            "candidate_depth": int(candidate),
            "reference_depth": int(reference),
            "margin": float(margin),
            "alpha": float(alpha),
            "n_pairs": int(primary.n_pairs),
            "n_excluded_questions": len(excluded),
            "excluded_question_ids": excluded,
            "n_invalid_candidate": int(primary.n_invalid_candidate),
            "n_invalid_reference": int(primary.n_invalid_reference),
            "b": int(primary.b),
            "c": int(primary.c),
            "discordance": float(discordance),
            "mean_diff": float(primary.mean_diff),
            "sd_diff": float(primary.sd_diff),
            "se": float(primary.se),
        },
        "preregistered_primary": {
            "role": "confirmatory, unchanged",
            "margin": float(primary.margin),
            "z": float(primary.z),
            "p_value": primary.p_value,
            "lower_bound": float(primary.lower_bound),
            "upper_bound": float(primary.upper_bound),
            "non_inferior": bool(primary.non_inferior),
            "mcnemar_exact_p": float(primary.mcnemar_exact_p),
            "mcnemar_z_p": float(primary.mcnemar_z_p),
            "verdict": "non-inferior" if primary.non_inferior else "not supported",
        },
        "consistency_with_registered_analysis": consistency,
        "score_test": score,
        "exact_sensitivity": exact,
        "tost": {"five_pp": tost_5, "two_pp": {**tost_2, "role": "estimation-only"}},
        "realized_power": power_rows,
        "power_design": {
            "discordance": float(discordance),
            "sd_from_discordance": paired_difference_sd(discordance, primary.mean_diff),
            "sd_observed": float(primary.sd_diff),
            "formula": (
                "Var(d_i) = discordance - mean_diff^2; "
                "power = Phi((d + margin)/(sigma/sqrt(n)) - z_{1-alpha})"
            ),
            "caveat": (
                "Realized power at the observed discordance is a design-precision "
                "diagnostic, not evidence for or against the hypothesis."
            ),
        },
        "mde": mde_payload,
        "bca": {
            "mean_difference": bca_difference,
            "savings": bca_saving,
        },
        "joint_bootstrap": joint,
        "cluster_bootstrap": cluster,
        "caveats": [
            "All inference here is exploratory or sensitivity analysis.",
            "The preregistered 5 pp verdict is unchanged; no new margin is certified.",
            "The P1 raw CSV has no context_id, so no cluster bootstrap is computed.",
            "Post hoc power uses the observed discordance and is not a design guarantee.",
        ],
    }
