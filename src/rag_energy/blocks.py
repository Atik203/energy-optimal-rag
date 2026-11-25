"""Block-design energy estimator (Phase 7).

The per-query window estimator is falsified: the window sum recovers only about
82% of a continuous replay total, and the bias depends on the preceding depth.
This module implements the replacement the prediction needs:

* :func:`build_block_plan` - a randomized schedule of ``(depth, replicate)``
  blocks;
* :func:`depth_totals` - energy and correct counts per depth;
* :func:`energy_per_correct` - the ratio of sums;
* :func:`savings` - ``1 - E(candidate)/E(reference)``;
* :func:`bootstrap_savings` - cluster bootstrap that resamples whole blocks;
* :func:`cv_by_depth` - block-to-block coefficient of variation.

Everything here is pure and CPU-only so it can be tested without a GPU.
Energies are joules, accuracies are proportions in ``[0, 1]``, depths are
integers.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class BlockPlanItem:
    """One scheduled block. ``order`` is the execution position."""

    order: int
    k: int
    replicate: int


@dataclass(frozen=True)
class BlockObservation:
    """One completed block: integrated energy and answers for ``n`` questions."""

    k: int
    replicate: int
    energy_j: float
    correct: int
    n: int
    duration_s: float = 0.0

    def __post_init__(self) -> None:
        if self.k < 0:
            raise ValueError("depth must be non-negative")
        if self.energy_j < 0:
            raise ValueError("block energy must be non-negative")
        if not 0 <= self.correct <= self.n:
            raise ValueError("correct must lie in [0, n]")
        if self.n <= 0:
            raise ValueError("block must contain at least one question")


def build_block_plan(
    depths: Sequence[int],
    replicates: int,
    *,
    seed: int,
) -> list[BlockPlanItem]:
    """Return a randomized schedule with ``replicates`` blocks per depth.

    Randomizing the block order prevents thermal drift from being confounded
    with depth. The schedule is deterministic given ``seed``.
    """
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if not depths:
        raise ValueError("depths must not be empty")
    items = [(int(k), replicate) for k in depths for replicate in range(replicates)]
    random.Random(seed).shuffle(items)
    return [BlockPlanItem(order=i, k=k, replicate=r) for i, (k, r) in enumerate(items)]


def depth_totals(blocks: Sequence[BlockObservation]) -> dict[int, dict[str, float]]:
    """Sum energy and correct answers per depth and return ratio-of-sums energy."""
    totals: dict[int, dict[str, float]] = {}
    for block in blocks:
        entry = totals.setdefault(block.k, {"energy_j": 0.0, "correct": 0, "n": 0, "blocks": 0})
        entry["energy_j"] += block.energy_j
        entry["correct"] += block.correct
        entry["n"] += block.n
        entry["blocks"] += 1
    for entry in totals.values():
        entry["energy_per_correct"] = (
            entry["energy_j"] / entry["correct"] if entry["correct"] else math.inf
        )
        entry["accuracy"] = entry["correct"] / entry["n"] if entry["n"] else 0.0
    return totals


def energy_per_correct(blocks: Sequence[BlockObservation], depth: int) -> float:
    """Ratio of sums ``sum(J) / sum(C)`` at one depth, in J per correct answer."""
    totals = depth_totals(blocks)
    if depth not in totals:
        raise ValueError(f"no blocks at depth {depth}")
    return float(totals[depth]["energy_per_correct"])


def savings(blocks: Sequence[BlockObservation], candidate: int, reference: int) -> float:
    """Fractional energy saving of ``candidate`` against ``reference``.

    Returns a proportion in ``[0, 1]`` for a saving and a negative value when
    the candidate is more expensive.
    """
    reference_cost = energy_per_correct(blocks, reference)
    if not math.isfinite(reference_cost) or reference_cost <= 0:
        raise ValueError("reference energy per correct must be finite and positive")
    return 1.0 - energy_per_correct(blocks, candidate) / reference_cost


def cv_by_depth(blocks: Sequence[BlockObservation]) -> dict[int, dict[str, float]]:
    """Block-to-block coefficient of variation of energy per query."""
    grouped: dict[int, list[float]] = {}
    for block in blocks:
        grouped.setdefault(block.k, []).append(block.energy_j / block.n)
    out: dict[int, dict[str, float]] = {}
    for depth, values in grouped.items():
        if len(values) < 2:
            out[depth] = {"mean_j_per_query": values[0], "sd": 0.0, "cv": 0.0, "n_blocks": 1}
            continue
        mean = sum(values) / len(values)
        var = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
        sd = math.sqrt(var)
        out[depth] = {
            "mean_j_per_query": mean,
            "sd": sd,
            "cv": sd / mean if mean else math.inf,
            "n_blocks": len(values),
        }
    return out


def _cluster_resample(
    blocks: Sequence[BlockObservation], rng: random.Random
) -> list[BlockObservation]:
    """Resample blocks with replacement inside each depth."""
    grouped: dict[int, list[BlockObservation]] = {}
    for block in blocks:
        grouped.setdefault(block.k, []).append(block)
    out: list[BlockObservation] = []
    for _depth, members in grouped.items():
        for _ in range(len(members)):
            out.append(rng.choice(members))
    return out


def bootstrap_savings(
    blocks: Sequence[BlockObservation],
    candidate: int,
    reference: int,
    *,
    resamples: int = 2000,
    seed: int = 20261115,
) -> dict[str, float | list[float] | int]:
    """Cluster bootstrap over blocks for the savings estimate.

    Blocks are resampled with replacement within each depth, which propagates
    block-to-block variance into the ratio. Returns the point estimate, the 95%
    percentile interval, and the number of finite resamples.
    """
    if resamples <= 0:
        raise ValueError("resamples must be positive")
    point = savings(blocks, candidate, reference)
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(resamples):
        sample = _cluster_resample(blocks, rng)
        try:
            value = savings(sample, candidate, reference)
        except (ValueError, ZeroDivisionError):
            continue
        if math.isfinite(value):
            draws.append(value)
    if not draws:
        return {"point": point, "ci": [math.nan, math.nan], "n_valid": 0}
    draws.sort()

    def quantile(q: float) -> float:
        position = q * (len(draws) - 1)
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return draws[lower]
        weight = position - lower
        return draws[lower] * (1 - weight) + draws[upper] * weight

    return {
        "point": point,
        "ci": [quantile(0.025), quantile(0.975)],
        "n_valid": len(draws),
    }


def convergence(
    blocks: Sequence[BlockObservation],
    candidate: int,
    reference: int,
    *,
    alternative_savings_pct: float,
    tolerance_pp: float = 3.0,
) -> dict[str, object]:
    """Compare the block estimate with a sweep or replay estimate.

    Reports the gap in percentage points and whether it is inside the
    pre-specified tolerance (G7 uses 3 pp).
    """
    block_saving = 100.0 * savings(blocks, candidate, reference)
    gap = abs(block_saving - alternative_savings_pct)
    return {
        "block_savings_pct": block_saving,
        "alternative_savings_pct": alternative_savings_pct,
        "gap_pp": gap,
        "tolerance_pp": tolerance_pp,
        "agrees": gap <= tolerance_pp,
    }
