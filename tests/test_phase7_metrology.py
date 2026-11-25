"""Tests for the Phase 7 metrology analyses.

These pin the pure parts of the replay, session, carryover, and manifest-sidecar
scripts. The failure they guard against is silent: an ICC that returns a plausible
number for identical groups, or a predecessor that is read from the wrong row, would
produce a reportable result that is simply wrong.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def icc_module():
    return _load("phase7_sessions_analysis", "28_phase7_session_analysis.py")


@pytest.fixture(scope="module")
def replay_module():
    return _load("phase7_replay_analysis", "25_phase7_replay_analysis.py")


@pytest.fixture(scope="module")
def carryover_module():
    return _load("phase7_carryover", "27_phase7_carryover.py")


@pytest.fixture(scope="module")
def sessions_module():
    return _load("phase7_sessions_run", "26_phase7_sessions.py")


class TestICC:
    def test_identical_sessions_give_zero_icc(self, icc_module):
        groups = [[10.0, 11.0, 9.0, 10.5], [10.0, 11.0, 9.0, 10.5], [10.0, 11.0, 9.0, 10.5]]
        result = icc_module._icc_one_way(groups)
        assert result["ms_between"] == pytest.approx(0.0, abs=1e-9)
        # The estimator is -1/(m-1) when between-session variance is exactly zero.
        assert result["icc"] == pytest.approx(-1.0 / 3.0, abs=1e-9)
        assert result["icc_truncated"] == 0.0

    def test_separated_sessions_give_high_icc(self, icc_module):
        groups = [[10.0, 10.1, 9.9, 10.0], [20.0, 20.1, 19.9, 20.0], [30.0, 30.1, 29.9, 30.0]]
        result = icc_module._icc_one_way(groups)
        assert result["icc"] > 0.99
        assert result["icc_truncated"] == pytest.approx(result["icc"])

    def test_single_session_is_not_estimable(self, icc_module):
        result = icc_module._icc_one_way([[1.0, 2.0, 3.0]])
        assert result["icc"] != result["icc"]  # NaN, not a fabricated number


class TestReplayStatistics:
    def test_ols_slope_recovers_a_known_line(self, replay_module):
        xs = [float(i) for i in range(10)]
        ys = [3.0 - 0.5 * x for x in xs]
        result = replay_module._ols_slope(xs, ys)
        assert result["slope_j_per_replay"] == pytest.approx(-0.5)
        assert result["r_squared"] == pytest.approx(1.0)

    def test_spearman_detects_a_monotone_decline(self, replay_module):
        xs = [float(i) for i in range(10)]
        ys = [10.0 - float(i) for i in range(10)]
        assert replay_module._spearman(xs, ys) == pytest.approx(-1.0)

    def test_quantile_interpolates(self, replay_module):
        assert replay_module._quantile([0.0, 10.0], 0.5) == pytest.approx(5.0)


class TestHarmonization:
    def test_rebasing_idle_recovers_the_same_gross(self, icc_module):
        # 100 J net over 10 s behind a 20 W baseline implies 300 J gross.
        # At a 15 W baseline the same gross yields 150 J net.
        assert icc_module._harmonize(100.0, 10.0, 20.0, 15.0) == pytest.approx(150.0)

    def test_zero_duration_is_returned_unchanged(self, icc_module):
        assert icc_module._harmonize(100.0, 0.0, 20.0, 15.0) == pytest.approx(100.0)


class TestResumeProtocol:
    def test_rows_from_another_protocol_are_discarded(self, sessions_module, tmp_path):
        ledger = tmp_path / "sessions.partial.jsonl"
        ledger.write_text(
            '{"session": 0, "protocol": "old-method", "blocks": []}\n'
            '{"session": 1, "protocol": "idle-from-cooldown-tail-v2", "blocks": []}\n',
            encoding="utf-8",
        )
        done = sessions_module.load_resume(ledger, "idle-from-cooldown-tail-v2")
        assert set(done) == {1}

    def test_missing_ledger_is_empty(self, sessions_module, tmp_path):
        assert sessions_module.load_resume(tmp_path / "absent.jsonl", "v2") == {}


class TestCarryoverPredecessor:
    def test_predecessor_crosses_the_question_boundary(self, carryover_module):
        rows = [
            {
                "question_id": "q1",
                "question_order": "0",
                "order_in_question": "0",
                "k": "32",
                "j_gpu_raw": "10",
                "gpu_temp_c": "70",
                "sm_clock_mhz": "1800",
                "valid": "1",
            },
            {
                "question_id": "q1",
                "question_order": "0",
                "order_in_question": "1",
                "k": "4",
                "j_gpu_raw": "5",
                "gpu_temp_c": "70",
                "sm_clock_mhz": "1800",
                "valid": "1",
            },
            {
                "question_id": "q2",
                "question_order": "1",
                "order_in_question": "0",
                "k": "1",
                "j_gpu_raw": "3",
                "gpu_temp_c": "70",
                "sm_clock_mhz": "1800",
                "valid": "1",
            },
        ]
        out = carryover_module._with_predecessor(rows)
        assert len(out) == 2
        assert out[0]["k"] == 4.0 and out[0]["k_prev"] == 32.0
        assert out[1]["k"] == 1.0 and out[1]["k_prev"] == 4.0
