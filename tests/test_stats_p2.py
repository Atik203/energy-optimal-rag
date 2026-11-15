"""Tests for the P2 direction replication analysis."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from rag_energy.stats.p2 import _directional_test, write_p2_analysis

DEPTHS = (0, 1, 2, 4, 8, 16, 32)


def _row(
    qid: str,
    k: int,
    *,
    correct: int,
    j_total: float,
    valid: int = 1,
) -> dict[str, object]:
    return {
        "run_id": "test",
        "question_id": qid,
        "question_order": 0,
        "k": k,
        "order_in_question": k,
        "nonce": "a" * 10,
        "correct_em": correct,
        "correct_lenient": correct,
        "f1": float(correct),
        "prediction": "x",
        "gold": "x",
        "j_gpu_raw": j_total,
        "j_gpu_calibrated": j_total,
        "j_retrieval_proxy": 1.0,
        "j_total": j_total,
        "latency_s": 1.0,
        "prompt_tokens": 10,
        "output_tokens": 1,
        "load_s": 0.0,
        "prefill_s": 0.1,
        "eval_s": 0.1,
        "gpu_temp_c": 60.0,
        "sm_clock_mhz": 1800,
        "power_mean_w": 50.0,
        "valid": valid,
        "invalid_reason": "",
    }


def _dataset(n: int = 40, *, candidate_correct_parity: int = 0) -> list[dict]:
    """Rows where k=4 is worse than k=32 by construction."""
    rows: list[dict] = []
    for index in range(n):
        for k in DEPTHS:
            if k == 4:
                correct = int(index % 2 == candidate_correct_parity)
            elif k == 32:
                correct = 1
            else:
                correct = int((index + k) % 3 != 0)
            rows.append(
                _row(
                    f"q{index:03d}",
                    k,
                    correct=correct,
                    j_total=10.0 + 2.0 * k + 0.1 * index,
                )
            )
    return rows


def _write_raw(path: Path, rows: list[dict]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_direction_is_supported_when_the_whole_interval_is_negative() -> None:
    # b = 5 candidate-only wins, c = 25 reference-only wins, n = 100.
    candidate = [1] * 5 + [0] * 25 + [1] * 30 + [0] * 40
    reference = [0] * 5 + [1] * 25 + [1] * 30 + [0] * 40

    result = _directional_test(
        candidate,
        reference,
        margin=0.05,
        n_invalid_candidate=0,
        n_invalid_reference=0,
    )

    assert result["mean_diff"] == pytest.approx(-0.20)
    assert result["one_sided_upper_zero"] < 0.0
    assert result["h7_supported"] is True
    assert result["point_direction_matches"] is True


def test_direction_is_not_supported_when_the_interval_crosses_zero() -> None:
    # A small negative point estimate with a wide interval cannot support H7.
    candidate = [1] + [0] * 3 + [1] * 8 + [0] * 8
    reference = [0] + [1] * 3 + [1] * 8 + [0] * 8

    result = _directional_test(
        candidate,
        reference,
        margin=0.05,
        n_invalid_candidate=0,
        n_invalid_reference=0,
    )

    assert result["mean_diff"] < 0.0
    assert result["one_sided_upper_zero"] > 0.0
    assert result["h7_supported"] is False


def test_a_positive_contrast_does_not_match_p1() -> None:
    candidate = [1] * 30
    reference = [0] * 30

    result = _directional_test(
        candidate,
        reference,
        margin=0.05,
        n_invalid_candidate=0,
        n_invalid_reference=0,
    )

    assert result["mean_diff"] > 0.0
    assert result["point_direction_matches"] is False
    assert result["h7_supported"] is False


def test_write_p2_analysis_writes_outputs_without_a_five_point_claim(tmp_path: Path) -> None:
    rows = _dataset(n=40)
    raw = _write_raw(tmp_path / "raw.csv", rows)
    config = {"n_questions": 40, "k_grid": list(DEPTHS), "seed": 7}

    out = write_p2_analysis(
        raw,
        tmp_path / "analysis",
        run_id="synthetic_p2",
        config=config,
        resamples=100,
    )

    for name in (
        "estimates.csv",
        "direction.json",
        "bootstrap.json",
        "fit.json",
        "metadata.json",
        "p2.json",
        "report.md",
    ):
        assert (out / name).is_file(), name
    payload = json.loads((out / "p2.json").read_text(encoding="utf-8"))
    assert payload["run_id"] == "synthetic_p2"
    assert payload["h7_supported"] is True
    assert payload["completeness"]["complete"] is True
    assert payload["completeness"]["expected_rows"] == 280
    metadata = json.loads((out / "metadata.json").read_text(encoding="utf-8"))
    assert "direction" in metadata["h7_definition"]
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "H7 supported" in report
    assert "not powered" in report
    assert "does not certify 5 pp" in report


def test_completeness_uses_the_run_config_and_rejects_a_short_run(tmp_path: Path) -> None:
    rows = _dataset(n=10)
    raw = _write_raw(tmp_path / "raw.csv", rows)
    config = {"n_questions": 20, "k_grid": list(DEPTHS)}

    with pytest.raises(ValueError, match="incomplete run"):
        write_p2_analysis(raw, tmp_path / "analysis", run_id="short", config=config, resamples=20)


def test_missing_run_config_reports_completeness_as_unknown(tmp_path: Path) -> None:
    raw = _write_raw(tmp_path / "raw.csv", _dataset(n=10))

    out = write_p2_analysis(raw, tmp_path / "analysis", run_id="unknown", resamples=20)

    payload = json.loads((out / "p2.json").read_text(encoding="utf-8"))
    assert payload["completeness"]["complete"] is None
    assert payload["completeness"]["n_questions_observed"] == 10


def test_candidate_must_be_shallower_than_reference(tmp_path: Path) -> None:
    raw = _write_raw(tmp_path / "raw.csv", _dataset(n=10))

    with pytest.raises(ValueError, match="shallower"):
        write_p2_analysis(
            raw,
            tmp_path / "analysis",
            run_id="bad",
            candidate=32,
            reference=4,
            resamples=20,
        )
