"""Tests for the Phase 8 causal-mechanism scaffolds.

These pin the pure parts of the distractor dose-response run
(``scripts/30_qc_distractor.py``) and the dense precompute
(``scripts/31_qc_dense_precompute.py``). CPU only: no GPU, no model download,
no network. The failures they guard against are silent: a dose plan that drops
a level, a position condition that misplaces the gold, a DiD with the wrong
sign convention, or a harmonization that drifts from the Phase 7 convention.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    import sys

    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses can resolve string annotations
    # (``from __future__ import annotations``) via ``sys.modules``.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def distractor_module():
    return _load("qc_distractor", "30_qc_distractor.py")


@pytest.fixture(scope="module")
def dense_module():
    return _load("qc_dense_precompute", "31_qc_dense_precompute.py")


@pytest.fixture(scope="module")
def session_analysis_module():
    return _load("phase7_session_analysis", "28_phase7_session_analysis.py")


class TestDosePlan:
    def test_covers_every_dose_and_replicate(self, distractor_module):
        plan = distractor_module.build_dose_plan((0, 1, 3, 7, 15, 31), 2, seed=7)
        assert len(plan) == 12
        assert {(item.dose, item.replicate) for item in plan} == {
            (dose, replicate) for dose in (0, 1, 3, 7, 15, 31) for replicate in (0, 1)
        }

    def test_deterministic_for_a_seed(self, distractor_module):
        first = distractor_module.build_dose_plan(seed=99)
        second = distractor_module.build_dose_plan(seed=99)
        assert [(i.dose, i.replicate) for i in first] == [(i.dose, i.replicate) for i in second]

    def test_rejects_empty_doses(self, distractor_module):
        with pytest.raises(ValueError):
            distractor_module.build_dose_plan((), 1, seed=0)


class TestDoseContext:
    def test_gold_first_with_dose_appended(self, distractor_module):
        context = distractor_module.build_dose_context("gold", ["d1", "d2", "d3"], 2)
        assert context == ["gold", "d1", "d2"]

    def test_dose_zero_is_gold_only(self, distractor_module):
        assert distractor_module.build_dose_context("gold", ["d1"], 0) == ["gold"]

    def test_short_distractor_pool_raises(self, distractor_module):
        with pytest.raises(ValueError):
            distractor_module.build_dose_context("gold", ["d1"], 3)


class TestPositionContext:
    def test_gold_lands_on_rank(self, distractor_module):
        distractors = [f"d{i}" for i in range(31)]
        for rank in (1, 8, 32):
            context = distractor_module.build_position_context("gold", distractors, 32, rank)
            assert len(context) == 32
            assert context[rank - 1] == "gold"
            assert context.count("gold") == 1

    def test_rank_outside_total_raises(self, distractor_module):
        with pytest.raises(ValueError):
            distractor_module.build_position_context("gold", ["d"] * 31, 32, 33)


class TestDoseTrend:
    def test_declining_accuracy_gives_negative_slope(self, distractor_module):
        means = {0: 0.80, 1: 0.78, 3: 0.74, 7: 0.68, 15: 0.60, 31: 0.50}
        trend = distractor_module.dose_accuracy_trend(means)
        assert trend["slope_per_doubling"] == pytest.approx(-0.06, abs=1e-9)

    def test_flat_curve_gives_zero_slope(self, distractor_module):
        means = {dose: 0.7 for dose in (0, 1, 3, 7, 15, 31)}
        assert distractor_module.dose_accuracy_trend(means)["slope_per_doubling"] == (
            pytest.approx(0.0, abs=1e-12)
        )


class TestDiD:
    def test_sign_convention_dense_degrades_less(self, distractor_module):
        # Dense: 0.80 -> 0.75 (drop 0.05). BM25: 0.80 -> 0.60 (drop 0.20).
        # Prereg formula: dense drop minus BM25 drop = -0.15, so negative
        # supports H-dense. The sign convention must not be flipped.
        assert distractor_module.did_estimate(0.80, 0.75, 0.80, 0.60) == pytest.approx(-0.15)

    def test_bootstrap_recovers_point_on_synthetic_arms(self, distractor_module):
        dense_4 = [1] * 80 + [0] * 20
        dense_32 = [1] * 75 + [0] * 25
        bm25_4 = [1] * 80 + [0] * 20
        bm25_32 = [1] * 60 + [0] * 40
        out = distractor_module.did_bootstrap_ci(
            dense_4, dense_32, bm25_4, bm25_32, resamples=200, seed=0
        )
        assert out["point"] == pytest.approx(-0.15)
        assert out["ci95"][0] <= out["point"] <= out["ci95"][1]

    def test_mismatched_arms_raise(self, distractor_module):
        with pytest.raises(ValueError):
            distractor_module.did_bootstrap_ci([1, 0], [1], [1, 0], [1, 0])


class TestHarmonizeReuse:
    def test_matches_phase7_convention(self, distractor_module, session_analysis_module):
        for energy, duration, idle, ref in [
            (100.0, 10.0, 20.0, 15.0),
            (250.0, 30.0, 14.5, 18.0),
            (100.0, 0.0, 20.0, 15.0),
        ]:
            assert distractor_module._harmonize(energy, duration, idle, ref) == (
                pytest.approx(session_analysis_module._harmonize(energy, duration, idle, ref))
            )


class TestResumeProtocol:
    def test_rows_from_another_protocol_are_discarded(self, distractor_module, tmp_path):
        ledger = tmp_path / "distractor.partial.jsonl"
        ledger.write_text(
            '{"dose": 0, "replicate": 0, "position": 1, "protocol": "old", "blocks": []}\n'
            '{"dose": 1, "replicate": 0, "position": 1, '
            '"protocol": "qc-distractor-v1", "blocks": []}\n',
            encoding="utf-8",
        )
        done = distractor_module.load_resume(ledger, "qc-distractor-v1")
        assert set(done) == {(1, 0, 1)}

    def test_missing_ledger_is_empty(self, distractor_module, tmp_path):
        assert distractor_module.load_resume(tmp_path / "absent.jsonl", "qc-distractor-v1") == {}


class TestDensePrecompute:
    def test_explicit_dir_resolves(self, dense_module, tmp_path):
        repo = tmp_path / "models--sentence-transformers--all-MiniLM-L6-v2"
        snap = repo / "snapshots" / ("a" * 40)
        snap.mkdir(parents=True)
        (repo / "refs").mkdir(parents=True)
        (repo / "refs" / "main").write_text("a" * 40, encoding="utf-8")
        assert dense_module.resolve_model_dir(explicit=str(tmp_path)) == snap

    def test_absent_cache_refuses_instead_of_downloading(self, dense_module, tmp_path, monkeypatch):
        # Hermetic: ignore the real machine caches and env so the test does
        # not depend on whether this host has the model cached.
        monkeypatch.setattr(dense_module, "DEFAULT_CACHE_DIRS", ())
        monkeypatch.delenv("HF_HUB_CACHE", raising=False)
        monkeypatch.delenv("HUGGINGFACE_HUB_CACHE", raising=False)
        with pytest.raises(FileNotFoundError):
            dense_module.resolve_model_dir(explicit=str(tmp_path / "empty"))

    def test_revision_hash_comes_from_refs_main(self, dense_module, tmp_path):
        repo = tmp_path / "models--sentence-transformers--all-MiniLM-L6-v2"
        snap = repo / "snapshots" / ("b" * 40)
        snap.mkdir(parents=True)
        (repo / "refs").mkdir(parents=True)
        (repo / "refs" / "main").write_text("b" * 40, encoding="utf-8")
        assert dense_module.read_revision_hash(snap) == "b" * 40

    def test_manifest_records_revision(self, dense_module):
        manifest = dense_module.build_manifest(
            model_id="sentence-transformers/all-MiniLM-L6-v2",
            revision_hash="c" * 40,
            snapshot_dir="/cache/snap",
            n_passages=45651,
            embedding_dim=384,
            normalize=True,
            batch_size=256,
            created_utc="2026-11-26T00:00:00Z",
        )
        assert manifest["revision_hash"] == "c" * 40
        assert manifest["frozen"] is True
        assert manifest["n_passages"] == 45651

    def test_offline_env_disables_downloads(self, dense_module):
        env = dense_module.offline_env()
        assert env["HF_HUB_OFFLINE"] == "1"
        assert env["TRANSFORMERS_OFFLINE"] == "1"
