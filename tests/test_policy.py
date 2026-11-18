"""Tests for the query-conditional depth policy."""

from __future__ import annotations

import pytest

pytest.importorskip("sklearn")

from rag_energy.stats.policy import (
    PolicyExample,
    evaluate_policy,
    oracle_evaluation,
    oracle_gain_pct,
    static_evaluation,
    train_policy,
)


def _examples(start: int, n: int) -> list[PolicyExample]:
    examples = []
    for i in range(start, start + n):
        # Alternate easy/hard questions; deeper depths help the hard ones.
        hard = i % 2 == 0
        scores = [3.0, 0.5, 0.1] if hard else [5.0, 4.0, 1.0]
        correct = {0: 0, 1: int(hard), 2: 1}
        energy = {0: 10.0, 1: 20.0, 2: 30.0}
        examples.append(
            PolicyExample(
                question_id=str(i),
                question="a question with some words",
                bm25_scores=scores,
                best_depth=2,
                correct_by_depth=correct,
                energy_by_depth=energy,
            )
        )
    return examples


def test_static_and_oracle_evaluations() -> None:
    test = _examples(0, 10)
    static = static_evaluation(test, 2)
    oracle = oracle_evaluation(test)
    assert static["accuracy"] == 1.0
    assert oracle["accuracy"] == 1.0
    assert oracle["total_j"] <= static["total_j"]
    assert oracle_gain_pct(static["energy_per_correct"], oracle["energy_per_correct"]) >= 0


def test_policy_trains_and_evaluates() -> None:
    train = _examples(0, 40)
    validation = _examples(40, 20)
    test = _examples(60, 20)
    policy = train_policy(train, validation)
    result = evaluate_policy(policy, test, static_depth=2, threshold=0.5)
    assert result["n"] == 20
    assert 0.0 <= result["accuracy"] <= 1.0
    assert result["energy_per_correct"] > 0


def test_threshold_falls_back_to_static() -> None:
    train = _examples(0, 40)
    validation = _examples(40, 20)
    test = _examples(60, 20)
    policy = train_policy(train, validation)
    # A threshold above 1.0 is invalid; at 1.0 no probability clears it, so the
    # policy must equal the static depth exactly.
    result = evaluate_policy(policy, test, static_depth=2, threshold=1.0)
    static = static_evaluation(test, 2)
    assert result["accuracy"] == static["accuracy"]
    assert result["total_j"] == static["total_j"]
