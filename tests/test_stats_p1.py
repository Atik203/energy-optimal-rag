"""Tests for the P1 confirmatory analysis."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

from rag_energy.stats.p1 import (
    affine_lack_of_fit,
    bootstrap,
    certification_cost,
    context_share,
    identity_gap,
    load_rows,
    margin_sensitivity,
    noninferiority,
    paired_questions,
    summarize,
    write_p1_analysis,
)


def _row(
    qid: str,
    k: int,
    *,
    correct: int,
    j_total: float,
    valid: int = 1,
    correct_lenient: int | None = None,
    f1: float = 0.0,
) -> dict[str, object]:
    return {
        "run_id": "test",
        "question_id": qid,
        "question_order": 0,
        "k": k,
        "order_in_question": k,
        "nonce": "a" * 10,
        "correct_em": correct,
        "correct_lenient": correct if correct_lenient is None else correct_lenient,
        "f1": f1,
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


def _dataset(n: int = 20, depths: tuple[int, ...] = (0, 1, 2, 4, 8, 16, 32)) -> list[dict]:
    rows: list[dict] = []
    for index in range(n):
        for k in depths:
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


def test_summarize_uses_ratio_of_sums_and_reports_invalid() -> None:
    rows = [
        _row("q1", 4, correct=1, j_total=10.0),
        _row("q2", 4, correct=0, j_total=30.0),
        _row("q3", 4, correct=1, j_total=20.0, valid=0),
    ]

    summaries = summarize(rows)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.n_valid == 2
    assert summary.n_invalid == 1
    assert summary.n_correct == 1
    assert summary.accuracy == pytest.approx(0.5)
    assert summary.mean_j == pytest.approx(20.0)
    assert summary.e_per_correct == pytest.approx(40.0)


def test_summarize_retains_infinite_energy_when_no_answer_is_correct() -> None:
    summaries = summarize([_row("q1", 8, correct=0, j_total=10.0)])

    assert math.isinf(summaries[0].e_per_correct)
    assert summaries[0].as_row()["e_per_correct"] == "inf"


def test_paired_questions_requires_valid_rows_at_both_depths() -> None:
    rows = [
        _row("q1", 4, correct=1, j_total=10.0),
        _row("q1", 32, correct=1, j_total=20.0),
        _row("q2", 4, correct=1, j_total=10.0),
        _row("q2", 32, correct=1, j_total=20.0, valid=0),
        _row("q3", 4, correct=1, j_total=10.0, valid=0),
        _row("q3", 32, correct=1, j_total=20.0),
    ]

    candidate, reference, excluded = paired_questions(rows, 4, 32)

    assert [row["question_id"] for row in candidate] == ["q1"]
    assert [row["question_id"] for row in reference] == ["q1"]
    assert excluded == ["q2", "q3"]


def test_noninferiority_reports_lower_bound_and_mcnemar() -> None:
    # 10 candidate-only, 10 reference-only, 80 concordant.
    candidate = [1] * 10 + [0] * 10 + [1] * 40 + [0] * 40
    reference = [0] * 10 + [1] * 10 + [1] * 40 + [0] * 40

    result = noninferiority(candidate, reference, margin=0.05, alpha=0.05)

    assert result.n_pairs == 100
    assert result.b == 10
    assert result.c == 10
    assert result.mean_diff == pytest.approx(0.0)
    assert result.se == pytest.approx(math.sqrt(20.0 / 99.0) / 10.0)
    assert result.lower_bound == pytest.approx(-0.0739, abs=1e-4)
    assert result.p_value == pytest.approx(0.1330, abs=1e-4)
    assert result.non_inferior is False
    assert result.mcnemar_exact_p == pytest.approx(1.0)


def test_noninferiority_passes_with_no_discordance() -> None:
    result = noninferiority([1] * 100, [1] * 100)

    assert result.mean_diff == 0.0
    assert result.se == 0.0
    assert result.lower_bound == 0.0
    assert result.p_value == 0.0
    assert result.non_inferior is True


def test_noninferiority_rejects_a_five_point_loss() -> None:
    candidate = [1] * 10 + [0] * 15 + [1] * 40 + [0] * 35
    reference = [0] * 10 + [1] * 15 + [1] * 40 + [0] * 35

    result = noninferiority(candidate, reference, margin=0.05)

    assert result.mean_diff == pytest.approx(-0.05)
    assert result.lower_bound < -0.05
    assert result.non_inferior is False


def test_bootstrap_savings_point_matches_the_ratio_estimand() -> None:
    rows = _dataset(n=60)

    result = bootstrap(rows, resamples=200, seed=7)

    paired = summarize(rows)
    by_k = {summary.k: summary for summary in paired}
    expected = 100.0 * (1.0 - by_k[4].e_per_correct / by_k[32].e_per_correct)
    assert result["savings_pct"]["point"] == pytest.approx(expected, rel=1e-9)
    assert result["n_pairs"] == 60
    assert sum(result["p_k_optimal"].values()) == pytest.approx(1.0)
    interval = result["savings_pct"]["interval"]
    assert interval["lower"] <= interval["upper"]


def test_bootstrap_is_deterministic_for_a_fixed_seed() -> None:
    rows = _dataset(n=30)

    first = bootstrap(rows, resamples=100, seed=11)
    second = bootstrap(rows, resamples=100, seed=11)

    assert first["savings_pct"] == second["savings_pct"]
    assert first["p_k_optimal"] == second["p_k_optimal"]


def test_affine_lack_of_fit_detects_an_exact_line() -> None:
    points = [(k, 10.0 + 2.0 * k) for k in (0, 1, 2, 4, 8, 16, 32)]

    fit = affine_lack_of_fit(points)

    assert fit["a"] == pytest.approx(10.0)
    assert fit["b"] == pytest.approx(2.0)
    assert fit["r2"] == pytest.approx(1.0)
    assert fit["quadratic_coefficient"] == pytest.approx(0.0, abs=1e-9)
    assert fit["lack_of_fit_p"] > 0.99


def test_context_share_uses_the_affine_prefill_term() -> None:
    summaries = summarize(
        [
            _row("q1", 4, correct=1, j_total=100.0),
            _row("q2", 4, correct=0, j_total=100.0),
        ]
    )

    shares = context_share(summaries, slope=2.0)

    # mean_j = 100, mean_retrieval = 1, J_pre = 2 * 4 = 8 -> 0.09
    assert shares[4] == pytest.approx(0.09)


def test_identity_gap_uses_central_difference_at_an_interior_depth() -> None:
    summaries = [
        {"k": 2, "accuracy": 0.44},
        {"k": 4, "accuracy": 0.48},
        {"k": 8, "accuracy": 0.56},
    ]

    from rag_energy.stats.p1 import DepthSummary

    typed = [
        DepthSummary(
            k=item["k"],
            n_valid=100,
            n_invalid=0,
            n_correct=int(100 * item["accuracy"]),
            accuracy=item["accuracy"],
            mean_j=100.0,
            mean_gpu_j=90.0,
            mean_retrieval_j=10.0,
            e_per_correct=100.0,
        )
        for item in summaries
    ]

    gap = identity_gap(typed, a=10.0, b=2.0, depth=4)

    assert gap["method"] == "central"
    assert gap["epsilon_j"] == pytest.approx(8.0 / 18.0)
    assert gap["epsilon_a"] == pytest.approx(4.0 * 0.02 / 0.48)
    assert gap["gap"] == pytest.approx(8.0 / 18.0 - 4.0 * 0.02 / 0.48)


def test_certification_cost_matches_the_break_even_formula() -> None:
    from rag_energy.stats.p1 import DepthSummary

    summaries = [
        DepthSummary(4, 100, 0, 50, 0.5, 25.0, 25.0, 0.0, 50.0),
        DepthSummary(32, 100, 0, 50, 0.5, 75.0, 75.0, 0.0, 150.0),
    ]

    result = certification_cost(summaries, selected_depth=4, reference_depth=32)

    assert result["total_sweep_j"] == pytest.approx(10_000.0)
    assert result["n_star"] == pytest.approx(200.0)


def test_margin_sensitivity_selects_the_cheapest_feasible_depth() -> None:
    from rag_energy.stats.p1 import DepthSummary

    summaries = [
        DepthSummary(0, 100, 0, 40, 0.40, 40.0, 40.0, 0.0, 100.0),
        DepthSummary(4, 100, 0, 50, 0.50, 25.0, 25.0, 0.0, 50.0),
        DepthSummary(32, 100, 0, 52, 0.52, 78.0, 78.0, 0.0, 150.0),
    ]

    rows = margin_sensitivity(summaries, margins=(0.01, 0.05))

    assert rows[0]["selected_depth"] == 32
    assert rows[1]["selected_depth"] == 4
    assert rows[1]["savings_pct"] == pytest.approx(100.0 * (1.0 - 50.0 / 150.0))


def test_write_p1_analysis_writes_every_registered_output(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    rows = _dataset(n=40)
    with raw.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    out = write_p1_analysis(raw, tmp_path / "analysis", run_id="synthetic", resamples=100)

    for name in (
        "estimates.csv",
        "identity.csv",
        "noninferiority.json",
        "bootstrap.json",
        "certification.json",
        "fit.json",
        "sensitivity.json",
        "gates.json",
        "metadata.json",
        "report.md",
    ):
        assert (out / name).is_file(), name
    payload = json.loads((out / "noninferiority.json").read_text(encoding="utf-8"))
    assert payload["run_id"] == "synthetic"
    assert "supported" in payload["decision"]
    assert (out / "estimates.csv").read_text(encoding="utf-8").count("\n") == 8
    assert load_rows(raw)[0]["question_id"] == "q000"
