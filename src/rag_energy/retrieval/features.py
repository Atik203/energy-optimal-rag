"""Query features for the query-conditional depth policy.

Features are computed from the BM25 score distribution only, so they are
available before generation and cost almost nothing. The policy must not use
the gold answer or any post-generation signal.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def score_features(scores: Sequence[float]) -> dict[str, float]:
    """Summarize a BM25 score vector.

    Returns:
        ``top``, ``second``, ``gap`` (top - second), ``mean``, ``std``,
        ``entropy`` of the softmax over scores, and ``n_positive``.
    """
    if not scores:
        return {
            "top": 0.0,
            "second": 0.0,
            "gap": 0.0,
            "mean": 0.0,
            "std": 0.0,
            "entropy": 0.0,
            "n_positive": 0.0,
        }

    ordered = sorted((float(s) for s in scores), reverse=True)
    top = ordered[0]
    second = ordered[1] if len(ordered) > 1 else 0.0
    mean = sum(ordered) / len(ordered)
    variance = sum((s - mean) ** 2 for s in ordered) / len(ordered)

    # Softmax with a max-shift for numerical stability.
    exps = [math.exp(s - top) for s in ordered]
    total = sum(exps)
    probs = [e / total for e in exps]
    entropy = -sum(p * math.log(p) for p in probs if p > 0.0)

    return {
        "top": top,
        "second": second,
        "gap": top - second,
        "mean": mean,
        "std": math.sqrt(variance),
        "entropy": entropy,
        "n_positive": float(sum(1 for s in ordered if s > 0.0)),
    }
