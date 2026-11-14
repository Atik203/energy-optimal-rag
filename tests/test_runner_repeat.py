"""Repeat-CV (K7) tests with a fake reader and sampler."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("pyarrow")

import pandas as pd

from rag_energy.energy.nvml_sampler import PowerSample
from rag_energy.readers.base import ReaderResult
from rag_energy.runner import run_repeat_cv


class FakeReader:
    name = "fake"

    def generate(self, question: str, passages: list[str], nonce: str) -> ReaderResult:
        return ReaderResult(text="alpha", latency_s=0.01, load_s=0.0)


class FakeSampler:
    def __init__(self, interval_ms: int = 10) -> None:
        self.interval_ms = interval_ms
        self._started = 0.0

    def start(self) -> None:
        self._started = time.monotonic()

    def stop(self) -> list[PowerSample]:
        return [
            PowerSample(t_s=self._started, power_w=50.0),
            PowerSample(t_s=self._started + 0.1, power_w=50.0),
        ]


def _write_processed(tmp_path: Path) -> Path:
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame(
        [
            {
                "qid": f"q{i}",
                "question": f"What is {i}?",
                "gold": "alpha",
                "wh_type": "what",
                "context_id": "c1",
                "title": "A",
            }
            for i in (1, 2)
        ]
    ).to_parquet(processed / "squad_questions.parquet", index=False)
    pd.DataFrame([{"passage_id": "p1", "context_id": "c1", "text": "alpha"}]).to_parquet(
        processed / "squad_corpus.parquet", index=False
    )
    (processed / "squad_splits.json").write_text(
        json.dumps({"splits": {"p0_golden": ["q1", "q2"]}}), encoding="utf-8"
    )
    return processed


def _write_config(tmp_path: Path) -> Path:
    configs = tmp_path / "configs"
    (configs / "runs").mkdir(parents=True)
    (configs / "base.toml").write_text(
        """\
schema_version = 1
kind = "base"
seed = 20261115
[project]
name = "test"
[paths]
data_raw = "data/raw"
[reader]
backend = "ollama"
model = "fake"
num_ctx = 4096
[retrieval]
top_k = 8
passage_words = 70
[energy]
sampler = "nvml"
sample_interval_ms = 10
idle_baseline_s = 1
block_size = 1
warmup_queries = 1
nonce_hex_chars = 10
cpu_retrieval_proxy_watts = 20.0
[measurement]
repeat_blocks = 2
repeat_queries_per_block = 2
repeat_depth = 8
""",
        encoding="utf-8",
    )
    run = configs / "runs" / "test.toml"
    run.write_text(
        """\
schema_version = 1
kind = "run"
run_id = "test_run"
dataset = "squad"
n_questions = 2
k_grid = [0, 8]
id_split = "p0_golden"
seed = 20261115
phase = "P0"
[reader]
model = "fake"
[retrieval]
top_k = 8
[energy]
sampler = "nvml"
sample_interval_ms = 10
idle_baseline_s = 1
block_size = 1
warmup_queries = 1
nonce_hex_chars = 10
cpu_retrieval_proxy_watts = 20.0
[scoring]
primary = "normalized_em"
[output]
dir = "runs"
raw_csv = "raw.csv"
blocks_json = "blocks.json"
""",
        encoding="utf-8",
    )
    return run


def test_run_repeat_cv_writes_zero_cv(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path)
    config_path = _write_config(tmp_path)

    repeat_path = run_repeat_cv(
        config_path,
        root=tmp_path,
        processed_dir=processed,
        out_root=tmp_path / "runs",
        reader=FakeReader(),
        sampler_factory=FakeSampler,
        idle_power_w=15.0,
    )

    payload = json.loads(repeat_path.read_text(encoding="utf-8"))
    assert payload["k"] == 8
    assert payload["n_blocks"] == 2
    assert payload["queries_per_block"] == 2
    assert payload["cv_max"] == pytest.approx(0.0)
    assert payload["passed"] is True
    assert len(payload["per_query"]) == 2
