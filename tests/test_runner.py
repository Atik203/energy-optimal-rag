"""Runner contract tests that do not need a GPU or a live reader."""

from __future__ import annotations

from rag_energy.config import REPO_ROOT
from rag_energy.runner import load_run_spec


def test_load_run_spec_resolves_p0_grid() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "runs" / "squad_qwen4b_p0.toml")

    assert spec.run_id == "golden_squad_qwen4b_p0"
    assert spec.config["kind"] == "run"
    assert spec.config["n_questions"] == 200
    assert spec.config["reader"]["num_ctx"] == 4096
    assert spec.config["grid_id"] == "golden200_k7"
    assert len(spec.config_sha256) == 64
