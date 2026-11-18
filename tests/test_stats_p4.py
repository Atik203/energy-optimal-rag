"""Tests for P4 cross-arm theory validation."""

from __future__ import annotations

import csv
import json

import pytest

from rag_energy.stats.p4 import write_p4_analysis


def _write_raw(path, depths, correct_counts, n=10):
    fields = [
        "question_id",
        "k",
        "correct_em",
        "correct_lenient",
        "f1",
        "j_total",
        "j_gpu_calibrated",
        "j_retrieval_proxy",
        "valid",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for depth, correct in zip(depths, correct_counts, strict=True):
            for index in range(n):
                is_correct = index < correct
                writer.writerow(
                    {
                        "question_id": f"q{index}",
                        "k": depth,
                        "correct_em": int(is_correct),
                        "correct_lenient": int(is_correct),
                        "f1": 1.0 if is_correct else 0.0,
                        "j_total": 10.0 + depth,
                        "j_gpu_calibrated": 10.0 + depth,
                        "j_retrieval_proxy": 0.0,
                        "valid": 1,
                    }
                )


def test_p4_flags_non_monotone_accuracy(tmp_path) -> None:
    raw = tmp_path / "raw.csv"
    _write_raw(raw, [0, 1, 2, 4], [6, 9, 7, 10])
    out = write_p4_analysis({"synthetic": raw}, tmp_path / "out")
    payload = json.loads((out / "p4.json").read_text(encoding="utf-8"))
    assert payload["arms"]["synthetic"]["monotone"] is False
    assert payload["arms"]["synthetic"]["accuracy"]["1"] == pytest.approx(0.9)
    assert (out / "identity.csv").is_file()
    assert (out / "margin.csv").is_file()
    assert (out / "scoring.csv").is_file()


def test_p4_requires_an_arm(tmp_path) -> None:
    with pytest.raises(ValueError):
        write_p4_analysis({}, tmp_path)
