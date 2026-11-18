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
    "wh_what",
    "wh_who",
    "wh_when",
    "wh_where",
    "wh_which",
    "wh_why",
    "wh_how",
    "wh_other",
)

WH_TYPES: tuple[str, ...] = ("what", "who", "when", "where", "which", "why", "how")


@dataclass(frozen=True)
class PolicyExample:
    """One training example. Features must be available before generation."""

    question_id: str
    question: str
    bm25_scores: Sequence[float]
    best_depth: int
    correct_by_depth: dict[int, int]
    energy_by_depth: dict[int, float]
    wh_type: str = ""


def featurize(example: PolicyExample, query_length: int | None = None) -> dict[str, float]:
    """Build the policy feature vector from BM25 scores and question shape."""
    features = score_features(example.bm25_scores)
    features["question_words"] = float(
        query_length if query_length is not None else len(example.question.split())
    )
    wh = example.wh_type.strip().lower()
    if wh not in WH_TYPES:
        wh = "other"
    for name in WH_TYPES:
        features[f"wh_{name}"] = 1.0 if wh == name else 0.0
    features["wh_other"] = 1.0 if wh == "other" else 0.0
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
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if not train:
        raise ValueError("train must not be empty")
    depths = tuple(sorted(train[0].correct_by_depth))
    models: dict[int, Any] = {}
    for depth in depths:
        x = [_feature_vector(example) for example in train]
        y = [int(example.correct_by_depth[depth]) for example in train]
        if len(set(y)) < 2:
            models[depth] = float(sum(y) / len(y))
            continue
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, random_state=seed),
        )
        model.fit(x, y)
        models[depth] = model
    return DepthPolicy(models=models, depths=depths)


def _predict_correct(policy: DepthPolicy, example: PolicyExample, depth: int) -> float:
    model = policy.models.get(depth)
    if model is None:
        return 0.0
    if isinstance(model, float):
        return model
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


def matched_oracle_evaluation(
    test: Sequence[PolicyExample], static_depth: int, *, allow_abstention: bool = True
) -> dict[str, float]:
    """Hindsight oracle constrained to the static depth's accuracy.

    Start every question at its cheapest allowed depth, then pay the smallest
    extra energy needed to make exactly ``C`` questions correct, where ``C`` is
    the number correct at ``static_depth``. With ``allow_abstention=False``, the
    cheapest allowed depth is ``k >= 1``.
    """
    if not test:
        raise ValueError("test must not be empty")
    target_correct = sum(int(example.correct_by_depth[static_depth]) for example in test)
    allowed = {
        depth
        for example in test
        for depth in example.energy_by_depth
        if allow_abstention or depth >= 1
    }
    if not allowed:
        raise ValueError("no allowed depths")
    base_by_example = [
        min(
            (
                example.energy_by_depth[depth]
                for depth in allowed
                if depth in example.energy_by_depth
            ),
            default=float("inf"),
        )
        for example in test
    ]
    base_j = sum(base_by_example)
    extras: list[float] = []
    for example, base in zip(test, base_by_example, strict=True):
        correct_costs = [
            example.energy_by_depth[depth] - base
            for depth, correct in example.correct_by_depth.items()
            if correct and depth in allowed
        ]
        if correct_costs:
            extras.append(min(correct_costs))
    if len(extras) < target_correct:
        raise ValueError("not enough questions with a correct depth for matched oracle")
    extras.sort()
    total_j = base_j + sum(extras[:target_correct])
    return {
        "n": float(len(test)),
        "accuracy": target_correct / len(test),
        "total_j": total_j,
        "energy_per_correct": total_j / target_correct if target_correct else float("inf"),
        "mean_depth": float("nan"),
        "allow_abstention": allow_abstention,
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
