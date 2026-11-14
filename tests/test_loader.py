"""Prepared-data loader tests: split order, missing IDs, and limits."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("pyarrow")

import pandas as pd

from rag_energy.data.loader import load_squad_split


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
