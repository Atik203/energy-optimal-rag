"""Deterministic question splits.

Splits are assigned by hashing the question ID with the project seed, so the
same ID always lands in the same split regardless of file order. This is
required for the policy's 600/200/200 train/validation/test split.
"""

from __future__ import annotations

import hashlib

BUCKETS = 10_000


def stable_bucket(question_id: str, seed: int, buckets: int = BUCKETS) -> int:
    """Map a question ID to a stable bucket in ``[0, buckets)``."""
    if buckets <= 0:
        raise ValueError("buckets must be positive")
    payload = f"{seed}:{question_id}".encode()
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:16], 16) % buckets


def assign_split(
    question_id: str,
    seed: int,
    train: float = 0.6,
    validation: float = 0.2,
    test: float = 0.2,
) -> str:
    """Assign ``"train"``, ``"validation"``, or ``"test"`` deterministically."""
    if min(train, validation, test) < 0:
        raise ValueError("split fractions must be non-negative")
    total = train + validation + test
    if abs(total - 1.0) > 1e-9:
        raise ValueError("split fractions must sum to 1")

    position = stable_bucket(question_id, seed) / BUCKETS
    if position < train:
        return "train"
    if position < train + validation:
        return "validation"
    return "test"
