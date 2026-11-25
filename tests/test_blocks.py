"""Tests for the Phase 7 block-design estimator (stdlib only)."""

from __future__ import annotations

import pytest

from rag_energy.blocks import (
    BlockObservation,
    bootstrap_savings,
    build_block_plan,
    convergence,
    cv_by_depth,
    depth_totals,
    energy_per_correct,
    savings,
)


def _blocks():
    """Four depths, two replicates each, exactly 100 J and 5/10 correct."""
    out = []
    for k, energy, correct in [(1, 100.0, 5), (4, 120.0, 6), (8, 180.0, 6), (32, 300.0, 6)]:
        for replicate in range(2):
            out.append(
                BlockObservation(
                    k=k,
                    replicate=replicate,
                    energy_j=energy,
                    correct=correct,
                    n=10,
                    duration_s=60.0,
                )
            )
    return out


def test_plan_is_deterministic_and_balanced():
    first = build_block_plan([0, 1, 4], replicates=3, seed=7)
    second = build_block_plan([0, 1, 4], replicates=3, seed=7)
    assert [(i.k, i.replicate) for i in first] == [(i.k, i.replicate) for i in second]
    assert [i.order for i in first] == list(range(9))
    for depth in (0, 1, 4):
        assert sum(1 for i in first if i.k == depth) == 3


def test_plan_changes_with_seed():
    a = [(i.k, i.replicate) for i in build_block_plan([0, 1, 4], 3, seed=1)]
    b = [(i.k, i.replicate) for i in build_block_plan([0, 1, 4], 3, seed=2)]
    assert a != b


def test_plan_rejects_bad_input():
    with pytest.raises(ValueError):
        build_block_plan([], 3, seed=1)
    with pytest.raises(ValueError):
        build_block_plan([1], 0, seed=1)


def test_depth_totals_ratio_of_sums():
    totals = depth_totals(_blocks())
    assert totals[1]["energy_j"] == pytest.approx(200.0)
    assert totals[1]["correct"] == 10
    assert totals[1]["energy_per_correct"] == pytest.approx(20.0)
    assert totals[1]["accuracy"] == pytest.approx(0.5)


def test_energy_per_correct_missing_depth():
    with pytest.raises(ValueError):
        energy_per_correct(_blocks(), 2)


def test_savings_matches_ratio_of_sums():
    blocks = _blocks()
    expected = 1 - (120.0 / 6) / (300.0 / 6)
    assert savings(blocks, 4, 32) == pytest.approx(expected)


def test_savings_negative_when_candidate_costs_more():
    assert savings(_blocks(), 8, 4) < 0


def test_savings_rejects_zero_reference():
    blocks = [
        BlockObservation(k=4, replicate=0, energy_j=10.0, correct=0, n=10),
        BlockObservation(k=32, replicate=0, energy_j=10.0, correct=0, n=10),
    ]
    with pytest.raises(ValueError):
        savings(blocks, 4, 32)


def test_cv_by_depth_zero_when_blocks_identical():
    cv = cv_by_depth(_blocks())
    assert cv[4]["cv"] == pytest.approx(0.0)
    assert cv[4]["n_blocks"] == 2


def test_bootstrap_interval_brackets_point():
    result = bootstrap_savings(_blocks(), 4, 32, resamples=500, seed=3)
    low, high = result["ci"]
    assert low <= result["point"] <= high
    assert result["n_valid"] > 0


def test_bootstrap_is_deterministic():
    a = bootstrap_savings(_blocks(), 4, 32, resamples=200, seed=11)
    b = bootstrap_savings(_blocks(), 4, 32, resamples=200, seed=11)
    assert a == b


def test_convergence_flag():
    result = convergence(_blocks(), 4, 32, alternative_savings_pct=58.0, tolerance_pp=3.0)
    assert result["agrees"] is True
    far = convergence(_blocks(), 4, 32, alternative_savings_pct=80.0, tolerance_pp=3.0)
    assert far["agrees"] is False
