"""Answer normalization and correctness rules.

The primary correctness rule is normalized exact match (EM), matching the
pre-registration. Lenient span match and token F1 are secondary and must be
reported alongside EM; the pilot showed that strict EM can decide the green
verdict, so the scoring rule is a sensitivity axis, not an implementation detail.

Standard library only.
"""

from __future__ import annotations

import re
import string
from collections import Counter

_ARTICLE_RE = re.compile(r"\b(a|an|the)\b", re.UNICODE)


def normalize_answer(text: str) -> str:
    """Lowercase, strip punctuation and articles, collapse whitespace.

    This follows the SQuAD evaluation convention closely enough for
    comparability, but the exact rule is frozen in the preregistration.
    """
    lowered = text.lower()
    without_punct = "".join(ch for ch in lowered if ch not in string.punctuation)
    without_articles = _ARTICLE_RE.sub(" ", without_punct)
    return " ".join(without_articles.split())


def exact_match(prediction: str, gold: str) -> bool:
    """Primary correctness: normalized prediction equals normalized gold."""
    return normalize_answer(prediction) == normalize_answer(gold)


def lenient_span_match(prediction: str, gold: str) -> bool:
    """Secondary correctness: the normalized gold appears in the prediction.

    This tolerates answers such as "Denver linebacker Von Miller" for gold
    "Von Miller", which strict EM penalizes.
    """
    gold_norm = normalize_answer(gold)
    return bool(gold_norm) and gold_norm in normalize_answer(prediction)


def token_f1(prediction: str, gold: str) -> float:
    """Token-level F1 over normalized tokens, with the standard empty rule."""
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = Counter(pred_tokens) & Counter(gold_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def correctness(prediction: str, gold: str, rule: str = "normalized_em") -> int:
    """Return 1/0 for the named correctness rule."""
    if rule == "normalized_em":
        return int(exact_match(prediction, gold))
    if rule == "lenient_span":
        return int(lenient_span_match(prediction, gold))
    if rule == "token_f1_ge_0.5":
        return int(token_f1(prediction, gold) >= 0.5)
    raise ValueError(f"unknown correctness rule: {rule!r}")
