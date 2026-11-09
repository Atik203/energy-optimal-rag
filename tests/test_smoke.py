"""Smoke tests.

Deliberately dependency-light: these tests must pass in CI with only pytest
installed, i.e. without numpy, pandas, torch, or a GPU.
"""

from __future__ import annotations

from pathlib import Path

from rag_energy import __version__
from rag_energy.config import validate_all


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_configs_exist_and_parse() -> None:
    root = Path(__file__).resolve().parents[1]
    report = validate_all(root)
    assert report.n_files >= 10, "expected the full config tree to be present"
    assert report.ok, f"config validation errors: {report.errors}"
