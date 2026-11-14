"""SQuAD preparation tests on a tiny in-memory fixture.

The real SQuAD JSON is never needed here. These tests exercise the contract:
deduplicate contexts, truncate to a word limit, chunk deterministically, sample
stratified disjoint IDs, and update the tracked manifest.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("pyarrow")

from rag_energy.cli import main
from rag_energy.data.prep_squad import prepare_squad


def _fixture() -> dict:
    long_context = " ".join(f"w{i}" for i in range(12))
    short = "short context here"
    return {
        "data": [
            {
                "title": "A",
                "paragraphs": [
                    {
                        "context": long_context,
                        "qas": [
                            {
                                "id": "q1",
                                "question": "What is the first thing?",
                                "answers": [{"text": "alpha", "answer_start": 0}],
                            },
                            {
                                "id": "q2",
                                "question": "When did it happen?",
                                "answers": [{"text": "beta", "answer_start": 0}],
                            },
                        ],
                    },
                    {
                        "context": short,
                        "qas": [
                            {
                                "id": "q3",
                                "question": "Who wrote it?",
                                "answers": [{"text": "gamma", "answer_start": 0}],
                            }
                        ],
                    },
                ],
            },
            {
                "title": "B",
                "paragraphs": [
                    {
                        "context": short,
                        "qas": [
                            {
                                "id": "q4",
                                "question": "Where is it?",
                                "answers": [{"text": "delta", "answer_start": 0}],
                            }
                        ],
                    },
                    {
                        "context": "another short context",
                        "qas": [
                            {
                                "id": "q5",
                                "question": "Which one is it?",
                                "answers": [{"text": "epsilon", "answer_start": 0}],
                            }
                        ],
                    },
                    {
                        "context": "yet another context",
                        "qas": [
                            {
                                "id": "q6",
                                "question": "Why does it happen?",
                                "answers": [{"text": "zeta", "answer_start": 0}],
                            }
                        ],
                    },
                    {
                        "context": "final context",
                        "qas": [
                            {
                                "id": "q7",
                                "question": "How does it work?",
                                "answers": [{"text": "eta", "answer_start": 0}],
                            }
                        ],
                    },
                ],
            },
        ]
    }


def _write_fixture(path: Path) -> Path:
    path.write_text(json.dumps(_fixture()), encoding="utf-8")
    return path


def _manifest() -> dict:
    return {
        "schema_version": 1,
        "generated_utc": None,
        "project": "energy-optimal-rag",
        "policy": "test",
        "datasets": [
            {
                "id": "squad",
                "name": "SQuAD",
                "version": "1.1",
                "split": "dev",
                "source_url": "https://example.invalid",
                "upstream_license": "CC BY-SA 4.0",
                "n_questions_total": 0,
                "n_questions_used": 0,
                "corpus": {},
                "checksums": {
                    "source_sha256": None,
                    "questions_sha256": None,
                    "corpus_sha256": None,
                },
                "prepared_utc": None,
                "preparation_seed": 20261115,
                "status": "not_prepared",
                "notes": "",
            }
        ],
    }


def _prepare(tmp_path: Path, **overrides: object) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    raw = _write_fixture(tmp_path / "dev.json")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    kwargs = {
        "out_dir": tmp_path / "processed",
        "n_questions": 5,
        "seed": 7,
        "passage_words": 5,
        "context_word_limit": 10,
        "split_sizes": {
            "p0_golden": 2,
            "p1_primary": 5,
            "replication": 2,
            "boundary": 1,
            "context": 1,
            "tax": 1,
        },
        "splits_out": tmp_path / "splits.json",
        "manifest_path": manifest_path,
    }
    kwargs.update(overrides)
    prepare_squad(raw, **kwargs)
    return manifest_path


def test_prepare_squad_writes_parquet_and_splits(tmp_path: Path) -> None:
    manifest_path = _prepare(tmp_path)

    assert (tmp_path / "processed" / "squad_questions.parquet").is_file()
    assert (tmp_path / "processed" / "squad_corpus.parquet").is_file()
    assert (tmp_path / "splits.json").is_file()
    assert manifest_path.is_file()

    import pandas as pd

    questions = pd.read_parquet(tmp_path / "processed" / "squad_questions.parquet")
    corpus = pd.read_parquet(tmp_path / "processed" / "squad_corpus.parquet")
    assert len(questions) == 7
    assert list(questions.columns) == [
        "qid",
        "question",
        "gold",
        "wh_type",
        "context_id",
        "title",
    ]
    assert len(corpus) == 6
    assert list(corpus.columns) == [
        "passage_id",
        "context_id",
        "title",
        "chunk_index",
        "text",
        "n_words",
    ]
    assert int(corpus["n_words"].max()) == 5
    assert corpus["context_id"].nunique() == 5


def test_prepare_squad_splits_are_stratified_and_deterministic(tmp_path: Path) -> None:
    _prepare(tmp_path / "a")
    _prepare(tmp_path / "b")

    first = json.loads((tmp_path / "a" / "splits.json").read_text(encoding="utf-8"))
    second = json.loads((tmp_path / "b" / "splits.json").read_text(encoding="utf-8"))
    assert first["splits"] == second["splits"]
    assert first["sha256"] == second["sha256"]

    splits = first["splits"]
    assert len(splits["p0_golden"]) == 2
    assert len(splits["p1_primary"]) == 5
    assert len(splits["replication"]) == 2
    assert len(splits["boundary"]) == 1
    assert splits["context"] == splits["boundary"]
    assert len(splits["tax"]) == 1
    assert set(splits["p0_golden"]).isdisjoint(splits["p1_primary"])
    assert set(splits["replication"]) <= set(splits["p1_primary"])
    assert set(splits["boundary"]) <= set(splits["p1_primary"])
    assert set(splits["replication"]).isdisjoint(splits["boundary"])
    assert "What is" not in json.dumps(first)


def test_prepare_squad_updates_manifest(tmp_path: Path) -> None:
    manifest_path = _prepare(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    squad = manifest["datasets"][0]

    assert squad["status"] == "prepared"
    assert squad["n_questions_total"] == 7
    assert squad["n_questions_used"] == 5
    assert squad["corpus"]["n_contexts"] == 5
    assert squad["corpus"]["n_passages"] == 6
    assert squad["checksums"]["source_sha256"]
    assert squad["checksums"]["questions_sha256"]
    assert squad["checksums"]["corpus_sha256"]
    assert squad["checksums"]["splits_sha256"]


def test_prepare_squad_rejects_oversized_split(tmp_path: Path) -> None:
    raw = _write_fixture(tmp_path / "dev.json")
    with pytest.raises(ValueError, match="p0_golden"):
        prepare_squad(
            raw,
            out_dir=tmp_path / "processed",
            split_sizes={
                "p0_golden": 100,
                "p1_primary": 5,
                "replication": 2,
                "boundary": 1,
                "context": 1,
                "tax": 1,
            },
        )


def test_prepare_squad_rejects_bad_squad_document(tmp_path: Path) -> None:
    raw = tmp_path / "bad.json"
    raw.write_text('{"not_data": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="data"):
        prepare_squad(raw, out_dir=tmp_path / "processed")


def test_cli_prepare_runs_on_fixture(tmp_path: Path) -> None:
    raw = _write_fixture(tmp_path / "dev.json")
    out = tmp_path / "processed"
    split_sizes = json.dumps(
        {
            "p0_golden": 2,
            "p1_primary": 5,
            "replication": 2,
            "boundary": 1,
            "context": 1,
            "tax": 1,
        }
    )

    code = main(
        [
            "prepare",
            "--raw",
            str(raw),
            "--out",
            str(out),
            "--n-questions",
            "5",
            "--split-sizes",
            split_sizes,
        ]
    )

    assert code == 0
    assert (out / "squad_questions.parquet").is_file()
    assert (out / "squad_corpus.parquet").is_file()
    assert (out / "squad_splits.json").is_file()
