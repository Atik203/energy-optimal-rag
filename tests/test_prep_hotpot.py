"""Tests for HotpotQA distractor preparation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_energy.data.prep_hotpot import prepare_hotpot


def _question(qid: str, *, n_paragraphs: int, qtype: str = "bridge") -> dict:
    return {
        "id": qid,
        "question": f"Question {qid}?",
        "answer": f"answer-{qid}",
        "type": qtype,
        "level": "hard",
        "supporting_facts": [[f"T{qid}-0", 0], [f"T{qid}-1", 0]],
        "context": [
            [f"T{qid}-{index}", [f"Paragraph {index} of {qid}."]] for index in range(n_paragraphs)
        ],
    }


def _write_json(path: Path, questions: list[dict]) -> Path:
    path.write_text(json.dumps(questions), encoding="utf-8")
    return path


def _dataset() -> list[dict]:
    questions = [
        _question("q1", n_paragraphs=10, qtype="bridge"),
        _question("q2", n_paragraphs=10, qtype="bridge"),
        _question("q3", n_paragraphs=10, qtype="bridge"),
        _question("q4", n_paragraphs=10, qtype="comparison"),
        _question("q5", n_paragraphs=3, qtype="bridge"),
        _question("q6", n_paragraphs=2, qtype="comparison"),
    ]
    return questions


def test_prepare_hotpot_keeps_whole_paragraphs_and_writes_outputs(tmp_path: Path) -> None:
    raw = _write_json(tmp_path / "hotpot.json", _dataset())

    manifest_path = prepare_hotpot(
        raw,
        tmp_path / "processed",
        n_questions=4,
        seed=7,
        splits_out=tmp_path / "hotpot_splits.json",
    )

    summary = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert summary["counts"]["n_questions_total"] == 6
    assert summary["counts"]["n_questions_frame"] == 4
    assert summary["counts"]["n_questions"] == 4
    assert summary["counts"]["n_passages"] == 40
    assert summary["corpus"]["n_contexts"] == 4
    assert summary["corpus"]["passage_words"] is None

    import pandas as pd

    questions = pd.read_parquet(tmp_path / "processed" / "hotpot_questions.parquet")
    corpus = pd.read_parquet(tmp_path / "processed" / "hotpot_corpus.parquet")
    assert set(questions["qid"]) == {"q1", "q2", "q3", "q4"}
    assert (questions["n_paragraphs"] == 10).all()
    assert (questions["n_gold_paragraphs"] == 2).all()
    assert len(corpus) == 40
    assert int(corpus["is_gold"].sum()) == 8
    assert corpus.groupby("qid").size().eq(10).all()
    assert corpus["passage_id"].is_unique
    assert corpus["passage_id"].str.startswith("hotpot:").all()

    splits = json.loads((tmp_path / "hotpot_splits.json").read_text(encoding="utf-8"))
    assert splits["splits"]["hotpot"] == ["q1", "q2", "q3", "q4"]
    assert len(splits["sha256"]["hotpot"]) == 64


def test_prepare_hotpot_reads_the_parquet_mirror(tmp_path: Path) -> None:
    import pandas as pd

    rows = []
    for item in _dataset():
        context = {
            "title": [title for title, _ in item["context"]],
            "sentences": [sentences for _, sentences in item["context"]],
        }
        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answer": item["answer"],
                "type": item["type"],
                "level": item["level"],
                "supporting_facts": {
                    "title": [title for title, _ in item["supporting_facts"]],
                    "sent_id": [index for _, index in item["supporting_facts"]],
                },
                "context": context,
            }
        )
    raw = tmp_path / "hotpot.parquet"
    pd.DataFrame(rows).to_parquet(raw, index=False)

    manifest_path = prepare_hotpot(raw, tmp_path / "processed", n_questions=4, seed=7)

    summary = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert summary["counts"]["n_questions"] == 4
    assert summary["counts"]["n_passages"] == 40


def test_prepare_hotpot_rejects_a_sample_larger_than_the_frame(tmp_path: Path) -> None:
    raw = _write_json(tmp_path / "hotpot.json", _dataset())

    with pytest.raises(ValueError, match="only 4 available"):
        prepare_hotpot(raw, tmp_path / "processed", n_questions=5)


def test_prepare_hotpot_rejects_duplicate_question_ids(tmp_path: Path) -> None:
    questions = _dataset()
    questions.append(_question("q1", n_paragraphs=10))
    raw = _write_json(tmp_path / "hotpot.json", questions)

    with pytest.raises(ValueError, match="duplicate HotpotQA question id"):
        prepare_hotpot(raw, tmp_path / "processed", n_questions=4)


def test_word_chunking_is_opt_in(tmp_path: Path) -> None:
    raw = _write_json(tmp_path / "hotpot.json", _dataset())

    manifest_path = prepare_hotpot(
        raw,
        tmp_path / "processed",
        n_questions=4,
        chunking="word",
        passage_words=2,
    )

    summary = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert summary["counts"]["n_passages"] > 40
    assert summary["corpus"]["passage_words"] == 2
