"""Registry writer tests: exact schema, LF endings, hashes, and updates."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from rag_energy.config import REPO_ROOT
from rag_energy.registry import (
    REGISTRY_FIELDS,
    append_registry_row,
    read_registry,
    sha256_file,
    update_registry_status,
)


def _header(path: Path) -> None:
    path.write_text(",".join(REGISTRY_FIELDS) + "\n", encoding="utf-8", newline="")


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "r1",
        "timestamp_utc": "2026-11-14T00:00:00Z",
        "phase": "P0",
        "dataset": "squad",
        "reader": "qwen3.5:4b",
        "retriever": "bm25",
        "k_grid": (0, 1, 2),
        "n_questions": 200,
        "seed": 20261115,
        "energy_sampler": "nvml",
        "status": "planned",
        "git_commit": "abc1234",
        "config_path": "configs/runs/squad_qwen4b_p0.toml",
        "config_sha256": "a" * 64,
        "prereg_sha256": "",
        "model_digest": "sha256:model",
        "raw_csv": "runs/golden_squad_qwen4b_p0/raw.csv",
        "notes": "golden harness check",
    }
    row.update(overrides)
    return row


def test_append_registry_row_writes_exact_schema(tmp_path: Path) -> None:
    path = tmp_path / "registry.csv"
    _header(path)

    append_registry_row(path, _row())

    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.endswith(b"\n")
    assert b"\r\n" not in raw
    rows = read_registry(path)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "r1"
    assert rows[0]["k_grid"] == "0|1|2"
    assert rows[0]["config_sha256"] == "a" * 64


def test_append_registry_row_rejects_duplicate_run_id(tmp_path: Path) -> None:
    path = tmp_path / "registry.csv"
    _header(path)
    append_registry_row(path, _row())

    with pytest.raises(ValueError, match="already registered"):
        append_registry_row(path, _row())


def test_append_registry_row_rejects_missing_field(tmp_path: Path) -> None:
    path = tmp_path / "registry.csv"
    _header(path)
    row = _row()
    row.pop("config_sha256")

    with pytest.raises(ValueError, match="missing"):
        append_registry_row(path, row)


def test_append_registry_row_rejects_unknown_status(tmp_path: Path) -> None:
    path = tmp_path / "registry.csv"
    _header(path)

    with pytest.raises(ValueError, match="status"):
        append_registry_row(path, _row(status="done"))


def test_update_registry_status_only_changes_target(tmp_path: Path) -> None:
    path = tmp_path / "registry.csv"
    _header(path)
    append_registry_row(path, _row())
    append_registry_row(path, _row(run_id="r2", status="running"))

    update_registry_status(path, "r1", "completed", notes="finished")

    rows = read_registry(path)
    assert rows[0]["status"] == "completed"
    assert rows[0]["notes"] == "finished"
    assert rows[1]["status"] == "running"


def test_update_registry_status_rejects_unknown_run(tmp_path: Path) -> None:
    path = tmp_path / "registry.csv"
    _header(path)

    with pytest.raises(ValueError, match="not found"):
        update_registry_status(path, "missing", "completed")


def test_sha256_file_matches_hashlib(tmp_path: Path) -> None:
    path = tmp_path / "payload.txt"
    path.write_bytes(b"abc")

    assert sha256_file(path) == hashlib.sha256(b"abc").hexdigest()


def test_tracked_registry_header_matches_schema() -> None:
    assert read_registry(REPO_ROOT / "runs" / "registry.csv") == []
