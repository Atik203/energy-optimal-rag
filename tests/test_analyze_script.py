"""Tests for the P1 analysis routing and completeness guards."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "05_analyze.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("analyze_script", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_registry(
    root: Path,
    *,
    status: str = "completed",
    run_id: str = "squad_qwen4b_p1",
    phase: str = "P1",
    k_grid: str = "0|1",
    n_questions: str = "2",
) -> None:
    runs = root / "runs"
    runs.mkdir(parents=True)
    fields = [
        "run_id",
        "timestamp_utc",
        "phase",
        "dataset",
        "reader",
        "retriever",
        "k_grid",
        "n_questions",
        "seed",
        "energy_sampler",
        "status",
        "git_commit",
        "config_path",
        "config_sha256",
        "prereg_sha256",
        "model_digest",
        "raw_csv",
        "notes",
    ]
    with (runs / "registry.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "run_id": run_id,
                "timestamp_utc": "2026-11-15T00:00:00Z",
                "phase": phase,
                "dataset": "squad",
                "reader": "qwen3.5:4b",
                "retriever": "bm25",
                "k_grid": k_grid,
                "n_questions": n_questions,
                "seed": "20261115",
                "energy_sampler": "nvml",
                "status": status,
                "git_commit": "abc1234",
                "config_path": "configs/runs/squad_qwen4b.toml",
                "config_sha256": "deadbeef",
                "prereg_sha256": "abc",
                "model_digest": "sha256:model",
                "raw_csv": f"runs/{run_id}/raw.csv",
                "notes": "",
            }
        )


def _write_raw(root: Path, rows: int, *, run_id: str = "squad_qwen4b_p1") -> Path:
    path = root / "runs" / run_id / "raw.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["question_id", "k", "j_total", "correct_em"],
            lineterminator="\n",
        )
        writer.writeheader()
        for index in range(rows):
            writer.writerow(
                {
                    "question_id": f"q{index // 2}",
                    "k": index % 2,
                    "j_total": 10.0,
                    "correct_em": 1,
                }
            )
    return path


def test_phase_comes_from_the_manifest_then_the_registry(tmp_path: Path) -> None:
    module = _load_script()
    _write_registry(tmp_path)

    assert module._phase(tmp_path, "squad_qwen4b_p1") == "P1"

    manifest = tmp_path / "runs" / "squad_qwen4b_p1" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"phase": "P0"}), encoding="utf-8")
    assert module._phase(tmp_path, "squad_qwen4b_p1") == "P0"


def test_incomplete_run_is_refused(tmp_path: Path) -> None:
    module = _load_script()
    _write_registry(tmp_path, status="running")
    raw = _write_raw(tmp_path, rows=4)

    with pytest.raises(SystemExit, match="not 'completed'"):
        module._check_complete(tmp_path, "squad_qwen4b_p1", raw)


def test_row_count_must_match_the_registered_grid(tmp_path: Path) -> None:
    module = _load_script()
    _write_registry(tmp_path, status="completed")
    raw = _write_raw(tmp_path, rows=3)

    with pytest.raises(SystemExit, match="expected 4"):
        module._check_complete(tmp_path, "squad_qwen4b_p1", raw)


def test_complete_run_passes_the_guard(tmp_path: Path) -> None:
    module = _load_script()
    _write_registry(tmp_path, status="completed")
    raw = _write_raw(tmp_path, rows=4)

    module._check_complete(tmp_path, "squad_qwen4b_p1", raw)


def test_prereg_hash_mismatch_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script()
    _write_registry(tmp_path, status="completed")
    manifest = tmp_path / "runs" / "squad_qwen4b_p1" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"prereg_sha256": "old"}), encoding="utf-8")
    monkeypatch.setattr(module, "_prereg_sha256", lambda root: "new")

    with pytest.raises(SystemExit, match="prereg hash mismatch"):
        module._check_prereg_hash(tmp_path, "squad_qwen4b_p1")


def test_unfrozen_prereg_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script()
    _write_registry(tmp_path, status="completed")
    monkeypatch.setattr(module, "_prereg_sha256", lambda root: "")

    with pytest.raises(SystemExit, match="not frozen"):
        module._check_prereg_hash(tmp_path, "squad_qwen4b_p1")


def test_p2_phase_routes_to_the_direction_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_script()
    run_id = "squad_qwen15b_p2"
    _write_registry(
        tmp_path,
        run_id=run_id,
        phase="P2",
        k_grid="0|1|2|4|8|16|32",
        n_questions="2",
    )
    _write_raw(tmp_path, rows=14, run_id=run_id)
    monkeypatch.setattr(module, "_prereg_sha256", lambda root: "abc")
    calls: dict[str, object] = {}

    def fake_analysis(raw_path: Path, out_dir: Path, **kwargs: object) -> Path:
        calls.update(kwargs)
        calls["out_dir"] = out_dir
        return out_dir

    monkeypatch.setattr(module, "write_p2_analysis", fake_analysis)

    assert module.main(["--run-id", run_id, "--root", str(tmp_path), "--resamples", "25"]) == 0

    assert calls["run_id"] == run_id
    assert calls["resamples"] == 25
    assert calls["margin"] is None
    assert calls["out_dir"] == tmp_path / "analysis" / run_id
