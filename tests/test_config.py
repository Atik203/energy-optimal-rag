"""Validation tests for :mod:`rag_energy.config`.

Standard library only: these tests build a throwaway config tree under
``tmp_path`` and never touch the real repository configs.
"""

from __future__ import annotations

from pathlib import Path

from rag_energy.config import category_for, validate_config

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
