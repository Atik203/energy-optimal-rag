"""Tests for global and per-question retrieval dispatch."""

from __future__ import annotations

import pytest

pytest.importorskip("pandas")
pytest.importorskip("rank_bm25")

import pandas as pd

from rag_energy.retrieval.index import RetrievalIndex


def _grouped_corpus() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "passage_id": f"hotpot:{qid}:{index}",
                "qid": qid,
                "title": f"T{index}",
                "text": text,
                "is_gold": index < 2,
            }
            for qid, words in (
                ("h1", ["apple", "apple orchard", "banana", "carrot"]),
                ("h2", ["zebra", "zebra stripe", "yak", "xylophone"]),
            )
            for index, text in enumerate(words)
        ]
    )


def test_grouped_index_never_searches_another_question() -> None:
    index = RetrievalIndex.from_corpus(_grouped_corpus())

    hits = index.search("h1", "apple orchard", 4)

    assert hits
    assert hits[0].passage_id == "hotpot:h1:1"
    assert all(hit.passage_id.startswith("hotpot:h1:") for hit in hits)
    assert index.scope == "per_question"


def test_grouped_index_rejects_an_unknown_question() -> None:
    index = RetrievalIndex.from_corpus(_grouped_corpus())

    with pytest.raises(ValueError, match="no retrieval index"):
        index.search("missing", "apple", 1)


def test_global_index_ignores_the_question_id() -> None:
    corpus = pd.DataFrame(
        [
            {"passage_id": "p1", "context_id": "c1", "text": "alpha beta"},
            {"passage_id": "p2", "context_id": "c2", "text": "gamma delta"},
            {"passage_id": "p3", "context_id": "c3", "text": "epsilon zeta"},
            {"passage_id": "p4", "context_id": "c4", "text": "eta theta"},
        ]
    )
    index = RetrievalIndex.from_corpus(corpus)

    hits = index.search("any-question", "gamma", 1)

    assert [hit.passage_id for hit in hits] == ["p2"]
    assert index.scope == "global"
