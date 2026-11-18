"""Tests for HotpotQA supporting-paragraph retrieval recall."""

from __future__ import annotations

import pytest

pytest.importorskip("pandas")
pytest.importorskip("rank_bm25")

import pandas as pd

from rag_energy.retrieval.index import RetrievalIndex
from rag_energy.retrieval.recall import hotpot_recall


def _corpus() -> pd.DataFrame:
    rows = []
    for qid, words in (
        ("h1", ["apple apple", "banana", "carrot", "date"]),
        ("h2", ["zebra zebra", "yak", "xylophone", "wombat"]),
    ):
        for index, text in enumerate(words):
            rows.append(
                {
                    "passage_id": f"hotpot:{qid}:{index}",
                    "qid": qid,
                    "title": f"T{index}",
                    "text": text,
                    "is_gold": index < 2,
                }
            )
    return pd.DataFrame(rows)


def _questions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "qid": "h1",
                "question": "apple",
                "gold": "x",
                "type": "bridge",
                "level": "easy",
                "n_paragraphs": 4,
                "n_gold_paragraphs": 2,
            },
            {
                "qid": "h2",
                "question": "zebra",
                "gold": "y",
                "type": "comparison",
                "level": "medium",
                "n_paragraphs": 4,
                "n_gold_paragraphs": 2,
            },
        ]
    )


def test_recall_is_perfect_when_gold_terms_are_distinctive() -> None:
    corpus = _corpus()
    index = RetrievalIndex.from_corpus(corpus)
    per_question, aggregate = hotpot_recall(index, _questions(), corpus, [1, 2, 4])
    assert set(per_question["k"]) == {1, 2, 4}
    # At k=4 every question has both gold paragraphs.
    at4 = per_question[per_question["k"] == 4]
    assert (at4["recall"] == 1.0).all()
    assert (at4["all_gold"]).all()
    agg4 = aggregate[aggregate["k"] == 4].iloc[0]
    assert agg4["mean_recall"] == 1.0
    assert agg4["all_gold_rate"] == 1.0


def test_recall_at_one_can_miss_a_gold_paragraph() -> None:
    corpus = _corpus()
    index = RetrievalIndex.from_corpus(corpus)
    per_question, _ = hotpot_recall(index, _questions(), corpus, [1])
    # With two gold paragraphs and k=1, no question can have all gold.
    assert not per_question["all_gold"].any()
    assert (per_question["n_retrieved_gold"] <= 1).all()


def test_zero_k_returns_empty_retrieval() -> None:
    corpus = _corpus()
    index = RetrievalIndex.from_corpus(corpus)
    per_question, _ = hotpot_recall(index, _questions(), corpus, [0, 2])
    at0 = per_question[per_question["k"] == 0]
    assert (at0["n_retrieved_gold"] == 0).all()
    assert (at0["recall"] == 0.0).all()


def test_validation_errors() -> None:
    corpus = _corpus()
    index = RetrievalIndex.from_corpus(corpus)
    with pytest.raises(ValueError):
        hotpot_recall(index, _questions(), corpus, [])
    with pytest.raises(ValueError):
        hotpot_recall(index, _questions(), corpus, [1, 1])
    with pytest.raises(ValueError):
        hotpot_recall(index, _questions(), corpus, [-1, 2])
    # Remove gold markers to trigger missing-gold validation.
    bad = corpus.copy()
    bad["is_gold"] = False
    with pytest.raises(ValueError, match="without gold"):
        hotpot_recall(index, _questions(), bad, [2])


def test_aggregate_has_expected_columns() -> None:
    corpus = _corpus()
    index = RetrievalIndex.from_corpus(corpus)
    _, aggregate = hotpot_recall(index, _questions(), corpus, [2])
    assert list(aggregate.columns) == [
        "k",
        "n_questions",
        "mean_recall",
        "all_gold_rate",
        "min_recall",
        "max_recall",
    ]
    assert aggregate.iloc[0]["n_questions"] == 2
