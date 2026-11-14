"""Validation tests for :mod:`rag_energy.config`.

Standard library only: these tests build a throwaway config tree under
``tmp_path`` and never touch the real repository configs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rag_energy.config import (
    ConfigError,
    category_for,
    resolve_run_config,
    validate_all,
    validate_config,
)

_ANALYSIS_TOML = """\
schema_version = 1
kind = "analysis"
frozen = false
n_questions = {n_questions}
seed = 20261115

[primary]
margin_pp = 5.0
alpha = 0.05

[secondary]
margin_pp = 2.0

[bootstrap]
resamples = 1000

[policy_split]
train = {train}
validation = {validation}
test = {test}

[gates]
g1_margin_pp = 5.0
"""


def _write_analysis_config(
    tmp_path: Path,
    *,
    n_questions: int,
    train: int,
    validation: int,
    test: int,
) -> Path:
    """Write a minimal analysis config and return its path."""
    path = tmp_path / "configs" / "analysis" / "test.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _ANALYSIS_TOML.format(
            n_questions=n_questions,
            train=train,
            validation=validation,
            test=test,
        ),
        encoding="utf-8",
    )
    return path


def test_policy_split_matches_n_questions(tmp_path: Path) -> None:
    path = _write_analysis_config(tmp_path, n_questions=500, train=300, validation=100, test=100)
    assert validate_config(path, root=tmp_path) == []


def test_policy_split_mismatch_reports_target(tmp_path: Path) -> None:
    path = _write_analysis_config(tmp_path, n_questions=500, train=600, validation=200, test=200)
    errors = validate_config(path, root=tmp_path)
    assert any("sum to 500" in error for error in errors), errors


def test_category_for_locates_run_and_base(tmp_path: Path) -> None:
    assert category_for(tmp_path / "configs" / "runs" / "x.toml", tmp_path) == "run"
    assert category_for(tmp_path / "configs" / "base.toml", tmp_path) == "base"


_RUN_TOML = """\
schema_version = 1
kind = "run"
run_id = "test_run"
dataset = "squad"
n_questions = 500
k_grid = {k_grid}
seed = 20261115

[reader]
backend = "{backend}"
model = "{model}"
num_ctx = {num_ctx}

[retrieval]
top_k = {top_k}

[energy]
sampler = "nvml"
"""


def _write_run_config(
    tmp_path: Path,
    *,
    backend: str = "ollama",
    model: str = "llama3.2:3b",
    num_ctx: int = 4096,
    top_k: int = 32,
    k_grid: str = "[0, 1, 2, 4, 8, 16, 32]",
) -> Path:
    """Write a minimal run config and return its path."""
    path = tmp_path / "configs" / "runs" / "test.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _RUN_TOML.format(
            backend=backend,
            model=model,
            num_ctx=num_ctx,
            top_k=top_k,
            k_grid=k_grid,
        ),
        encoding="utf-8",
    )
    return path


def test_run_accepts_llama_panel_shape(tmp_path: Path) -> None:
    path = _write_run_config(tmp_path)
    assert validate_config(path, root=tmp_path) == []


def test_run_rejects_unknown_reader_backend(tmp_path: Path) -> None:
    path = _write_run_config(tmp_path, backend="vllm")
    errors = validate_config(path, root=tmp_path)
    assert any("reader.backend" in error for error in errors), errors


def test_run_rejects_empty_reader_model(tmp_path: Path) -> None:
    path = _write_run_config(tmp_path, model="")
    errors = validate_config(path, root=tmp_path)
    assert any("reader.model" in error for error in errors), errors


def test_run_rejects_nonpositive_num_ctx(tmp_path: Path) -> None:
    path = _write_run_config(tmp_path, num_ctx=0)
    errors = validate_config(path, root=tmp_path)
    assert any("reader.num_ctx" in error for error in errors), errors


def test_run_rejects_top_k_below_max_depth(tmp_path: Path) -> None:
    path = _write_run_config(tmp_path, top_k=32, k_grid="[32, 48, 64]")
    errors = validate_config(path, root=tmp_path)
    assert any("retrieval.top_k=32" in error for error in errors), errors


_BASE_TOML = """\
schema_version = 1
kind = "base"
seed = 20261115

[project]
name = "test"

[paths]
data_raw = "data/raw"

[reader]
backend = "ollama"
model = "base-model"
num_ctx = 4096

[retrieval]
top_k = 32
passage_words = 70

[energy]
sampler = "nvml"
sample_interval_ms = 100
"""

_RESOLVER_RUN_TOML = """\
schema_version = 1
kind = "run"
run_id = "r1"
dataset = "squad"
n_questions = 100
k_grid = [0, 1]
seed = 2
phase = "P0"
{grid_line}

[reader]
model = "run-model"

[retrieval]
top_k = 32

[energy]
sampler = "nvml"
"""

_GRID_TOML = """\
schema_version = 1
kind = "grid"
grid_id = "g1"
k_grid = [0, 1, 2]
n_questions = 200
base_run = "{base_run}"
phase = "P0"

[reader]
num_ctx = 8192

[retrieval]
top_k = 64
"""


def _write_resolver_tree(tmp_path: Path, *, base_run: str = "r1") -> Path:
    """Write a base, run, and referenced grid under a throwaway root."""
    configs = tmp_path / "configs"
    (configs / "runs").mkdir(parents=True)
    (configs / "grid").mkdir(parents=True)
    (configs / "base.toml").write_text(_BASE_TOML, encoding="utf-8")
    run_path = configs / "runs" / "r1.toml"
    run_path.write_text(_RESOLVER_RUN_TOML.format(grid_line='grid_id = "g1"'), encoding="utf-8")
    (configs / "grid" / "g1.toml").write_text(
        _GRID_TOML.format(base_run=base_run), encoding="utf-8"
    )
    return run_path


def test_resolve_run_config_merges_base_run_and_grid(tmp_path: Path) -> None:
    resolved = resolve_run_config(_write_resolver_tree(tmp_path), root=tmp_path)

    assert resolved.run_id == "r1"
    assert resolved.data["kind"] == "run"
    assert resolved.data["seed"] == 2
    assert resolved.data["reader"]["model"] == "run-model"
    assert resolved.data["reader"]["num_ctx"] == 8192
    assert resolved.data["retrieval"]["top_k"] == 64
    assert resolved.data["retrieval"]["passage_words"] == 70
    assert resolved.data["energy"]["sample_interval_ms"] == 100
    assert resolved.data["n_questions"] == 200
    assert resolved.data["k_grid"] == [0, 1, 2]
    assert len(resolved.sources) == 3
    assert len(resolved.config_sha256) == 64
    int(resolved.config_sha256, 16)


def test_resolve_run_config_without_grid_keeps_run_values(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    (configs / "runs").mkdir(parents=True)
    (configs / "base.toml").write_text(_BASE_TOML, encoding="utf-8")
    run_path = configs / "runs" / "r1.toml"
    run_path.write_text(_RESOLVER_RUN_TOML.format(grid_line=""), encoding="utf-8")

    resolved = resolve_run_config(run_path, root=tmp_path)

    assert resolved.data["n_questions"] == 100
    assert resolved.data["k_grid"] == [0, 1]
    assert resolved.data["reader"]["model"] == "run-model"
    assert resolved.data["reader"]["num_ctx"] == 4096
    assert len(resolved.sources) == 2


def test_resolve_run_config_rejects_missing_grid(tmp_path: Path) -> None:
    run_path = _write_resolver_tree(tmp_path)
    run_path.write_text(
        _RESOLVER_RUN_TOML.format(grid_line='grid_id = "missing"'), encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="grid"):
        resolve_run_config(run_path, root=tmp_path)


def test_resolve_run_config_rejects_grid_base_run_mismatch(tmp_path: Path) -> None:
    run_path = _write_resolver_tree(tmp_path, base_run="other")

    with pytest.raises(ConfigError, match="base_run"):
        resolve_run_config(run_path, root=tmp_path)


def test_resolve_run_config_hash_changes_with_grid(tmp_path: Path) -> None:
    run_path = _write_resolver_tree(tmp_path)
    first = resolve_run_config(run_path, root=tmp_path)

    grid_path = tmp_path / "configs" / "grid" / "g1.toml"
    grid_path.write_text(
        _GRID_TOML.format(base_run="r1").replace("n_questions = 200", "n_questions = 201"),
        encoding="utf-8",
    )
    second = resolve_run_config(run_path, root=tmp_path)

    assert first.config_sha256 != second.config_sha256


def test_validate_all_resolves_run_grids(tmp_path: Path) -> None:
    _write_resolver_tree(tmp_path)
    assert validate_all(tmp_path).ok


def test_validate_all_reports_grid_mismatch(tmp_path: Path) -> None:
    _write_resolver_tree(tmp_path, base_run="other")
    report = validate_all(tmp_path)
    assert not report.ok
