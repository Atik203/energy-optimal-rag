"""Depth-sweep runner integration test with fake reader and sampler."""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("pyarrow")

import pandas as pd

from rag_energy.energy.nvml_sampler import PowerSample
from rag_energy.readers.base import ReaderError, ReaderResult
from rag_energy.registry import read_registry
from rag_energy.runner import RAW_FIELDS, run_block_calibration, run_depth_sweep, run_repeat_cv
from rag_energy.stats.sweep import write_analysis


class FakeReader:
    name = "fake"

    def __init__(self, fail_on: str | None = None) -> None:
        self.fail_on = fail_on

    def generate(self, question: str, passages: list[str], nonce: str) -> ReaderResult:
        if self.fail_on and question == self.fail_on:
            raise ReaderError("backend down")
        return ReaderResult(
            text="alpha",
            latency_s=0.01,
            prompt_tokens=10,
            output_tokens=1,
            load_s=0.0,
            prompt_eval_s=0.005,
            eval_s=0.005,
        )


class FakeSampler:
    def __init__(self, interval_ms: int = 10, watts: float = 50.0) -> None:
        self.interval_ms = interval_ms
        self.watts = watts
        self._started = 0.0

    def start(self) -> None:
        self._started = time.monotonic()

    def stop(self) -> list[PowerSample]:
        return [
            PowerSample(
                t_s=self._started, power_w=self.watts, temperature_c=60.0, sm_clock_mhz=1500.0
            ),
            PowerSample(
                t_s=self._started + 0.1,
                power_w=self.watts,
                temperature_c=61.0,
                sm_clock_mhz=1500.0,
            ),
        ]


class ContinuousSampler(FakeSampler):
    """Samples every 10 ms so block windows have multiple points."""

    def stop(self) -> list[PowerSample]:
        now = time.monotonic()
        count = max(2, int((now - self._started) / 0.01) + 1)
        samples = [
            PowerSample(
                t_s=self._started + index * 0.01,
                power_w=self.watts,
                temperature_c=60.0,
                sm_clock_mhz=1500.0,
            )
            for index in range(count)
        ]
        samples.append(
            PowerSample(
                t_s=now,
                power_w=self.watts,
                temperature_c=60.0,
                sm_clock_mhz=1500.0,
            )
        )
        return samples


class SlowReader(FakeReader):
    """Reader with a realistic-enough duration for window selection."""

    def generate(self, question: str, passages: list[str], nonce: str) -> ReaderResult:
        time.sleep(0.1)
        return super().generate(question, passages, nonce)


def _write_processed(tmp_path: Path) -> Path:
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame(
        [
            {
                "qid": "q1",
                "question": "What is one?",
                "gold": "alpha",
                "wh_type": "what",
                "context_id": "c1",
                "title": "A",
            },
            {
                "qid": "q2",
                "question": "When is two?",
                "gold": "alpha",
                "wh_type": "when",
                "context_id": "c1",
                "title": "A",
            },
            {
                "qid": "q3",
                "question": "Who is three?",
                "gold": "alpha",
                "wh_type": "who",
                "context_id": "c2",
                "title": "B",
            },
        ]
    ).to_parquet(processed / "squad_questions.parquet", index=False)
    pd.DataFrame(
        [
            {"passage_id": "p1", "context_id": "c1", "text": "alpha one"},
            {"passage_id": "p2", "context_id": "c2", "text": "alpha two"},
        ]
    ).to_parquet(processed / "squad_corpus.parquet", index=False)
    (processed / "squad_splits.json").write_text(
        json.dumps({"splits": {"p0_golden": ["q1", "q2", "q3"]}}),
        encoding="utf-8",
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
top_k = 2
passage_words = 70
[energy]
sampler = "nvml"
sample_interval_ms = 10
idle_baseline_s = 1
block_size = 2
warmup_queries = 1
nonce_hex_chars = 10
cpu_retrieval_proxy_watts = 20.0
[measurement]
repeat_blocks = 2
repeat_queries_per_block = 2
repeat_depth = 2
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
n_questions = 3
k_grid = [0, 2]
id_split = "p0_golden"
seed = 20261115
phase = "P0"
[reader]
model = "fake"
[retrieval]
top_k = 2
[energy]
sampler = "nvml"
sample_interval_ms = 10
idle_baseline_s = 1
block_size = 2
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


def test_run_depth_sweep_writes_rows_and_registry(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path)
    config_path = _write_config(tmp_path)
    registry_path = tmp_path / "runs" / "registry.csv"

    raw_path = run_depth_sweep(
        config_path,
        root=tmp_path,
        processed_dir=processed,
        out_root=tmp_path / "runs",
        registry_path=registry_path,
        reader=FakeReader(),
        sampler_factory=FakeSampler,
        idle_power_w=15.0,
    )

    rows = list(csv.DictReader(raw_path.open(encoding="utf-8", newline="")))
    assert tuple(rows[0]) == RAW_FIELDS
    assert len(rows) == 6
    assert {row["question_id"] for row in rows} == {"q1", "q2", "q3"}
    assert {row["k"] for row in rows} == {"0", "2"}
    assert len({row["nonce"] for row in rows}) == 6
    assert all(row["valid"] == "1" for row in rows)
    assert all(row["correct_em"] == "1" for row in rows)
    assert all(float(row["j_gpu_raw"]) == pytest.approx(3.5) for row in rows)
    assert all(float(row["j_retrieval_proxy"]) >= 0 for row in rows)
    assert all(
        float(row["j_total"]) == pytest.approx(3.5 + float(row["j_retrieval_proxy"]))
        for row in rows
    )

    registry = read_registry(registry_path)
    assert len(registry) == 1
    assert registry[0]["run_id"] == "test_run"
    assert registry[0]["status"] == "completed"
    assert registry[0]["k_grid"] == "0|2"
    assert len(registry[0]["config_sha256"]) == 64

    manifest = json.loads((tmp_path / "runs" / "test_run" / "manifest.json").read_text())
    assert manifest["run_id"] == "test_run"
    assert manifest["counts"]["rows"] == 6
    assert manifest["id_split"] == "p0_golden"
    assert manifest["environment"]["executable"] == sys.executable


def test_run_depth_sweep_marks_reader_failure_invalid(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path)
    config_path = _write_config(tmp_path)

    raw_path = run_depth_sweep(
        config_path,
        root=tmp_path,
        processed_dir=processed,
        out_root=tmp_path / "runs",
        registry_path=tmp_path / "runs" / "registry.csv",
        reader=FakeReader(fail_on="When is two?"),
        sampler_factory=FakeSampler,
        idle_power_w=15.0,
    )

    rows = list(csv.DictReader(raw_path.open(encoding="utf-8", newline="")))
    failed = [row for row in rows if row["question_id"] == "q2"]
    assert failed
    assert all(row["valid"] == "0" for row in failed)
    assert all(row["invalid_reason"] == "reader_error" for row in failed)
    assert all(row["prediction"] == "" for row in failed)


def test_p0_chain_runs_sweep_blocks_repeat_and_analysis(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path)
    config_path = _write_config(tmp_path)
    runs = tmp_path / "runs"

    raw_path = run_depth_sweep(
        config_path,
        root=tmp_path,
        processed_dir=processed,
        out_root=runs,
        registry_path=runs / "registry.csv",
        reader=FakeReader(),
        sampler_factory=FakeSampler,
        idle_power_w=15.0,
    )
    blocks_path = run_block_calibration(
        config_path,
        root=tmp_path,
        processed_dir=processed,
        out_root=runs,
        reader=SlowReader(),
        sampler_factory=lambda interval_ms: ContinuousSampler(interval_ms, watts=35.0),
        idle_power_w=0.0,
    )
    repeat_path = run_repeat_cv(
        config_path,
        root=tmp_path,
        processed_dir=processed,
        out_root=runs,
        reader=SlowReader(),
        sampler_factory=lambda interval_ms: ContinuousSampler(interval_ms, watts=35.0),
        idle_power_w=0.0,
    )
    analysis_dir = write_analysis(raw_path, tmp_path / "analysis", run_id="test_run")

    assert blocks_path.is_file()
    assert repeat_path.is_file()
    assert (analysis_dir / "estimates.csv").is_file()
    assert (analysis_dir / "report.md").is_file()

    blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    assert [item["n_queries"] for item in blocks["depths"]] == [2, 2]
    assert all(0.8 <= item["factor_csv"] <= 1.4 for item in blocks["depths"])
