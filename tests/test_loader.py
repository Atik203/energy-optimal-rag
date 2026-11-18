"""Prepared-data loader tests: split order, missing IDs, and limits."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("pyarrow")

import pandas as pd

from rag_energy.data.loader import (
    load_hotpot_split,
    load_prepared_split,
    load_squad_split,
)


def _write_processed(tmp_path: Path, ids: list[str]) -> Path:
    processed = tmp_path / "processed"
    processed.mkdir()
    questions = pd.DataFrame(
        [
            {
                "qid": "q1",
                "question": "What is one?",
                "gold": "alpha",
                "wh_type": "what",
                "context_id": "c1",
                "title": "A",
            },
            {
                "qid": "q2",
                "question": "When is two?",
                "gold": "beta",
                "wh_type": "when",
                "context_id": "c1",
                "title": "A",
            },
            {
                "qid": "q3",
                "question": "Who is three?",
                "gold": "gamma",
                "wh_type": "who",
                "context_id": "c2",
                "title": "B",
            },
        ]
    )
    corpus = pd.DataFrame(
        [
            {"passage_id": "p1", "context_id": "c1", "text": "alpha beta"},
            {"passage_id": "p2", "context_id": "c2", "text": "gamma"},
        ]
    )
    questions.to_parquet(processed / "squad_questions.parquet", index=False)
    corpus.to_parquet(processed / "squad_corpus.parquet", index=False)
    (processed / "squad_splits.json").write_text(
        json.dumps({"splits": {"p0_golden": ids}}), encoding="utf-8"
    )
    return processed


def test_load_squad_split_preserves_id_order(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path, ["q3", "q1"])

    split = load_squad_split(processed, "p0_golden")

    assert split.name == "p0_golden"
    assert tuple(split.questions["qid"]) == ("q3", "q1")
    assert len(split.corpus) == 2
    assert split.ids == ("q3", "q1")


def test_load_squad_split_honors_limit(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path, ["q3", "q1", "q2"])

    split = load_squad_split(processed, "p0_golden", limit=2)

    assert tuple(split.questions["qid"]) == ("q3", "q1")
    assert split.ids == ("q3", "q1")


def test_load_squad_split_rejects_missing_split(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path, ["q1"])

    with pytest.raises(ValueError, match="p1_primary"):
        load_squad_split(processed, "p1_primary")


def test_load_squad_split_rejects_missing_question(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path, ["q1", "missing"])

    with pytest.raises(ValueError, match="missing"):
        load_squad_split(processed, "p0_golden")


def test_load_squad_split_rejects_duplicate_ids(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path, ["q1", "q1"])

    with pytest.raises(ValueError, match="duplicate"):
        load_squad_split(processed, "p0_golden")


def _write_hotpot_processed(tmp_path: Path, ids: list[str]) -> Path:
    processed = tmp_path / "hotpot"
    processed.mkdir()
    questions = pd.DataFrame(
        [
            {
                "qid": qid,
                "question": f"Question {qid}?",
                "gold": f"answer-{qid}",
                "type": "bridge",
                "level": "hard",
                "n_paragraphs": 10,
                "n_gold_paragraphs": 2,
            }
            for qid in ("h1", "h2", "h3")
        ]
    )
    corpus = pd.DataFrame(
        [
            {
                "passage_id": f"hotpot:{qid}:{index}",
                "qid": qid,
                "title": f"T{qid}-{index}",
                "text": f"text {qid} {index}",
                "is_gold": index < 2,
            }
            for qid in ("h1", "h2", "h3")
            for index in range(10)
        ]
    )
    questions.to_parquet(processed / "hotpot_questions.parquet", index=False)
    corpus.to_parquet(processed / "hotpot_corpus.parquet", index=False)
    (processed / "hotpot_splits.json").write_text(
        json.dumps({"splits": {"hotpot": ids}}), encoding="utf-8"
    )
    return processed


def test_load_hotpot_split_preserves_order_and_limit(tmp_path: Path) -> None:
    processed = _write_hotpot_processed(tmp_path, ["h2", "h1", "h3"])
    split = load_hotpot_split(processed, "hotpot", limit=2)
    assert split.ids == ("h2", "h1")
    assert tuple(split.questions["qid"]) == ("h2", "h1")
    assert len(split.corpus) == 30

    split = load_prepared_split(processed, "hotpot", "hotpot")
    assert split.ids == ("h2", "h1", "h3")
    assert split.corpus["qid"].nunique() == 3


def test_load_hotpot_split_rejects_a_question_without_ten_paragraphs(tmp_path: Path) -> None:
    processed = _write_hotpot_processed(tmp_path, ["h1"])
    corpus = pd.read_parquet(processed / "hotpot_corpus.parquet")
    corpus = corpus[~((corpus["qid"] == "h1") & (corpus["passage_id"].str.endswith(":9")))]
    corpus.to_parquet(processed / "hotpot_corpus.parquet", index=False)

    with pytest.raises(ValueError, match="exactly 10 paragraphs"):
        load_hotpot_split(processed, "hotpot")
