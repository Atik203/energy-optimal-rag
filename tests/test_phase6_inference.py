"""Tests for the Phase 6 inference-repair helpers (CPU-only, synthetic input)."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "phase6_inference", ROOT / "scripts" / "21_phase6_inference.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def phase6():
    return _load()


def test_cluster_robust_matches_iid_when_one_question_per_cluster(phase6):
    values = [1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 0.0]
    clusters = [f"c{i}" for i in range(len(values))]
    stats = phase6._cluster_robust_mean(values, clusters)
    assert stats["n_clusters"] == len(values)
    assert stats["mean"] == pytest.approx(sum(values) / len(values))
    # With singleton clusters the design effect is ~1.
    assert stats["design_effect"] == pytest.approx(1.0, abs=1e-9)


def test_cluster_robust_inflates_variance_within_cluster_correlation(phase6):
    # Two clusters, each internally constant: strong intra-cluster correlation.
    values = [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    clusters = ["a", "a", "a", "a", "b", "b", "b", "b"]
    stats = phase6._cluster_robust_mean(values, clusters)
    assert stats["mean"] == pytest.approx(0.5)
    assert stats["design_effect"] > 1.0
    assert stats["se_cluster"] > stats["se_iid"]


def test_cluster_robust_single_cluster_falls_back_to_iid(phase6):
    stats = phase6._cluster_robust_mean([1.0, 0.0, 1.0], ["only", "only", "only"])
    assert stats["n_clusters"] == 1
    assert stats["se_cluster"] == pytest.approx(stats["se_iid"])


def test_ols_recovers_exact_line(phase6):
    x = np.column_stack([np.ones(5), np.arange(5, dtype=float)])
    y = 3.0 + 2.0 * np.arange(5, dtype=float)
    fit = phase6._ols(x, y)
    assert fit["beta"] == pytest.approx([3.0, 2.0])
    assert fit["r2"] == pytest.approx(1.0)
    assert fit["rmse"] == pytest.approx(0.0, abs=1e-12)


def test_ols_information_criteria_order_by_fit(phase6):
    x = np.column_stack([np.ones(6), np.arange(6, dtype=float)])
    good = phase6._ols(x, 1.0 + 0.5 * np.arange(6, dtype=float))
    noisy = phase6._ols(x, np.array([1.0, 2.0, 1.0, 3.0, 2.0, 5.0]))
    assert good["bic"] < noisy["bic"]


def test_cluster_se_is_finite(phase6):
    x = np.column_stack([np.ones(4), np.arange(4, dtype=float)])
    y = np.array([1.0, 2.1, 2.9, 4.2])
    fit = phase6._ols(x, y)
    se = phase6._cluster_se(x, fit["resid"], np.asarray(fit["beta"]), ["a", "a", "b", "b"])
    assert len(se) == 2
    assert all(math.isfinite(value) and value >= 0 for value in se)
