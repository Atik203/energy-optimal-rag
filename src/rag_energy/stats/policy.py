"""Query-conditional depth policy.

The policy maps pre-generation query features to a depth. It is trained on 600
questions, tuned on 200, and evaluated once on 200 held-out questions at matched
accuracy against the best static depth. The oracle is an upper bound; the
learned policy is the result.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from rag_energy.retrieval.features import score_features


@dataclass(frozen=True)
class PolicyExample:
    """One training example. Features must be available before generation."""

    question_id: str
    question: str
    bm25_scores: Sequence[float]
    best_depth: int
    correct_by_depth: dict[int, int]
    energy_by_depth: dict[int, float]


def featurize(example: PolicyExample, query_length: int | None = None) -> dict[str, float]:
    """Build the policy feature vector from BM25 scores and question shape."""
    features = score_features(example.bm25_scores)
    features["question_words"] = float(
        query_length if query_length is not None else len(example.question.split())
    )
    return features


def oracle_gain_pct(static_energy: float, oracle_energy: float) -> float:
    """Oracle energy gain over the best static depth, in percent."""
    if static_energy <= 0:
        raise ValueError("static_energy must be positive")
    return 100.0 * (1.0 - oracle_energy / static_energy)


def train_policy(
    train: Sequence[PolicyExample],
    validation: Sequence[PolicyExample],
    seed: int = 20261115,
    max_depth: int = 32,
) -> Any:
    """Train the depth policy. Implemented in P3.

    The model must be simple and auditable (cost-sensitive classifier or small
    decision tree). No test-set tuning.
    """
    raise NotImplementedError("train_policy is implemented in P3; see ROADMAP.md P3.")


def evaluate_policy(policy: Any, test: Sequence[PolicyExample]) -> dict[str, float]:
    """Evaluate a policy at matched accuracy. Implemented in P3."""
    raise NotImplementedError("evaluate_policy is implemented in P3.")
