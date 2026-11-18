"""Tests for the CPU-only simulation studies.

The tests run deliberately small grids. They check that the study outputs are
finite where required, that coverage and rejection rates are probabilities,
and that the vectorized delta-method SE matches the frozen ratio module.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from rag_energy.stats.ratio import delta_method_variance, ratio_standard_error
from rag_energy.stats.simulations import (
    _bca_bounds,
    _delta_standard_errors,
    _paired_table_probabilities,
    _score_statistics,
    render_report,
    simulate_power_study,
    simulate_ratio_study,
    simulate_selection_study,
    write_simulation_outputs,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "simulations_script", ROOT / "scripts" / "19_simulations.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_delta_standard_error_matches_frozen_ratio_module() -> None:
    rng = np.random.default_rng(7)
    joules = rng.lognormal(3.2, 0.4, size=(3, 120))
    correct = rng.binomial(1, 0.4, size=(3, 120)).astype(float)
    vectorized = _delta_standard_errors(joules, correct)
    for row in range(joules.shape[0]):
        expected = ratio_standard_error(joules[row].tolist(), correct[row].tolist())
        assert vectorized[row] == pytest.approx(expected, rel=1e-12, abs=1e-12)
        variance = delta_method_variance(joules[row].tolist(), correct[row].tolist())
        assert variance >= 0


def test_paired_table_probabilities_sum_to_one() -> None:
    probabilities = _paired_table_probabilities(0.5, 0.12, -0.05)
    assert probabilities.sum() == pytest.approx(1.0)
    assert np.all(probabilities >= 0.0)
    with pytest.raises(ValueError):
        _paired_table_probabilities(0.5, 0.12, -0.6)


def test_score_statistic_is_zero_at_the_null_difference() -> None:
    # d_hat = -margin is the boundary of the null; the score is centred at zero.
    statistic, p_value = _score_statistics(np.array([6.0]), np.array([16.0]), 200, 0.05)
    assert statistic[0] == pytest.approx(0.0, abs=1e-12)
    assert p_value[0] == pytest.approx(0.5, abs=1e-12)


def test_bca_bounds_are_ordered() -> None:
    rng = np.random.default_rng(11)
    n = 200
    correct = rng.binomial(1, 0.5, n).astype(float)
    joules = rng.lognormal(3.1, 0.3, n) * (1.0 + 0.2 * correct)
    theta = joules.sum() / correct.sum()
    index = rng.integers(0, n, size=(200, n))
    draws = joules[index].sum(axis=1) / correct[index].sum(axis=1)
    lower, upper, fallback = _bca_bounds(draws, joules, correct, float(theta))
    assert lower <= upper
    assert isinstance(fallback, bool)


def test_ratio_study_small_run() -> None:
    study = simulate_ratio_study(
        accuracies=(0.3, 0.8),
        sample_sizes=(60, 120),
        noises=("lognormal", "gamma"),
        reps=12,
        bootstrap_reps=4,
        bootstrap_resamples=25,
        seed=101,
    )
    assert study["study"] == "S1_ratio_estimator"
    assert len(study["cells"]) == 8
    for cell in study["cells"]:
        estimate = cell["ratio_of_sums"]
        assert math.isfinite(estimate["bias"])
        assert math.isfinite(estimate["rmse"])
        assert math.isfinite(cell["true_e_ratio"])
        for coverage in estimate["coverage"].values():
            assert coverage is None or 0.0 <= coverage <= 1.0
        for width in estimate["mean_width"].values():
            assert width is None or width["mean"] is None or width["mean"] >= 0.0
        assert 0.0 <= cell["mean_of_ratios"]["undefined_rate"] <= 1.0
        assert 0.0 <= cell["mean_of_ratios"]["coverage_vs_ratio_target"] <= 1.0


def test_power_study_small_run() -> None:
    study = simulate_power_study(
        sample_sizes=(60, 120),
        differences=(-0.05, -0.02, 0.0),
        reps=40,
        seed=202,
    )
    assert study["study"] == "S2_noninferiority_power"
    assert len(study["cells"]) == 6
    for cell in study["cells"]:
        for value in cell["rejection"].values():
            assert 0.0 <= value <= 1.0
        for value in cell["coverage"].values():
            assert 0.0 <= value <= 1.0
        assert math.isfinite(cell["mean_difference"])
        assert cell["mean_se"] >= 0.0
        assert cell["mean_width_pp"]["wald"] >= 0.0
    margin_cells = [cell for cell in study["cells"] if cell["is_margin_cell"]]
    assert len(margin_cells) == 2


def test_selection_study_small_run() -> None:
    study = simulate_selection_study(
        gaps=(0.05, 0.25),
        sample_sizes=(60, 120),
        reps=10,
        bootstrap_reps=4,
        bootstrap_resamples=20,
        seed=303,
        engine_check_resamples=8,
    )
    assert study["study"] == "S3_selection_and_certification"
    assert len(study["cells"]) == 4
    for cell in study["cells"]:
        assert 0.0 <= cell["selection_rate"] <= 1.0
        assert sum(cell["selection_counts"].values()) == cell["reps"]
        assert math.isfinite(cell["winner_curse"]["mean_e_bias"])
        assert math.isfinite(cell["winner_curse"]["mean_regret"])
        assert 0.0 <= cell["bootstrap"]["p_true_mean"] <= 1.0
        assert 0.0 <= cell["bootstrap"]["k3_pass_rate"] <= 1.0
        assert cell["n_star"]["defined_rate"] is None or (
            0.0 <= cell["n_star"]["defined_rate"] <= 1.0
        )
        if cell["n_star"]["relative_bias"] is not None:
            assert math.isfinite(cell["n_star"]["relative_bias"])
        assert cell["engine_check"] is not None
        assert cell["engine_check"]["max_abs_difference"] <= 1.0


def test_outputs_and_report_are_written(tmp_path: Path) -> None:
    ratio = simulate_ratio_study(
        accuracies=(0.5,),
        sample_sizes=(60,),
        noises=("lognormal",),
        reps=8,
        bootstrap_reps=3,
        bootstrap_resamples=20,
        seed=404,
    )
    power = simulate_power_study(sample_sizes=(60,), differences=(-0.05,), reps=20, seed=405)
    selection = simulate_selection_study(
        gaps=(0.1,),
        sample_sizes=(60,),
        reps=8,
        bootstrap_reps=3,
        bootstrap_resamples=20,
        seed=406,
        engine_check_resamples=8,
    )
    written = write_simulation_outputs(tmp_path, ratio, power, selection)
    names = {path.name for path in written}
    assert names == {"s1.json", "s2.json", "s3.json", "report.md"}
    for name in ("s1.json", "s2.json", "s3.json"):
        payload = json.loads((tmp_path / name).read_text(encoding="utf-8"))
        assert payload["note"].startswith("Monte Carlo simulation")
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "not empirical results" in report
    assert "S1 - ratio estimator" in report
    assert "S2 - non-inferiority test" in report
    assert "S3 - selection and certification" in report
    assert report == render_report(ratio, power, selection)


def test_quick_script_writes_outputs(tmp_path: Path) -> None:
    module = _load_script()
    assert (
        module.main(
            [
                "--quick",
                "--out",
                str(tmp_path / "simulations"),
                "--seed",
                "505",
            ]
        )
        == 0
    )
    for name in ("s1.json", "s2.json", "s3.json", "report.md"):
        assert (tmp_path / "simulations" / name).is_file()
