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

FEATURE_NAMES: tuple[str, ...] = (
    "top",
    "second",
    "gap",
    "mean",
    "std",
    "entropy",
    "n_positive",
    "question_words",
)


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


def _feature_vector(example: PolicyExample) -> list[float]:
    features = featurize(example)
    return [features[name] for name in FEATURE_NAMES]


def oracle_gain_pct(static_energy: float, oracle_energy: float) -> float:
    """Oracle energy gain over the best static depth, in percent."""
    if static_energy <= 0:
        raise ValueError("static_energy must be positive")
    return 100.0 * (1.0 - oracle_energy / static_energy)


def cheapest_correct_depth(example: PolicyExample) -> int:
    """Hindsight oracle: cheapest depth that answers correctly, else cheapest."""
    correct = [k for k, c in example.correct_by_depth.items() if c]
    pool = correct or list(example.energy_by_depth)
    return min(pool, key=lambda k: example.energy_by_depth[k])


@dataclass(frozen=True)
class DepthPolicy:
    """Per-depth correctness models used by the cost-sensitive policy."""

    models: dict[int, Any]
    depths: tuple[int, ...]


def train_policy(
    train: Sequence[PolicyExample],
    validation: Sequence[PolicyExample],
    seed: int = 20261115,
    max_depth: int = 32,
) -> DepthPolicy:
    """Train one small logistic model per depth.

    Each model predicts whether the reader answers correctly at that depth from
    pre-generation features. The policy then picks the cheapest depth whose
    predicted correctness clears a threshold. The validation split is used only
    to choose that threshold, never the model parameters.
    """
    from sklearn.linear_model import LogisticRegression

    if not train:
        raise ValueError("train must not be empty")
    depths = tuple(sorted(train[0].correct_by_depth))
    models: dict[int, Any] = {}
    for depth in depths:
        x = [_feature_vector(example) for example in train]
        y = [int(example.correct_by_depth[depth]) for example in train]
        if len(set(y)) < 2:
            models[depth] = None
            continue
        model = LogisticRegression(max_iter=1000, random_state=seed)
        model.fit(x, y)
        models[depth] = model
    return DepthPolicy(models=models, depths=depths)


def _predict_correct(policy: DepthPolicy, example: PolicyExample, depth: int) -> float:
    model = policy.models.get(depth)
    if model is None:
        values = [int(e.correct_by_depth[depth]) for e in [example]]
        return float(values[0])
    return float(model.predict_proba([_feature_vector(example)])[0, 1])


def _predict(policy: DepthPolicy, example: PolicyExample, threshold: float) -> int | None:
    for depth in policy.depths:
        if _predict_correct(policy, example, depth) >= threshold:
            return depth
    return None


def policy_energy(example: PolicyExample, depth: int) -> float:
    """Energy contributed by one policy decision."""
    return float(example.energy_by_depth[depth])


def policy_correct(example: PolicyExample, depth: int) -> int:
    """Correctness contributed by one policy decision."""
    return int(example.correct_by_depth[depth])


def evaluate_policy(
    policy: Any,
    test: Sequence[PolicyExample],
    static_depth: int,
    threshold: float = 0.0,
) -> dict[str, float]:
    """Evaluate a policy at a confidence threshold.

    Depths below ``threshold`` fall back to ``static_depth``. Energy is the
    ratio of sums ``sum(J) / sum(correct)``.
    """
    if not test:
        raise ValueError("test must not be empty")
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError("threshold must lie in [0, 1]")
    depths: list[int] = []
    for example in test:
        depth = _predict(policy, example, threshold)
        depths.append(static_depth if depth is None else depth)
    total_j = sum(
        policy_energy(example, depth) for example, depth in zip(test, depths, strict=True)
    )
    total_correct = sum(
        policy_correct(example, depth) for example, depth in zip(test, depths, strict=True)
    )
    accuracy = total_correct / len(test)
    energy_per_correct = total_j / total_correct if total_correct else float("inf")
    return {
        "n": float(len(test)),
        "accuracy": accuracy,
        "total_j": total_j,
        "energy_per_correct": energy_per_correct,
        "mean_depth": sum(depths) / len(depths),
        "threshold": threshold,
    }


def oracle_evaluation(test: Sequence[PolicyExample]) -> dict[str, float]:
    """Hindsight oracle: cheapest correct depth per question."""
    if not test:
        raise ValueError("test must not be empty")
    depths = [cheapest_correct_depth(example) for example in test]
    total_j = sum(
        policy_energy(example, depth) for example, depth in zip(test, depths, strict=True)
    )
    total_correct = sum(
        policy_correct(example, depth) for example, depth in zip(test, depths, strict=True)
    )
    return {
        "n": float(len(test)),
        "accuracy": total_correct / len(test),
        "total_j": total_j,
        "energy_per_correct": total_j / total_correct if total_correct else float("inf"),
        "mean_depth": sum(depths) / len(depths),
    }


def static_evaluation(test: Sequence[PolicyExample], depth: int) -> dict[str, float]:
    """Evaluate one fixed depth on the same examples."""
    total_j = sum(policy_energy(example, depth) for example in test)
    total_correct = sum(policy_correct(example, depth) for example in test)
    return {
        "n": float(len(test)),
        "accuracy": total_correct / len(test),
        "total_j": total_j,
        "energy_per_correct": total_j / total_correct if total_correct else float("inf"),
        "depth": float(depth),
    }
