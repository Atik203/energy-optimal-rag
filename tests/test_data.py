"""Unit tests for chunking, deterministic splits, and manifest validation.

Standard library plus pytest only: no numpy, pandas, torch, or GPU. Nothing is
written to disk; manifest checks run on in-memory dictionaries.
"""

from __future__ import annotations

from typing import Any

import pytest

from rag_energy.data.chunking import chunk_document, chunk_words
from rag_energy.data.manifest import (
    MANIFEST_SCHEMA_VERSION,
    build_manifest,
    validate_manifest,
)
from rag_energy.data.splits import assign_split, stable_bucket


def test_chunk_words_splits_without_overlap() -> None:
    assert chunk_words("a b c d e", size=2) == ["a b", "c d", "e"]


def test_chunk_words_keeps_exact_multiple_without_trailing_chunk() -> None:
    assert chunk_words("a b c d e f", size=3) == ["a b c", "d e f"]


def test_chunk_words_default_size_is_seventy_words() -> None:
    text = " ".join(f"w{i}" for i in range(75))
    chunks = chunk_words(text)
    assert len(chunks) == 2
    assert len(chunks[0].split()) == 70
    assert chunks[1] == "w70 w71 w72 w73 w74"


def test_chunk_words_shares_overlap_between_adjacent_chunks() -> None:
    # step = size - overlap = 2, so word c is shared.
    assert chunk_words("a b c d e", size=3, overlap=1) == ["a b c", "c d e"]
    # step = 1; the final window reaches the end, so no extra tail chunk.
    assert chunk_words("a b c", size=2, overlap=1) == ["a b", "b c"]
    # a partial trailing chunk is kept when the last window is longer than the
    # remaining words.
    assert chunk_words("a b c d", size=3, overlap=1) == ["a b c", "c d"]


@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_chunk_words_returns_empty_for_blank_text(text: str) -> None:
    assert chunk_words(text, size=2) == []


@pytest.mark.parametrize(
    ("size", "overlap", "match"),
    [
        (0, 0, "size"),
        (-1, 0, "size"),
        (2, -1, "overlap"),
        (2, 2, "overlap"),
        (2, 3, "overlap"),
    ],
)
def test_chunk_words_rejects_invalid_size_or_overlap(size: int, overlap: int, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        chunk_words("a b c", size=size, overlap=overlap)


def test_chunk_document_preserves_passage_order() -> None:
    assert chunk_document(["a b c", "d e"], size=2) == ["a b", "c", "d e"]


def test_chunk_document_of_no_passages_is_empty() -> None:
    assert chunk_document([], size=2) == []


def test_stable_bucket_is_deterministic() -> None:
    assert stable_bucket("q1", 13) == stable_bucket("q1", 13)
    assert stable_bucket("squad:5727b2d1", 2026, buckets=10_000) == stable_bucket(
        "squad:5727b2d1", 2026, buckets=10_000
    )


@pytest.mark.parametrize("buckets", [1, 10, 10_000])
def test_stable_bucket_stays_in_range(buckets: int) -> None:
    for question_id in ("q1", "q2", "q3", "squad:5727b2d1dd62a815002e8f7e"):
        bucket = stable_bucket(question_id, 13, buckets=buckets)
        assert 0 <= bucket < buckets


def test_stable_bucket_differs_across_ids() -> None:
    # Two distinct IDs are expected to land in different 10-bucket bins.
    assert stable_bucket("q1", 13, buckets=10) != stable_bucket("q2", 13, buckets=10)


@pytest.mark.parametrize("buckets", [0, -1])
def test_stable_bucket_rejects_non_positive_buckets(buckets: int) -> None:
    with pytest.raises(ValueError, match="buckets must be positive"):
        stable_bucket("q1", 13, buckets=buckets)


def test_assign_split_is_deterministic() -> None:
    assert assign_split("q1", 13) == assign_split("q1", 13)
    assert assign_split("q7", 13) == assign_split("q7", 13)


def test_assign_split_returns_a_known_label() -> None:
    labels = {assign_split(f"q{i}", 13) for i in range(10)}
    assert labels <= {"train", "validation", "test"}


def test_assign_split_honors_degenerate_fractions() -> None:
    assert assign_split("q1", 13, train=1.0, validation=0.0, test=0.0) == "train"
    assert assign_split("q1", 13, train=0.0, validation=0.0, test=1.0) == "test"
    assert assign_split("q1", 13, train=0.0, validation=1.0, test=0.0) == "validation"


def test_assign_split_rejects_fractions_that_do_not_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        assign_split("q1", 13, train=0.6, validation=0.2, test=0.3)


def test_assign_split_rejects_negative_fractions() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        assign_split("q1", 13, train=-0.1, validation=0.9, test=0.2)


def _dataset() -> dict[str, Any]:
    return {
        "id": "squad",
        "name": "SQuAD v2.0 dev",
        "version": "2.0",
        "split": "validation",
        "source_url": "https://rajpurkar.github.io/SQuAD-explorer/",
        "upstream_license": "CC BY-SA 4.0",
        "n_questions_used": 1000,
        "status": "prepared",
    }


def _manifest(datasets: list[Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "datasets": [_dataset()] if datasets is None else datasets,
    }


def test_validate_manifest_accepts_minimal_valid_manifest() -> None:
    assert validate_manifest(_manifest()) == []


def test_validate_manifest_requires_non_empty_datasets() -> None:
    assert validate_manifest({"schema_version": MANIFEST_SCHEMA_VERSION, "datasets": []}) != []


def test_validate_manifest_rejects_wrong_schema_version() -> None:
    manifest = _manifest()
    manifest["schema_version"] = MANIFEST_SCHEMA_VERSION + 1
    assert "schema_version must be 1" in validate_manifest(manifest)


def test_validate_manifest_reports_missing_required_field() -> None:
    dataset = _dataset()
    del dataset["source_url"]
    errors = validate_manifest(_manifest([dataset]))
    assert any("missing 'source_url'" in error for error in errors)


def test_validate_manifest_rejects_duplicate_ids() -> None:
    second = dict(_dataset(), name="SQuAD v2.0 train", split="train")
    errors = validate_manifest(_manifest([_dataset(), second]))
    assert any("duplicate dataset id" in error for error in errors)


def test_validate_manifest_rejects_unknown_status() -> None:
    dataset = dict(_dataset(), status="downloaded")
    errors = validate_manifest(_manifest([dataset]))
    assert any("status must be one of" in error for error in errors)


@pytest.mark.parametrize("n_used", [-1, -1000])
def test_validate_manifest_rejects_negative_n_questions_used(n_used: int) -> None:
    dataset = dict(_dataset(), n_questions_used=n_used)
    errors = validate_manifest(_manifest([dataset]))
    assert any("n_questions_used must be a non-negative integer" in e for e in errors)


def test_validate_manifest_rejects_non_integer_n_questions_used() -> None:
    dataset = dict(_dataset(), n_questions_used="1000")
    errors = validate_manifest(_manifest([dataset]))
    assert any("n_questions_used must be a non-negative integer" in e for e in errors)


def test_validate_manifest_rejects_non_object_dataset() -> None:
    errors = validate_manifest(_manifest(["squad"]))
    assert any("must be an object" in error for error in errors)


def test_build_manifest_has_expected_shape_and_validates() -> None:
    dataset = _dataset()
    manifest = build_manifest("energy-optimal-rag", [dataset])
    assert manifest["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert manifest["project"] == "energy-optimal-rag"
    assert manifest["datasets"] == [dataset]
    assert "policy" in manifest
    assert "No raw text is stored" in manifest["policy"]
    assert validate_manifest(manifest) == []
