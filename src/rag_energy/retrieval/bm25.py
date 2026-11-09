"""BM25 retrieval over chunked passages.

Pilot configuration: ``rank_bm25.BM25Okapi``, lowercase alphanumeric tokens,
index built once, top-32. The index must be built once per run; rebuilding it
per query would contaminate the retrieval-energy accounting.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokenizer used by the pilot."""
    return _TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class RetrievedPassage:
    passage_id: str
    text: str
    score: float
    rank: int


class BM25Index:
    """Thin wrapper around ``rank_bm25.BM25Okapi``.

    Import of ``rank_bm25`` is deferred so the package can be imported in a
    dependency-light environment.
    """

    def __init__(self, passages: Sequence[tuple[str, str]]) -> None:
        """Build an index from ``(passage_id, text)`` pairs."""
        from rank_bm25 import BM25Okapi  # noqa: PLC0415 (optional dependency)

        self._ids = [passage_id for passage_id, _ in passages]
        self._texts = [text for _, text in passages]
        self._bm25 = BM25Okapi([tokenize(text) for text in self._texts])

    def search(self, query: str, k: int) -> list[RetrievedPassage]:
        """Return the top-``k`` passages with scores in rank order."""
        if k < 0:
            raise ValueError("k must be non-negative")
        if k == 0:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [
            RetrievedPassage(
                passage_id=self._ids[i],
                text=self._texts[i],
                score=float(scores[i]),
                rank=rank,
            )
            for rank, i in enumerate(order, start=1)
        ]


def build_index(passages: Iterable[tuple[str, str]]) -> BM25Index:
    """Convenience constructor."""
    return BM25Index(list(passages))
