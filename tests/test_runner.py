"""Runner contract tests that do not need a GPU or a live reader."""

from __future__ import annotations

from rag_energy.config import REPO_ROOT
from rag_energy.readers.hf_reader import HFReader
from rag_energy.runner import _default_reader, _model_digest, load_run_spec


def test_load_run_spec_resolves_p0_grid() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "runs" / "squad_qwen4b_p0.toml")

    assert spec.run_id == "golden_squad_qwen4b_p0"
    assert spec.config["kind"] == "run"
    assert spec.config["n_questions"] == 200
    assert spec.config["reader"]["num_ctx"] == 4096
    assert spec.config["grid_id"] == "golden200_k7"
    assert len(spec.config_sha256) == 64


def test_hf_reader_dispatch_and_revision_digest() -> None:
    config = {
        "reader": {
            "backend": "hf",
            "model": "Qwen/Qwen2.5-1.5B-Instruct",
            "device": "cuda",
            "dtype": "float16",
            "num_ctx": 4096,
            "num_predict": 24,
            "temperature": 0.0,
            "top_k": 1,
            "seed": 42,
        }
    }

    reader = _default_reader(config)

    assert isinstance(reader, HFReader)
    assert reader.config.model == "Qwen/Qwen2.5-1.5B-Instruct"
    assert reader.config.device == "cuda"
    reader.revision = "abc123"
    assert _model_digest(reader, config) == "abc123"
