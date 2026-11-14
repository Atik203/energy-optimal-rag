"""P0 sweep-analysis tests: estimates, affine fit, anchors, and report files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from rag_energy.cli import main
from rag_energy.stats.sweep import (
    P0_FIT,
    P0_J_ANCHORS,
    affine_fit,
    compute_estimates,
    p0_check,
    write_analysis,
)


def _rows() -> list[dict[str, str]]:
    rows = []
    for k, correct in ((1, 2), (4, 3)):
        for index in range(3):
            rows.append(
                {
                    "k": str(k),
                    "valid": "1",
                    "correct_em": "1" if index < correct else "0",
                    "j_total": "10" if k == 1 else "20",
                    "j_gpu_calibrated": "8" if k == 1 else "16",
                    "j_retrieval_proxy": "2" if k == 1 else "4",
                    "invalid_reason": "",
                }
            )
    rows.append(
        {
            "k": "4",
            "valid": "0",
            "correct_em": "0",
            "j_total": "0",
            "j_gpu_calibrated": "0",
            "j_retrieval_proxy": "0",
            "invalid_reason": "reader_error",
        }
    )
    return rows


def test_compute_estimates_uses_ratio_of_sums() -> None:
    estimates = compute_estimates(_rows())
    by_k = {estimate.k: estimate for estimate in estimates}

    assert by_k[1].n_valid == 3
    assert by_k[1].n_correct == 2
    assert by_k[1].accuracy == pytest.approx(2 / 3)
    assert by_k[1].mean_j == pytest.approx(10.0)
    assert by_k[1].e_per_correct == pytest.approx(15.0)
    assert by_k[4].n_invalid == 1
    assert by_k[4].n_valid == 3
    assert by_k[4].e_per_correct == pytest.approx(20.0)


def test_compute_estimates_keeps_infinite_e_when_nothing_is_correct() -> None:
    rows = [
        {
            "k": "1",
            "valid": "1",
            "correct_em": "0",
            "j_total": "10",
            "j_gpu_calibrated": "8",
            "j_retrieval_proxy": "2",
            "invalid_reason": "",
        }
    ]

    estimate = compute_estimates(rows)[0]

    assert estimate.n_correct == 0
    assert estimate.e_per_correct == float("inf")


def test_affine_fit_recovers_known_line() -> None:
    fit = affine_fit([(1, 17.98), (4, 25.10), (32, 89.55)])

    assert fit.a == pytest.approx(P0_FIT["a"], abs=0.1)
    assert fit.b == pytest.approx(P0_FIT["b"], abs=0.1)
    assert fit.r2 > 0.99


def _anchor_estimates():
    from rag_energy.stats.sweep import DepthEstimate

    return [
        DepthEstimate(
            k=k,
            n_valid=200,
            n_invalid=0,
            n_correct=100,
            accuracy=0.5,
            mean_j=j,
            e_per_correct=j / 0.5,
            mean_gpu_j=j * 0.8,
            mean_retrieval_j=j * 0.2,
        )
        for k, j in P0_J_ANCHORS.items()
    ]


def test_p0_check_passes_on_pilot_anchors() -> None:
    estimates = _anchor_estimates()
    fit = affine_fit([(estimate.k, estimate.mean_j) for estimate in estimates])

    check = p0_check(estimates, fit)

    assert check["passed"] is True
    assert all(item["passed"] for item in check["checks"])


def test_p0_check_fails_on_shifted_energy() -> None:
    estimates = _anchor_estimates()
    estimates[0] = type(estimates[0])(
        **{**estimates[0].__dict__, "mean_j": estimates[0].mean_j * 1.2}
    )
    fit = affine_fit([(estimate.k, estimate.mean_j) for estimate in estimates])

    check = p0_check(estimates, fit)

    assert check["passed"] is False
    assert any("J(1)" in item["name"] and not item["passed"] for item in check["checks"])


def test_write_analysis_writes_estimates_check_and_report(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    with raw.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_rows()[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(_rows())

    out = tmp_path / "analysis"
    write_analysis(raw, out, run_id="test_run")

    assert (out / "estimates.csv").is_file()
    assert (out / "p0_check.json").is_file()
    assert (out / "report.md").is_file()
    estimates = list(csv.DictReader((out / "estimates.csv").open(encoding="utf-8")))
    assert {row["k"] for row in estimates} == {"1", "4"}
    check = json.loads((out / "p0_check.json").read_text(encoding="utf-8"))
    assert "passed" in check
    assert "P0" in (out / "report.md").read_text(encoding="utf-8")


def test_cli_analyze_writes_report(tmp_path: Path) -> None:
    raw = tmp_path / "runs" / "test_run" / "raw.csv"
    raw.parent.mkdir(parents=True)
    with raw.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_rows()[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(_rows())

    code = main(["analyze", "--run-id", "test_run", "--root", str(tmp_path)])

    assert code == 0
    assert (tmp_path / "analysis" / "test_run" / "report.md").is_file()
