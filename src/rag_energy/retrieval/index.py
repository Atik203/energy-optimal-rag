"""Retrieval dispatch for global and per-question corpora.

SQuAD builds one index over a shared corpus. HotpotQA distractor supplies 10
paragraphs per question and must not pool paragraphs across questions, so it
builds one small index per question. Both are built once per run; rebuilding
per query would contaminate the retrieval-energy accounting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag_energy.retrieval.bm25 import BM25Index, RetrievedPassage, build_index


@dataclass
class RetrievalIndex:
    """One global index or one index per question, searched by question id."""

    global_index: BM25Index | None = None
    grouped: dict[str, BM25Index] = field(default_factory=dict)

    @classmethod
    def from_corpus(cls, corpus: Any) -> RetrievalIndex:
        """Build from a dataframe with ``passage_id`` and ``text``.

        A ``qid`` column selects the grouped per-question layout.
        """
        columns = getattr(corpus, "columns", [])
        if "qid" in columns:
            grouped: dict[str, BM25Index] = {}
            for qid, group in corpus.groupby("qid", sort=True):
                grouped[str(qid)] = build_index(
                    zip(group["passage_id"], group["text"], strict=True)
                )
            if not grouped:
                raise ValueError("grouped corpus has no questions")
            return cls(grouped=grouped)
        pairs = list(zip(corpus["passage_id"], corpus["text"], strict=True))
        return cls(global_index=build_index(pairs))

    def search(self, question_id: str, query: str, k: int) -> list[RetrievedPassage]:
        """Search the corpus that belongs to ``question_id``."""
        if self.grouped:
            index = self.grouped.get(str(question_id))
            if index is None:
                raise ValueError(f"no retrieval index for question {question_id!r}")
        else:
            index = self.global_index
        if index is None:
            raise ValueError("retrieval index is empty")
        return index.search(query, k)

    @property
    def scope(self) -> str:
        return "per_question" if self.grouped else "global"
