"""Unit tests for BM25 query features and the CPU retrieval energy proxy.

Standard library plus pytest only: no numpy, pandas, torch, or GPU. The proxy is
an upper bound by construction and is never asserted to be a measurement.
"""

from __future__ import annotations

import math

import pytest

from rag_energy.retrieval.features import score_features
from rag_energy.retrieval.proxy_energy import (
    DEFAULT_WATTS,
    cpu_retrieval_joules,
    proxy_share,
)

FEATURE_KEYS = {"top", "second", "gap", "mean", "std", "entropy", "n_positive"}


def test_score_features_empty_returns_zero_dict_with_all_keys() -> None:
    features = score_features([])
    assert set(features) == FEATURE_KEYS
    assert all(value == 0.0 for value in features.values())


def test_score_features_known_vector() -> None:
    features = score_features([3.0, 1.0, 0.0])
    assert set(features) == FEATURE_KEYS
    assert features["top"] == pytest.approx(3.0)
    assert features["second"] == pytest.approx(1.0)
    assert features["gap"] == pytest.approx(2.0)
    assert features["mean"] == pytest.approx(4.0 / 3.0)
    # population variance = ((5/3)^2 + (1/3)^2 + (4/3)^2) / 3 = 14/9
    assert features["std"] == pytest.approx(math.sqrt(14.0 / 9.0))
    # softmax probs proportional to (1, e^-2, e^-3); H = -sum p ln p
    assert features["entropy"] == pytest.approx(0.5242666167276728)
    assert features["n_positive"] == 2.0


def test_score_features_is_order_invariant() -> None:
    assert score_features([0.0, 3.0, 1.0]) == pytest.approx(score_features([3.0, 1.0, 0.0]))


def test_score_features_single_score_has_zero_spread_and_entropy() -> None:
    features = score_features([5.0])
    assert features["top"] == pytest.approx(5.0)
    assert features["second"] == 0.0
    assert features["gap"] == pytest.approx(5.0)
    assert features["std"] == pytest.approx(0.0)
    assert features["entropy"] == pytest.approx(0.0)
    assert features["n_positive"] == 1.0


def test_score_features_tied_top_scores_have_zero_gap() -> None:
    features = score_features([2.0, 2.0])
    assert features["top"] == pytest.approx(2.0)
    assert features["second"] == pytest.approx(2.0)
    assert features["gap"] == pytest.approx(0.0)


def test_score_features_counts_only_positive_scores() -> None:
    assert score_features([3.0, 0.0, -1.0])["n_positive"] == 1.0
    assert score_features([-1.0, -2.0])["n_positive"] == 0.0


def test_cpu_retrieval_joules_uses_default_watts() -> None:
    assert DEFAULT_WATTS == 20.0
    assert cpu_retrieval_joules(2.0) == pytest.approx(40.0)


def test_cpu_retrieval_joules_accepts_custom_watts() -> None:
    assert cpu_retrieval_joules(2.0, watts=10.0) == pytest.approx(20.0)
    assert cpu_retrieval_joules(0.0) == 0.0


def test_cpu_retrieval_joules_rejects_negative_seconds() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        cpu_retrieval_joules(-0.1)


@pytest.mark.parametrize("watts", [0.0, -20.0])
def test_cpu_retrieval_joules_rejects_non_positive_watts(watts: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        cpu_retrieval_joules(1.0, watts=watts)


def test_proxy_share_matches_pilot_point() -> None:
    # 3.11 / (3.11 + 86.0) = 0.034900...
    assert proxy_share(3.11, 86.0) == pytest.approx(0.0349, abs=1e-4)


def test_proxy_share_is_one_half_for_equal_energy() -> None:
    assert proxy_share(1.0, 1.0) == pytest.approx(0.5)


@pytest.mark.parametrize(("cpu", "gpu"), [(0.0, 0.0), (-5.0, 1.0), (1.0, -5.0)])
def test_proxy_share_rejects_non_positive_total(cpu: float, gpu: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        proxy_share(cpu, gpu)
