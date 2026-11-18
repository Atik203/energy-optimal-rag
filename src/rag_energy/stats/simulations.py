"""Monte Carlo simulations for the ratio estimator, the NI test, and selection.

Three CPU-only studies:

* **S1** -- the ratio estimand ``E = E[J] / E[C]`` with paired ``(J, C)``,
  ``C ~ Bernoulli(A)`` and energy from a lognormal or gamma copula. The study
  compares the ratio of sums, the mean of per-query ratios, the delta-method
  standard error, the percentile bootstrap, and BCa.
* **S2** -- the one-sided paired non-inferiority test at a 5 pp margin over a
  grid of true paired differences. Rejection rates, type-I error at the margin,
  and interval coverage are reported for the frozen z test and a score
  sensitivity.
* **S3** -- selection over seven depths with known ``A(k)`` and ``E(k)``. The
  gap between the best and second-best feasible depth is varied. Selection
  reliability, the winner's curse, and the certification cost ``N*`` are
  reported.

Every function is deterministic given an explicit integer seed. Nothing here
reads a run, a GPU, or the network. These are simulations; they are not
empirical results and they do not re-adjudicate any pre-registered gate.

The module uses the frozen estimator and test implementations where they are
directly applicable: ``ratio_standard_error`` for the delta-method check,
``noninferiority`` for S2, ``certification_cost`` for S3, and
``p1.bootstrap`` for an engine cross-check in S3. The large grids use
vectorized equivalents of the same formulas; the cross-checks are recorded in
the output.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from scipy import integrate, special, stats

from rag_energy.stats.p1 import (
    DepthSummary,
    certification_cost,
    noninferiority,
)
from rag_energy.stats.p1 import (
    bootstrap as p1_bootstrap,
)
from rag_energy.stats.ratio import ratio_standard_error

DEPTHS: tuple[int, ...] = (0, 1, 2, 4, 8, 16, 32)
DEFAULT_SEED = 20261115
MARGIN = 0.05
ALPHA = 0.05
Z_975 = float(stats.norm.ppf(0.975))
Z_95 = float(stats.norm.ppf(0.95))

# S1 defaults. The energy intercept and slope are the pilot values used as a
# simulation input, not a claim about any run.
S1_ACCURACIES: tuple[float, ...] = (0.1, 0.3, 0.5, 0.8)
S1_SAMPLE_SIZES: tuple[int, ...] = (200, 500, 1000, 2000)
S1_NOISES: tuple[str, ...] = ("lognormal", "gamma")
S1_REPS = 2000
S1_BOOTSTRAP_REPS = 400
S1_BOOTSTRAP_RESAMPLES = 300
S1_ENERGY_A = 15.74
S1_ENERGY_B = 2.283
S1_ENERGY_K = 4
S1_ENERGY_CV = 0.35
S1_ENERGY_RHO = 0.5

# S2 defaults: a 50% reference accuracy and a 12% discordant-pair rate. These
# are planning inputs, not measured values.
S2_SAMPLE_SIZES: tuple[int, ...] = (200, 500, 1000, 2000)
S2_DIFFERENCES: tuple[float, ...] = (-0.08, -0.05, -0.02, 0.0, 0.02)
S2_REPS = 2000
S2_REFERENCE_ACCURACY = 0.50
S2_DISCORDANCE = 0.12

# S3 defaults. A(k) is flat enough at the top that k=4 is gate-feasible, and
# the energy slope is solved so the k=4 / k=8 gap matches the requested value.
S3_GAPS: tuple[float, ...] = (0.02, 0.10, 0.25)
S3_SAMPLE_SIZES: tuple[int, ...] = (200, 500, 1000)
S3_REPS = 1000
S3_BOOTSTRAP_REPS = 400
S3_BOOTSTRAP_RESAMPLES = 200
S3_ACCURACY: tuple[float, ...] = (0.30, 0.40, 0.42, 0.46, 0.475, 0.49, 0.50)
S3_ENERGY_A = 15.74
S3_ENERGY_CV = 0.35
S3_RHO_CORRECT = 0.30
S3_RHO_ENERGY = 0.50
S3_TRUE_DEPTH = 4


def _json_safe(value: Any) -> Any:
    """Convert numpy and non-finite values into JSON-safe objects."""
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if math.isnan(number):
            return None
        if math.isinf(number):
            return "inf" if number > 0 else "-inf"
        return number
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _finite_mean(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    return float(finite.mean()) if finite.size else None


def _percentile_bounds(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    """Percentile bounds that retain an infinite tail instead of dropping it."""
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("-inf"), float("inf")
    alpha = 1.0 - confidence
    lower = float(np.quantile(finite, alpha / 2.0))
    upper = float(np.quantile(finite, 1.0 - alpha / 2.0))
    if np.isposinf(values).any():
        upper = float("inf")
    if np.isneginf(values).any():
        lower = float("-inf")
    return lower, upper


def _bca_bounds(
    boot: np.ndarray,
    joules: np.ndarray,
    correct: np.ndarray,
    theta_hat: float,
    confidence: float = 0.95,
) -> tuple[float, float, bool]:
    """BCa interval for the ratio of sums; fall back when it is undefined."""
    finite = boot[np.isfinite(boot)]
    if finite.size < 10 or not math.isfinite(theta_hat):
        lower, upper = _percentile_bounds(boot, confidence)
        return lower, upper, True
    proportion = float(np.mean(finite < theta_hat))
    n_finite = finite.size
    proportion = min(max(proportion, 1.0 / (2.0 * n_finite)), 1.0 - 1.0 / (2.0 * n_finite))
    z0 = float(stats.norm.ppf(proportion))
    total_j = float(joules.sum())
    total_c = float(correct.sum())
    denominator = total_c - correct
    with np.errstate(divide="ignore", invalid="ignore"):
        jackknife = (total_j - joules) / denominator
    usable = jackknife[np.isfinite(jackknife)]
    if usable.size < 2:
        lower, upper = _percentile_bounds(boot, confidence)
        return lower, upper, True
    deviations = usable.mean() - usable
    denominator_a = 6.0 * float(np.sum(deviations**2)) ** 1.5
    acceleration = float(np.sum(deviations**3) / denominator_a) if denominator_a > 0 else 0.0
    alpha = (1.0 - confidence) / 2.0
    z_low = float(stats.norm.ppf(alpha))
    z_high = float(stats.norm.ppf(1.0 - alpha))
    low_adjusted = z0 + (z0 + z_low) / (1.0 - acceleration * (z0 + z_low))
    high_adjusted = z0 + (z0 + z_high) / (1.0 - acceleration * (z0 + z_high))
    if not math.isfinite(low_adjusted) or not math.isfinite(high_adjusted):
        lower, upper = _percentile_bounds(boot, confidence)
        return lower, upper, True
    lower = float(np.quantile(finite, float(stats.norm.cdf(low_adjusted))))
    upper = float(np.quantile(finite, float(stats.norm.cdf(high_adjusted))))
    if not lower <= upper:
        lower, upper = _percentile_bounds(boot, confidence)
        return lower, upper, True
    if np.isposinf(boot).any():
        upper = float("inf")
    if np.isneginf(boot).any():
        lower = float("-inf")
    return lower, upper, False


def _delta_standard_errors(joules: np.ndarray, correct: np.ndarray) -> np.ndarray:
    """Vectorized delta-method SEs, one per row of a ``(reps, n)`` design.

    This mirrors ``ratio.delta_method_variance``. The frozen function is used
    on a small subset as a numerical cross-check.
    """
    n = joules.shape[1]
    mean_j = joules.mean(axis=1)
    mean_c = correct.mean(axis=1)
    var_j = joules.var(axis=1, ddof=1)
    var_c = correct.var(axis=1, ddof=1)
    covariance = ((joules * correct).mean(axis=1) - mean_j * mean_c) * n / (n - 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        variance = (
            var_j / mean_c**2
            + mean_j**2 * var_c / mean_c**4
            - 2.0 * mean_j * covariance / mean_c**3
        )
        standard_error = np.sqrt(np.maximum(variance, 0.0) / n)
    standard_error = np.where(mean_c > 0, standard_error, np.inf)
    return standard_error


def _conditional_energy_lognormal(mean_j: float, cv: float, rho: float, accuracy: float) -> float:
    """``E[J | C = 1]`` for the lognormal shared-latent model."""
    threshold = float(stats.norm.ppf(1.0 - accuracy))
    shifted = cv * rho - threshold
    return float(mean_j * stats.norm.cdf(shifted) / accuracy)


def _conditional_energy_gamma(mean_j: float, cv: float, rho: float, accuracy: float) -> float:
    """``E[J | C = 1]`` for the gamma Gaussian-copula model by quadrature."""
    shape = 1.0 / (cv * cv)
    scale = mean_j / shape
    threshold = float(stats.norm.ppf(1.0 - accuracy))
    nodes, weights = np.polynomial.hermite_e.hermegauss(40)
    weights = weights / math.sqrt(2.0 * math.pi)
    root = math.sqrt(max(0.0, 1.0 - rho * rho))

    def conditional_at(z: float) -> float:
        latent = rho * z + root * nodes
        quantile_input = np.clip(special.ndtr(latent), 1e-15, 1.0 - 1e-12)
        quantiles = special.gammaincinv(shape, quantile_input) * scale
        return float(np.dot(weights, quantiles))

    integral, _ = integrate.quad(
        lambda z: float(stats.norm.pdf(z)) * conditional_at(z),
        threshold,
        threshold + 10.0,
        limit=100,
    )
    return float(integral / accuracy)


def _bias_stats(estimates: np.ndarray, target: float) -> dict[str, Any]:
    """Mean, bias, relative bias, RMSE, and SD against a known target."""
    finite = estimates[np.isfinite(estimates)]
    n_infinite = int(estimates.size - finite.size)
    if finite.size == 0:
        return {
            "mean": None,
            "bias": None,
            "relative_bias": None,
            "rmse": None,
            "sd": None,
            "n_finite": 0,
            "n_infinite": n_infinite,
        }
    mean = float(finite.mean())
    return {
        "mean": mean,
        "bias": mean - target,
        "relative_bias": (mean - target) / target if target != 0 else None,
        "rmse": float(np.sqrt(np.mean((finite - target) ** 2))),
        "sd": float(finite.std(ddof=1)) if finite.size > 1 else 0.0,
        "n_finite": int(finite.size),
        "n_infinite": n_infinite,
    }


def _coverage(lower: np.ndarray, upper: np.ndarray, target: float) -> float:
    return float(np.mean((lower <= target) & (target <= upper)))


def _width_summary(lower: np.ndarray, upper: np.ndarray) -> dict[str, Any]:
    width = upper - lower
    finite = width[np.isfinite(width)]
    return {
        "mean": float(finite.mean()) if finite.size else None,
        "median": float(np.median(finite)) if finite.size else None,
        "n_infinite": int(width.size - finite.size),
    }


def _simulate_ratio_cell(
    *,
    accuracy: float,
    n: int,
    noise: str,
    reps: int,
    bootstrap_reps: int,
    bootstrap_resamples: int,
    seed: int,
    energy_a: float,
    energy_b: float,
    energy_k: int,
    cv: float,
    rho: float,
) -> dict[str, Any]:
    """Run one S1 cell and return its summary."""
    if noise not in {"lognormal", "gamma"}:
        raise ValueError("noise must be 'lognormal' or 'gamma'")
    if not 0.0 < accuracy < 1.0:
        raise ValueError("accuracy must lie in (0, 1)")
    rng = np.random.default_rng(seed)
    mean_j = energy_a + energy_b * energy_k
    threshold = float(stats.norm.ppf(1.0 - accuracy))
    root = math.sqrt(max(0.0, 1.0 - rho * rho))
    latent = rng.standard_normal((reps, n))
    noise_latent = rng.standard_normal((reps, n))
    correct = (latent > threshold).astype(np.int8)
    shared = rho * latent + root * noise_latent
    if noise == "lognormal":
        joules = mean_j * np.exp(cv * shared - 0.5 * cv * cv)
        conditional = _conditional_energy_lognormal(mean_j, cv, rho, accuracy)
    else:
        shape = 1.0 / (cv * cv)
        quantiles = special.ndtr(shared)
        joules = special.gammaincinv(shape, quantiles) * mean_j / shape
        conditional = _conditional_energy_gamma(mean_j, cv, rho, accuracy)

    true_ratio = mean_j / accuracy
    true_mean_of_ratios = accuracy * conditional
    sum_j = joules.sum(axis=1)
    sum_c = correct.sum(axis=1).astype(float)
    sum_correct_j = (joules * correct).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio_estimates = np.where(sum_c > 0, sum_j / sum_c, np.inf)
    mean_of_ratios = sum_correct_j / n
    undefined_rate = float(np.mean(np.any(correct == 0, axis=1)))
    analytic_undefined = float(1.0 - (1.0 - accuracy) ** n)

    standard_error = _delta_standard_errors(joules, correct.astype(float))
    delta_lower = ratio_estimates - Z_975 * standard_error
    delta_upper = ratio_estimates + Z_975 * standard_error
    delta_coverage = _coverage(delta_lower, delta_upper, true_ratio)
    delta_width = _width_summary(delta_lower, delta_upper)

    finite_error = standard_error[np.isfinite(standard_error)]
    finite_ratio = ratio_estimates[np.isfinite(ratio_estimates)]
    se_ratio = (
        float(finite_error.mean() / finite_ratio.std(ddof=1))
        if finite_error.size and finite_ratio.size > 1 and finite_ratio.std(ddof=1) > 0
        else None
    )

    # Cross-check the vectorized SE against the frozen ratio module on a few rows.
    max_delta_diff = 0.0
    for row in range(min(10, reps)):
        reference = ratio_standard_error(joules[row].tolist(), correct[row].tolist())
        candidate = standard_error[row]
        if math.isfinite(reference) and math.isfinite(candidate):
            max_delta_diff = max(max_delta_diff, abs(float(candidate) - float(reference)))

    ratio_variance = (joules * correct).var(axis=1, ddof=1) / n
    mor_se = np.sqrt(ratio_variance)
    mor_lower = mean_of_ratios - Z_975 * mor_se
    mor_upper = mean_of_ratios + Z_975 * mor_se

    boot_reps = max(0, min(bootstrap_reps, reps))
    boot_lower = {"percentile": [], "bca": []}
    boot_upper = {"percentile": [], "bca": []}
    bca_fallbacks = 0
    boot_infinite = 0
    if boot_reps and bootstrap_resamples > 0:
        for row in range(boot_reps):
            index = rng.integers(0, n, size=(bootstrap_resamples, n))
            sample_j = joules[row][index].sum(axis=1)
            sample_c = correct[row][index].sum(axis=1)
            with np.errstate(divide="ignore", invalid="ignore"):
                draws = np.where(sample_c > 0, sample_j / sample_c, np.inf)
            boot_infinite += int(np.isinf(draws).sum())
            percentile_lower, percentile_upper = _percentile_bounds(draws)
            bca_lower, bca_upper, fallback = _bca_bounds(
                draws, joules[row], correct[row].astype(float), float(ratio_estimates[row])
            )
            bca_fallbacks += int(fallback)
            boot_lower["percentile"].append(percentile_lower)
            boot_upper["percentile"].append(percentile_upper)
            boot_lower["bca"].append(bca_lower)
            boot_upper["bca"].append(bca_upper)

    if boot_reps:
        percentile_lower = np.asarray(boot_lower["percentile"])
        percentile_upper = np.asarray(boot_upper["percentile"])
        bca_lower = np.asarray(boot_lower["bca"])
        bca_upper = np.asarray(boot_upper["bca"])
        bootstrap = {
            "reps": int(boot_reps),
            "resamples": int(bootstrap_resamples),
            "coverage": {
                "percentile": _coverage(percentile_lower, percentile_upper, true_ratio),
                "bca": _coverage(bca_lower, bca_upper, true_ratio),
            },
            "mean_width": {
                "percentile": _width_summary(percentile_lower, percentile_upper),
                "bca": _width_summary(bca_lower, bca_upper),
            },
            "bca_fallbacks": int(bca_fallbacks),
            "infinite_resamples": int(boot_infinite),
        }
    else:
        bootstrap = {
            "reps": 0,
            "resamples": int(bootstrap_resamples),
            "coverage": {"percentile": None, "bca": None},
            "mean_width": {"percentile": None, "bca": None},
            "bca_fallbacks": 0,
            "infinite_resamples": 0,
        }

    return {
        "accuracy": accuracy,
        "n": n,
        "noise": noise,
        "reps": reps,
        "mean_j": mean_j,
        "true_e_ratio": true_ratio,
        "true_e_conditional": conditional,
        "true_mean_of_ratios": true_mean_of_ratios,
        "ratio_of_sums": {
            **_bias_stats(ratio_estimates, true_ratio),
            "mean_delta_se": _finite_mean(standard_error),
            "se_ratio": se_ratio,
            "delta_se_max_abs_diff": max_delta_diff,
            "coverage": {
                "delta": delta_coverage,
                "percentile": bootstrap["coverage"]["percentile"],
                "bca": bootstrap["coverage"]["bca"],
            },
            "mean_width": {
                "delta": delta_width,
                "percentile": bootstrap["mean_width"]["percentile"],
                "bca": bootstrap["mean_width"]["bca"],
            },
        },
        "mean_of_ratios": {
            **_bias_stats(mean_of_ratios, true_ratio),
            "bias_vs_own_target": float(mean_of_ratios.mean() - true_mean_of_ratios),
            "relative_bias_vs_own_target": (
                float((mean_of_ratios.mean() - true_mean_of_ratios) / true_mean_of_ratios)
                if true_mean_of_ratios > 0
                else None
            ),
            "coverage_vs_ratio_target": _coverage(mor_lower, mor_upper, true_ratio),
            "coverage_vs_own_target": _coverage(mor_lower, mor_upper, true_mean_of_ratios),
            "mean_width": _width_summary(mor_lower, mor_upper),
            "undefined_rate": undefined_rate,
            "analytic_undefined_rate": analytic_undefined,
        },
        "bootstrap": bootstrap,
    }


def simulate_ratio_study(
    *,
    accuracies: Sequence[float] = S1_ACCURACIES,
    sample_sizes: Sequence[int] = S1_SAMPLE_SIZES,
    noises: Sequence[str] = S1_NOISES,
    reps: int = S1_REPS,
    bootstrap_reps: int = S1_BOOTSTRAP_REPS,
    bootstrap_resamples: int = S1_BOOTSTRAP_RESAMPLES,
    seed: int = DEFAULT_SEED,
    energy_a: float = S1_ENERGY_A,
    energy_b: float = S1_ENERGY_B,
    energy_k: int = S1_ENERGY_K,
    cv: float = S1_ENERGY_CV,
    rho: float = S1_ENERGY_RHO,
) -> dict[str, Any]:
    """Run the S1 ratio-estimator simulation grid.

    Args:
        accuracies: True ``A(k)`` values.
        sample_sizes: Numbers of paired queries.
        noises: ``"lognormal"`` and/or ``"gamma"``.
        reps: Monte Carlo replicates per cell.
        bootstrap_reps: Replicates on which bootstrap intervals are evaluated.
        bootstrap_resamples: Bootstrap resamples per evaluated replicate.
        seed: Base seed.
        energy_a: Energy intercept in joules per query.
        energy_b: Energy slope in joules per query per passage.
        energy_k: Depth used for the S1 energy mean.
        cv: Coefficient of variation of ``J``.
        rho: Shared-latent correlation between energy and correctness.

    Returns:
        A JSON-safe dictionary with metadata and one summary per cell.
    """
    if reps <= 0:
        raise ValueError("reps must be positive")
    if bootstrap_resamples < 0:
        raise ValueError("bootstrap_resamples must be non-negative")
    if not 0.0 <= rho <= 1.0:
        raise ValueError("rho must lie in [0, 1]")
    if cv <= 0:
        raise ValueError("cv must be positive")
    cells: list[dict[str, Any]] = []
    for accuracy_index, accuracy in enumerate(accuracies):
        for size_index, n in enumerate(sample_sizes):
            if n < 3:
                raise ValueError("sample sizes must be at least 3")
            for noise_index, noise in enumerate(noises):
                cell_seed = [seed, 1, accuracy_index, size_index, noise_index]
                cells.append(
                    _simulate_ratio_cell(
                        accuracy=float(accuracy),
                        n=int(n),
                        noise=noise,
                        reps=reps,
                        bootstrap_reps=bootstrap_reps,
                        bootstrap_resamples=bootstrap_resamples,
                        seed=cell_seed,
                        energy_a=energy_a,
                        energy_b=energy_b,
                        energy_k=energy_k,
                        cv=cv,
                        rho=rho,
                    )
                )
    return {
        "study": "S1_ratio_estimator",
        "seed": int(seed),
        "reps": int(reps),
        "bootstrap_reps": int(bootstrap_reps),
        "bootstrap_resamples": int(bootstrap_resamples),
        "note": "Monte Carlo simulation; not an empirical result.",
        "design": {
            "accuracies": [float(value) for value in accuracies],
            "sample_sizes": [int(value) for value in sample_sizes],
            "noises": list(noises),
            "energy_a": float(energy_a),
            "energy_b": float(energy_b),
            "energy_k": int(energy_k),
            "cv": float(cv),
            "rho": float(rho),
            "mean_j": float(energy_a + energy_b * energy_k),
            "estimand": "E[J]/A, with C ~ Bernoulli(A) and J correlated with C",
        },
        "cells": cells,
    }


def _paired_table_probabilities(
    reference_accuracy: float, discordance: float, difference: float
) -> np.ndarray:
    """Return ``[p11, p10, p01, p00]`` for a paired 2x2 table.

    ``p10`` is candidate-correct/reference-wrong and ``p01`` is the reverse.
    """
    if not 0.0 < reference_accuracy < 1.0:
        raise ValueError("reference_accuracy must lie in (0, 1)")
    if not 0.0 < discordance < 1.0:
        raise ValueError("discordance must lie in (0, 1)")
    p10 = (discordance + difference) / 2.0
    p01 = (discordance - difference) / 2.0
    p11 = reference_accuracy - p01
    p00 = 1.0 - p11 - p10 - p01
    probabilities = np.array([p11, p10, p01, p00], dtype=float)
    if np.any(probabilities < -1e-12) or np.any(probabilities > 1.0 + 1e-12):
        raise ValueError("the requested table has an impossible cell probability")
    return np.clip(probabilities, 0.0, 1.0)


def _score_statistics(
    discordant_candidate: np.ndarray,
    discordant_reference: np.ndarray,
    n: int,
    margin: float,
) -> tuple[np.ndarray, np.ndarray]:
    """One-sided score statistic for ``H0: d <= -margin``.

    The null variance fixes the discordant total at its observed value and
    replaces ``d`` by ``-margin``: ``v0 = D/n - margin**2``.
    """
    b = np.asarray(discordant_candidate, dtype=float)
    c = np.asarray(discordant_reference, dtype=float)
    difference = (b - c) / n
    total = (b + c) / n
    variance = total - margin * margin
    with np.errstate(divide="ignore", invalid="ignore"):
        statistic = (difference + margin) / np.sqrt(variance / n)
    statistic = np.where(variance > 0, statistic, np.inf)
    p_value = 1.0 - stats.norm.cdf(statistic)
    return statistic, p_value


def _score_interval(
    discordant_candidate: np.ndarray,
    discordant_reference: np.ndarray,
    n: int,
    confidence: float = 0.95,
) -> tuple[np.ndarray, np.ndarray]:
    """Grid-inverted two-sided score interval for the paired difference."""
    b = np.asarray(discordant_candidate, dtype=float)[:, None]
    c = np.asarray(discordant_reference, dtype=float)[:, None]
    difference = (b - c) / n
    total = (b + c) / n
    grid = np.linspace(-0.25, 0.25, 201)[None, :]
    variance = total - grid * grid
    with np.errstate(divide="ignore", invalid="ignore"):
        statistic = (difference - grid) / np.sqrt(variance / n)
    accepted = (variance > 0) & (np.abs(statistic) <= Z_975)
    any_accepted = accepted.any(axis=1)
    first = accepted.argmax(axis=1)
    last = accepted.shape[1] - 1 - accepted[:, ::-1].argmax(axis=1)
    lower = np.where(any_accepted, grid[0, first], -np.inf)
    upper = np.where(any_accepted, grid[0, last], np.inf)
    return lower, upper


def _simulate_power_cell(
    *,
    n: int,
    difference: float,
    reps: int,
    seed: int,
    margin: float,
    alpha: float,
    reference_accuracy: float,
    discordance: float,
) -> dict[str, Any]:
    """Run one S2 cell."""
    probabilities = _paired_table_probabilities(reference_accuracy, discordance, difference)
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(n, probabilities, size=reps)
    n11 = counts[:, 0]
    n10 = counts[:, 1]
    n01 = counts[:, 2]
    n00 = counts[:, 3]

    z_reject = 0
    p_values: list[float] = []
    lower_bounds: list[float] = []
    standard_errors: list[float] = []
    mean_differences: list[float] = []
    mcnemar_reject = 0
    for row in range(reps):
        candidate = np.concatenate(
            [
                np.ones(n11[row]),
                np.ones(n10[row]),
                np.zeros(n01[row]),
                np.zeros(n00[row]),
            ]
        )
        reference = np.concatenate(
            [
                np.ones(n11[row]),
                np.zeros(n10[row]),
                np.ones(n01[row]),
                np.zeros(n00[row]),
            ]
        )
        result = noninferiority(
            candidate.tolist(),
            reference.tolist(),
            margin=margin,
            alpha=alpha,
        )
        z_reject += int(result.non_inferior)
        if result.p_value is not None:
            p_values.append(float(result.p_value))
        lower_bounds.append(float(result.lower_bound))
        standard_errors.append(float(result.se))
        mean_differences.append(float(result.mean_diff))
        mcnemar_reject += int(result.mcnemar_exact_p < alpha)

    b = n10.astype(float)
    c = n01.astype(float)
    _, score_p = _score_statistics(b, c, n, margin)
    exact_pi = np.where(
        (b + c) > 0,
        ((b + c) / n - margin) / np.maximum(2.0 * (b + c) / n, 1e-12),
        1.0,
    )
    with np.errstate(invalid="ignore"):
        exact_p = stats.binom.sf(b - 1.0, b + c, np.clip(exact_pi, 0.0, 1.0))
    exact_p = np.where((b + c) > 0, exact_p, 1.0)

    lower = np.asarray(lower_bounds)
    standard_error = np.asarray(standard_errors)
    mean_difference = np.asarray(mean_differences)
    wald_lower = mean_difference - Z_975 * standard_error
    wald_upper = mean_difference + Z_975 * standard_error
    score_lower, score_upper = _score_interval(b, c, n)

    return {
        "n": int(n),
        "true_difference": difference,
        "true_difference_pp": 100.0 * difference,
        "reps": int(reps),
        "is_margin_cell": bool(abs(difference + margin) < 1e-12),
        "rejection": {
            "z": z_reject / reps,
            "score": float(np.mean(score_p < alpha)),
            "exact_conditional": float(np.mean(exact_p < alpha)),
        },
        "mean_difference": float(mean_difference.mean()),
        "mean_difference_pp": float(100.0 * mean_difference.mean()),
        "empirical_sd": float(mean_difference.std(ddof=1)),
        "empirical_sd_pp": float(100.0 * mean_difference.std(ddof=1)),
        "mean_se": float(standard_error.mean()),
        "mean_se_pp": float(100.0 * standard_error.mean()),
        "mean_lower_bound_pp": float(100.0 * lower.mean()),
        "coverage": {
            "lower_one_sided": float(np.mean(lower <= difference)),
            "wald_two_sided": _coverage(wald_lower, wald_upper, difference),
            "score_two_sided": _coverage(score_lower, score_upper, difference),
        },
        "mean_width_pp": {
            "wald": float(100.0 * np.mean(wald_upper - wald_lower)),
            "score": float(
                100.0
                * np.mean(
                    score_upper[np.isfinite(score_upper)] - score_lower[np.isfinite(score_lower)]
                )
            )
            if np.isfinite(score_upper).any()
            else None,
        },
        "mcnemar_reject_rate": mcnemar_reject / reps,
        "discordant_probability": float(discordance),
        "table_probabilities": {
            "p11": float(probabilities[0]),
            "p10": float(probabilities[1]),
            "p01": float(probabilities[2]),
            "p00": float(probabilities[3]),
        },
    }


def simulate_power_study(
    *,
    sample_sizes: Sequence[int] = S2_SAMPLE_SIZES,
    differences: Sequence[float] = S2_DIFFERENCES,
    reps: int = S2_REPS,
    seed: int = DEFAULT_SEED + 1,
    margin: float = MARGIN,
    alpha: float = ALPHA,
    reference_accuracy: float = S2_REFERENCE_ACCURACY,
    discordance: float = S2_DISCORDANCE,
) -> dict[str, Any]:
    """Run the S2 non-inferiority test and power simulation grid."""
    if reps <= 0:
        raise ValueError("reps must be positive")
    if margin <= 0:
        raise ValueError("margin must be positive")
    cells: list[dict[str, Any]] = []
    for size_index, n in enumerate(sample_sizes):
        if n < 3:
            raise ValueError("sample sizes must be at least 3")
        for difference_index, difference in enumerate(differences):
            _paired_table_probabilities(reference_accuracy, discordance, float(difference))
            cell_seed = [seed, 2, size_index, difference_index]
            cells.append(
                _simulate_power_cell(
                    n=int(n),
                    difference=float(difference),
                    reps=reps,
                    seed=cell_seed,
                    margin=margin,
                    alpha=alpha,
                    reference_accuracy=reference_accuracy,
                    discordance=discordance,
                )
            )
    return {
        "study": "S2_noninferiority_power",
        "seed": int(seed),
        "reps": int(reps),
        "margin": float(margin),
        "alpha": float(alpha),
        "note": "Monte Carlo simulation; not an empirical result.",
        "design": {
            "sample_sizes": [int(value) for value in sample_sizes],
            "differences_pp": [100.0 * float(value) for value in differences],
            "reference_accuracy": float(reference_accuracy),
            "discordance": float(discordance),
            "null": "H0: d <= -margin; one-sided alpha",
            "type_i_cell": "d = -margin",
        },
        "cells": cells,
    }


def _selection_design(gap: float, margin: float = MARGIN) -> dict[str, Any]:
    """Build a monotone ``A(k)`` and solve the slope for a target E-gap."""
    accuracy = np.asarray(S3_ACCURACY, dtype=float)
    intercept = S3_ENERGY_A
    numerator = intercept * ((1.0 + gap) * accuracy[4] - accuracy[3])
    denominator = 8.0 * accuracy[3] - 4.0 * (1.0 + gap) * accuracy[4]
    if denominator == 0:
        raise ValueError("the requested gap is degenerate")
    slope = numerator / denominator
    if slope <= 0:
        raise ValueError("the requested gap does not admit a positive energy slope")
    energies = intercept + slope * np.asarray(DEPTHS, dtype=float)
    ratio = energies / accuracy
    feasible = accuracy >= accuracy[-1] - margin
    masked = np.where(feasible, ratio, np.inf)
    best = int(np.argmin(masked))
    second = int(np.argsort(masked)[1])
    if DEPTHS[best] != S3_TRUE_DEPTH:
        raise ValueError("the design does not select k=4 as the true optimum")
    return {
        "gap": float(gap),
        "accuracy": [float(value) for value in accuracy],
        "mean_j": [float(value) for value in energies],
        "e_per_correct": [float(value) for value in ratio],
        "feasible": [bool(value) for value in feasible],
        "best_depth": int(DEPTHS[best]),
        "second_depth": int(DEPTHS[second]),
        "second_gap": float(ratio[second] / ratio[best] - 1.0),
        "energy_slope": float(slope),
    }


def _n_star_from_draw(
    *,
    n: int,
    accuracy: np.ndarray,
    mean_j: np.ndarray,
    e_per_correct: np.ndarray,
    selected_depth: int,
    reference_depth: int = 32,
) -> tuple[float | None, float | None]:
    """Call the frozen certification-cost routine on one simulated draw."""
    summaries = []
    for index, depth in enumerate(DEPTHS):
        n_correct = int(round(accuracy[index] * n))
        summaries.append(
            DepthSummary(
                k=int(depth),
                n_valid=int(n),
                n_invalid=0,
                n_correct=n_correct,
                accuracy=float(accuracy[index]),
                mean_j=float(mean_j[index]),
                mean_gpu_j=0.0,
                mean_retrieval_j=0.0,
                e_per_correct=float(e_per_correct[index]),
            )
        )
    result = certification_cost(
        summaries, selected_depth=selected_depth, reference_depth=reference_depth
    )
    return result.get("n_star"), result.get("n_star_exact")


def _bootstrap_selection_probabilities(
    *,
    joules: np.ndarray,
    correct: np.ndarray,
    resamples: int,
    margin: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, float]:
    """Fast paired bootstrap of ``P(k* optimal)`` for one data set.

    ``joules`` and ``correct`` have shape ``(n, 7)``. The return is the
    probability vector over the seven depths plus the probability of no
    feasible depth. The gate uses the resampled ``A(32)``.
    """
    n = joules.shape[0]
    index = rng.integers(0, n, size=(resamples, n))
    sum_j = joules[index].sum(axis=1)
    sum_c = correct[index].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        accuracy = sum_c / n
        e_per_correct = np.where(sum_c > 0, sum_j / sum_c, np.inf)
    feasible = accuracy >= accuracy[:, -1:] - margin
    masked = np.where(feasible, e_per_correct, np.inf)
    best = np.argmin(masked, axis=1)
    none = ~np.isfinite(masked).any(axis=1)
    best[none] = -1
    counts = np.zeros(len(DEPTHS))
    for index_depth in range(len(DEPTHS)):
        counts[index_depth] = float(np.mean(best == index_depth))
    return counts, float(np.mean(none))


def _engine_check(
    *,
    joules: np.ndarray,
    correct: np.ndarray,
    resamples: int,
    margin: float,
    seed: int,
) -> dict[str, Any]:
    """Compare the fast bootstrap with the frozen ``p1.bootstrap`` on one draw."""
    n = joules.shape[0]
    rows: list[dict[str, Any]] = []
    for row in range(n):
        for index, depth in enumerate(DEPTHS):
            rows.append(
                {
                    "question_id": f"q{row:05d}",
                    "k": int(depth),
                    "j_total": float(joules[row, index]),
                    "correct_em": int(correct[row, index]),
                    "valid": 1,
                }
            )
    flat_seed = list(seed) if isinstance(seed, (list, tuple)) else [seed]
    seed_int = int(np.random.SeedSequence(flat_seed).generate_state(1)[0])
    fast_rng = np.random.default_rng([*flat_seed, 99])
    fast_probabilities, fast_none = _bootstrap_selection_probabilities(
        joules=joules,
        correct=correct,
        resamples=resamples,
        margin=margin,
        rng=fast_rng,
    )
    frozen = p1_bootstrap(
        rows,
        resamples=resamples,
        seed=seed_int,
        margin=margin,
        correct_key="em",
        candidate=4,
        reference=32,
        selected_depth=4,
    )
    differences = []
    for index, depth in enumerate(DEPTHS):
        frozen_value = frozen["p_k_optimal"].get(str(depth), 0.0)
        differences.append(abs(float(fast_probabilities[index]) - float(frozen_value)))
    differences.append(abs(fast_none - float(frozen["p_k_optimal"].get("none", 0.0))))
    return {
        "resamples": int(resamples),
        "max_abs_difference": float(max(differences)),
        "note": "Different RNG streams; the difference is Monte Carlo error, not a bias check.",
    }


def _simulate_selection_cell(
    *,
    gap: float,
    n: int,
    reps: int,
    bootstrap_reps: int,
    bootstrap_resamples: int,
    seed: int,
    margin: float,
    cv: float,
    rho_correct: float,
    rho_energy: float,
    engine_check_resamples: int,
) -> dict[str, Any]:
    """Run one S3 cell."""
    design = _selection_design(gap, margin)
    accuracy = np.asarray(design["accuracy"], dtype=float)
    mean_j = np.asarray(design["mean_j"], dtype=float)
    true_e = np.asarray(design["e_per_correct"], dtype=float)
    rng = np.random.default_rng(seed)
    n_depths = len(DEPTHS)
    shared = rng.standard_normal((reps, n))
    sum_j = np.zeros((reps, n_depths))
    n_correct = np.zeros((reps, n_depths), dtype=int)
    boot_reps = max(0, min(bootstrap_reps, reps))
    boot_j = np.zeros((boot_reps, n, n_depths))
    boot_c = np.zeros((boot_reps, n, n_depths), dtype=np.int8)
    root_correct = math.sqrt(max(0.0, 1.0 - rho_correct * rho_correct))
    root_energy = math.sqrt(max(0.0, 1.0 - rho_energy * rho_energy))
    for index, _depth in enumerate(DEPTHS):
        threshold = float(stats.norm.ppf(1.0 - accuracy[index]))
        depth_latent = rng.standard_normal((reps, n))
        latent = rho_correct * shared + root_correct * depth_latent
        correct = (latent > threshold).astype(np.int8)
        energy_latent = rng.standard_normal((reps, n))
        shared_energy = rho_energy * latent + root_energy * energy_latent
        joules = mean_j[index] * np.exp(cv * shared_energy - 0.5 * cv * cv)
        sum_j[:, index] = joules.sum(axis=1)
        n_correct[:, index] = correct.sum(axis=1)
        if boot_reps:
            boot_j[:, :, index] = joules[:boot_reps]
            boot_c[:, :, index] = correct[:boot_reps]

    with np.errstate(divide="ignore", invalid="ignore"):
        accuracy_hat = n_correct / n
        mean_j_hat = sum_j / n
        e_hat = np.where(n_correct > 0, sum_j / np.maximum(n_correct, 1), np.inf)
    feasible = accuracy_hat >= accuracy_hat[:, -1:] - margin
    masked = np.where(feasible, e_hat, np.inf)
    selected = np.argmin(masked, axis=1)
    none = ~np.isfinite(masked).any(axis=1)
    selected[none] = -1
    valid_selected = selected >= 0
    selected_depth = np.array([DEPTHS[index] if index >= 0 else -1 for index in selected])
    true_depth_index = DEPTHS.index(S3_TRUE_DEPTH)
    selection_rate = float(np.mean(selected == true_depth_index))
    selection_counts = {
        str(depth): int(np.sum(selected == index)) for index, depth in enumerate(DEPTHS)
    }
    selection_counts["none"] = int(np.sum(none))

    e_hat_selected = np.where(
        valid_selected, e_hat[np.arange(reps), np.maximum(selected, 0)], np.nan
    )
    e_true_selected = np.where(valid_selected, true_e[np.maximum(selected, 0)], np.nan)
    a_true_selected = np.where(valid_selected, accuracy[np.maximum(selected, 0)], np.nan)
    a_hat_selected = np.where(
        valid_selected, accuracy_hat[np.arange(reps), np.maximum(selected, 0)], np.nan
    )
    winner_curse = e_hat_selected - e_true_selected
    regret = e_true_selected - true_e[true_depth_index]

    n_star_values: list[float] = []
    n_star_exact_values: list[float] = []
    n_star_true_values: list[float] = []
    n_star_true_exact_values: list[float] = []
    n_star_oracle_values: list[float] = []
    n_star_oracle_exact_values: list[float] = []
    for row in range(reps):
        if selected[row] < 0:
            continue
        depth = int(selected_depth[row])
        hat_n_star, hat_exact = _n_star_from_draw(
            n=n,
            accuracy=accuracy_hat[row],
            mean_j=mean_j_hat[row],
            e_per_correct=e_hat[row],
            selected_depth=depth,
        )
        true_n_star, true_exact = _n_star_from_draw(
            n=n,
            accuracy=accuracy,
            mean_j=mean_j,
            e_per_correct=true_e,
            selected_depth=depth,
        )
        oracle_n_star, oracle_exact = _n_star_from_draw(
            n=n,
            accuracy=accuracy,
            mean_j=mean_j,
            e_per_correct=true_e,
            selected_depth=S3_TRUE_DEPTH,
        )
        n_star_values.append(float(hat_n_star) if hat_n_star is not None else math.nan)
        n_star_exact_values.append(float(hat_exact) if hat_exact is not None else math.nan)
        n_star_true_values.append(float(true_n_star) if true_n_star is not None else math.nan)
        n_star_true_exact_values.append(float(true_exact) if true_exact is not None else math.nan)
        n_star_oracle_values.append(float(oracle_n_star) if oracle_n_star is not None else math.nan)
        n_star_oracle_exact_values.append(
            float(oracle_exact) if oracle_exact is not None else math.nan
        )

    n_star = np.asarray(n_star_values)
    n_star_exact = np.asarray(n_star_exact_values)
    n_star_true = np.asarray(n_star_true_values)
    n_star_true_exact = np.asarray(n_star_true_exact_values)
    defined = np.isfinite(n_star) & np.isfinite(n_star_true) & (n_star_true > 0)
    relative_bias = (
        float(np.mean((n_star[defined] - n_star_true[defined]) / n_star_true[defined]))
        if defined.any()
        else None
    )
    rmse = (
        float(np.sqrt(np.mean((n_star[defined] - n_star_true[defined]) ** 2)))
        if defined.any()
        else None
    )
    exact_defined = np.isfinite(n_star_exact) & np.isfinite(n_star_true_exact)
    exact_relative_bias = (
        float(
            np.mean(
                (n_star_exact[exact_defined] - n_star_true_exact[exact_defined])
                / n_star_true_exact[exact_defined]
            )
        )
        if exact_defined.any()
        else None
    )
    exact_rmse = (
        float(
            np.sqrt(np.mean((n_star_exact[exact_defined] - n_star_true_exact[exact_defined]) ** 2))
        )
        if exact_defined.any()
        else None
    )
    both = (
        np.isfinite(n_star)
        & np.isfinite(n_star_exact)
        & np.isfinite(n_star_true)
        & np.isfinite(n_star_true_exact)
    )
    correlation = (
        float(np.corrcoef(n_star[both], n_star_exact[both])[0, 1]) if both.sum() > 1 else None
    )
    ratio_exact_approx = float(np.mean(n_star_exact[both] / n_star[both])) if both.any() else None
    oracle = np.asarray(n_star_oracle_values)
    oracle_defined = np.isfinite(n_star) & np.isfinite(oracle) & (oracle > 0)
    relative_bias_vs_oracle = (
        float(np.mean((n_star[oracle_defined] - oracle[oracle_defined]) / oracle[oracle_defined]))
        if oracle_defined.any()
        else None
    )

    p_true_values = []
    p_max_values = []
    bootstrap_selected = []
    bootstrap_counts = np.zeros(n_depths)
    boot_none = 0.0
    if boot_reps and bootstrap_resamples > 0:
        for row in range(boot_reps):
            probabilities, none_probability = _bootstrap_selection_probabilities(
                joules=boot_j[row],
                correct=boot_c[row],
                resamples=bootstrap_resamples,
                margin=margin,
                rng=rng,
            )
            bootstrap_counts += probabilities
            boot_none += none_probability
            p_true_values.append(probabilities[true_depth_index])
            p_max_values.append(float(probabilities.max()))
            bootstrap_selected.append(int(np.argmax(probabilities)) == true_depth_index)
        p_true = np.asarray(p_true_values)
        p_max = np.asarray(p_max_values)
        p_k_optimal_mean = {
            str(depth): float(bootstrap_counts[index] / boot_reps)
            for index, depth in enumerate(DEPTHS)
        }
        p_k_optimal_mean["none"] = float(boot_none / boot_reps)
        bootstrap = {
            "reps": int(boot_reps),
            "resamples": int(bootstrap_resamples),
            "p_true_mean": float(p_true.mean()),
            "p_true_sd": float(p_true.std(ddof=1)) if p_true.size > 1 else 0.0,
            "p_true_q05": float(np.quantile(p_true, 0.05)),
            "p_true_q95": float(np.quantile(p_true, 0.95)),
            "p_max_mean": float(p_max.mean()),
            "map_selection_rate": float(np.mean(bootstrap_selected)),
            "k3_pass_rate": float(np.mean(p_true >= 0.8)),
            "brier": float(np.mean((p_true - (selected[:boot_reps] == true_depth_index)) ** 2)),
            "p_k_optimal_mean": p_k_optimal_mean,
        }
    else:
        bootstrap = {
            "reps": 0,
            "resamples": int(bootstrap_resamples),
            "p_true_mean": None,
            "p_true_sd": None,
            "p_true_q05": None,
            "p_true_q95": None,
            "p_max_mean": None,
            "map_selection_rate": None,
            "k3_pass_rate": None,
            "brier": None,
            "p_k_optimal_mean": {},
        }

    check: dict[str, Any] | None = None
    if engine_check_resamples > 0 and boot_reps:
        check = _engine_check(
            joules=boot_j[0],
            correct=boot_c[0],
            resamples=engine_check_resamples,
            margin=margin,
            seed=seed,
        )

    return {
        "gap": float(gap),
        "n": int(n),
        "reps": int(reps),
        "true_best_depth": S3_TRUE_DEPTH,
        "true_best_e": float(true_e[true_depth_index]),
        "true_second_depth": design["second_depth"],
        "true_second_gap": design["second_gap"],
        "energy_slope": design["energy_slope"],
        "selection_rate": selection_rate,
        "selection_counts": selection_counts,
        "mean_selected_depth": float(np.mean(selected[valid_selected]))
        if valid_selected.any()
        else None,
        "winner_curse": {
            "mean_e_bias": float(np.nanmean(winner_curse)),
            "relative_e_bias": float(np.nanmean(winner_curse / e_true_selected)),
            "mean_accuracy_bias": float(np.nanmean(a_hat_selected - a_true_selected)),
            "mean_regret": float(np.nanmean(regret)),
            "relative_regret": float(np.nanmean(regret / true_e[true_depth_index])),
        },
        "n_star": {
            "defined_rate": float(defined.mean()) if n_star.size else None,
            "relative_bias": relative_bias,
            "rmse": rmse,
            "relative_bias_vs_oracle": relative_bias_vs_oracle,
            "exact_relative_bias": exact_relative_bias,
            "exact_rmse": exact_rmse,
            "corr_exact_approx": correlation,
            "mean_ratio_exact_to_approx": ratio_exact_approx,
            "mean_estimate": _finite_mean(n_star),
            "mean_true": _finite_mean(n_star_true),
            "mean_exact_estimate": _finite_mean(n_star_exact),
            "mean_true_exact": _finite_mean(n_star_true_exact),
            "mean_oracle": _finite_mean(oracle),
        },
        "bootstrap": bootstrap,
        "engine_check": check,
    }


def simulate_selection_study(
    *,
    gaps: Sequence[float] = S3_GAPS,
    sample_sizes: Sequence[int] = S3_SAMPLE_SIZES,
    reps: int = S3_REPS,
    bootstrap_reps: int = S3_BOOTSTRAP_REPS,
    bootstrap_resamples: int = S3_BOOTSTRAP_RESAMPLES,
    seed: int = DEFAULT_SEED + 2,
    margin: float = MARGIN,
    cv: float = S3_ENERGY_CV,
    rho_correct: float = S3_RHO_CORRECT,
    rho_energy: float = S3_RHO_ENERGY,
    engine_check_resamples: int = 80,
) -> dict[str, Any]:
    """Run the S3 selection/certification simulation grid."""
    if reps <= 0:
        raise ValueError("reps must be positive")
    if bootstrap_resamples < 0:
        raise ValueError("bootstrap_resamples must be non-negative")
    if not 0.0 <= rho_correct <= 1.0 or not 0.0 <= rho_energy <= 1.0:
        raise ValueError("correlations must lie in [0, 1]")
    designs = [_selection_design(float(gap), margin) for gap in gaps]
    cells: list[dict[str, Any]] = []
    for gap_index, gap in enumerate(gaps):
        for size_index, n in enumerate(sample_sizes):
            if n < 10:
                raise ValueError("sample sizes must be at least 10")
            cell_seed = [seed, 3, gap_index, size_index]
            cells.append(
                _simulate_selection_cell(
                    gap=float(gap),
                    n=int(n),
                    reps=reps,
                    bootstrap_reps=bootstrap_reps,
                    bootstrap_resamples=bootstrap_resamples,
                    seed=cell_seed,
                    margin=margin,
                    cv=cv,
                    rho_correct=rho_correct,
                    rho_energy=rho_energy,
                    engine_check_resamples=engine_check_resamples,
                )
            )
    return {
        "study": "S3_selection_and_certification",
        "seed": int(seed),
        "reps": int(reps),
        "bootstrap_reps": int(bootstrap_reps),
        "bootstrap_resamples": int(bootstrap_resamples),
        "margin": float(margin),
        "note": "Monte Carlo simulation; not an empirical result.",
        "design": {
            "depths": list(DEPTHS),
            "accuracies": [float(value) for value in S3_ACCURACY],
            "gaps": designs,
            "cv": float(cv),
            "rho_correct": float(rho_correct),
            "rho_energy": float(rho_energy),
        },
        "cells": cells,
    }


def _format_pct(value: Any, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, str):
        return value
    return f"{100.0 * float(value):.{digits}f}%"


def _format_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, str):
        return value
    return f"{float(value):,.{digits}f}"


def render_report(
    ratio_study: dict[str, Any],
    power_study: dict[str, Any],
    selection_study: dict[str, Any],
) -> str:
    """Render a compact Markdown report from the three study payloads."""
    lines = [
        "# Simulation studies (CPU-only)",
        "",
        "**These are Monte Carlo simulations, not empirical results.** They exercise the",
        "frozen estimators on synthetic data and do not re-adjudicate any gate. All numbers",
        "below are generated by `scripts/19_simulations.py` from the JSON files in this",
        "directory.",
        "",
        "Seeds: "
        f"S1 `{ratio_study['seed']}`, S2 `{power_study['seed']}`, S3 `{selection_study['seed']}`. "
        f"Replicates: S1 {ratio_study['reps']}, S2 {power_study['reps']}, "
        f"S3 {selection_study['reps']}.",
        "",
        "## S1 - ratio estimator",
        "",
        "Paired `(J, C)` with `C ~ Bernoulli(A)` and `J` from a lognormal or gamma copula.",
        "The estimand is `E[J]/A`. `mean-of-ratios` is the all-query mean of `J_i/C_i`",
        "(a failure contributes zero), which targets `A * E[J|C=1]`, not `E[J]/A`.",
        "",
        "| noise | A | n | rel. bias | RMSE | delta cov. | pct. cov. | BCa cov. |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in ratio_study["cells"]:
        estimate = cell["ratio_of_sums"]
        lines.append(
            f"| {cell['noise']} | {cell['accuracy']:.2f} | {cell['n']} | "
            f"{_format_pct(estimate['relative_bias'])} | "
            f"{_format_number(estimate['rmse'], 2)} | "
            f"{_format_pct(estimate['coverage']['delta'])} | "
            f"{_format_pct(estimate['coverage']['percentile'])} | "
            f"{_format_pct(estimate['coverage']['bca'])} |"
        )
    lines.extend(
        [
            "",
            "Mean-of-ratios bias against the ratio target (same grid):",
            "",
            "| noise | A | n | bias vs `E[J]/A` | rel. bias | cov. of ratio target |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for cell in ratio_study["cells"]:
        estimate = cell["mean_of_ratios"]
        lines.append(
            f"| {cell['noise']} | {cell['accuracy']:.2f} | {cell['n']} | "
            f"{_format_number(estimate['bias'], 2)} | "
            f"{_format_pct(estimate['relative_bias'])} | "
            f"{_format_pct(estimate['coverage_vs_ratio_target'])} |"
        )
    lines.extend(
        [
            "",
            "The all-query mean of `J_i/C_i` is undefined whenever any query fails; the",
            "analytic undefined probability is `1-(1-A)^n`. The table's mean-of-ratios",
            "estimator uses the 0-for-failure convention and is therefore finite, but it",
            "estimates a different quantity. Its own-target coverage is in `s1.json`.",
            "",
            "## S2 - non-inferiority test",
            "",
            "Paired binary outcomes with a 12% discordant-pair rate and 50% reference accuracy.",
            "The margin is 5 pp; `d = -5 pp` is the type-I cell. `z` is the frozen paired test,",
            "`score` fixes the null variance, and `exact` is a conditional binomial sensitivity.",
            "",
            "| n | d (pp) | z reject | score reject | exact reject | Wald cov. | score cov. |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for cell in power_study["cells"]:
        lines.append(
            f"| {cell['n']} | {cell['true_difference_pp']:+.0f} | "
            f"{_format_pct(cell['rejection']['z'])} | "
            f"{_format_pct(cell['rejection']['score'])} | "
            f"{_format_pct(cell['rejection']['exact_conditional'])} | "
            f"{_format_pct(cell['coverage']['wald_two_sided'])} | "
            f"{_format_pct(cell['coverage']['score_two_sided'])} |"
        )
    lines.extend(
        [
            "",
            "Rejection at `d = -5 pp` is the type-I rate; the other rows are power. The",
            "one-sided lower-bound coverage is in `s2.json`.",
            "",
            "## S3 - selection and certification",
            "",
            "Seven depths, known `A(k)` and `E(k)`, with the 5 pp gate. The design solves the",
            "energy slope so the best (`k=4`) and second-best (`k=8`) feasible depths have the",
            "requested true `E` gap. `P(k*)` is the fast paired bootstrap probability of the",
            "true depth.",
            "",
            "| gap | n | selection rate | mean P(k*) | K3 pass | winner's curse | N* rel. bias | N* exact rel. bias |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for cell in selection_study["cells"]:
        lines.append(
            f"| {_format_pct(cell['true_second_gap'])} | {cell['n']} | "
            f"{_format_pct(cell['selection_rate'])} | "
            f"{_format_pct(cell['bootstrap']['p_true_mean'])} | "
            f"{_format_pct(cell['bootstrap']['k3_pass_rate'])} | "
            f"{_format_number(cell['winner_curse']['mean_e_bias'], 2)} | "
            f"{_format_pct(cell['n_star']['relative_bias'])} | "
            f"{_format_pct(cell['n_star']['exact_relative_bias'])} |"
        )
    lines.extend(
        [
            "",
            "Winner's curse is `E_hat(k_hat) - E_true(k_hat)` in J/correct; a negative value",
            "means the selected depth looks cheaper than it is. `N*` is the frozen",
            "certification-cost break-even; it is descriptive and not a deployment guarantee.",
            "The exact column is the frozen per-query-energy variant.",
            "",
            "## Caveats",
            "",
            "- The generative models are stylized. The lognormal and gamma copulas are not",
            "  calibrated to any measured energy distribution; the pilot slope and intercept",
            "  are inputs, not claims.",
            "- S1 bootstrap coverage uses a subset of replicates because each replicate needs",
            "  its own bootstrap. The point-estimator bias and RMSE use every replicate.",
            "- S2's exact conditional sensitivity estimates the discordant probability from",
            "  the same table; it is a sensitivity, not an exact non-inferiority test.",
            "- S3 generates paired depths with a shared question latent, but the fast bootstrap",
            "  and the certification-cost calculation use the same frozen formulas as P1.",
            "  Cross-depth dependence in real runs may differ from the simulation.",
            "- Monte Carlo error is not zero. At 2,000 replicates, a coverage near 0.95 has a",
            "  standard error of about 0.5 pp; at 400 bootstrap replicates it is about 1 pp.",
            "- These studies say nothing about the P1-P4 empirical outcomes and must not be",
            "  cited as evidence for or against any claim in the paper.",
            "",
        ]
    )
    return "\n".join(lines)


def write_simulation_outputs(
    out_dir: Path,
    ratio_study: dict[str, Any],
    power_study: dict[str, Any],
    selection_study: dict[str, Any],
) -> list[Path]:
    """Write ``s1.json``, ``s2.json``, ``s3.json`` and ``report.md``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, payload in (
        ("s1", ratio_study),
        ("s2", power_study),
        ("s3", selection_study),
    ):
        path = out_dir / f"{name}.json"
        path.write_text(
            json.dumps(_json_safe(payload), indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        written.append(path)
    report = out_dir / "report.md"
    report.write_text(
        render_report(ratio_study, power_study, selection_study),
        encoding="utf-8",
        newline="\n",
    )
    written.append(report)
    return written
