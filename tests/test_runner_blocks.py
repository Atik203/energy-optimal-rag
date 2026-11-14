"""Block-calibration tests with a fake reader and sampler."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("pyarrow")

import pandas as pd

from rag_energy.energy.nvml_sampler import PowerSample
from rag_energy.readers.base import ReaderResult
from rag_energy.runner import RAW_FIELDS, run_block_calibration


class FakeReader:
    name = "fake"

    def generate(self, question: str, passages: list[str], nonce: str) -> ReaderResult:
        return ReaderResult(
            text="alpha",
            latency_s=0.01,
            prompt_tokens=10,
            output_tokens=1,
            load_s=0.0,
        )


class BlockSampler:
    def __init__(self, interval_ms: int = 10) -> None:
        self.interval_ms = interval_ms
        self._started = 0.0

    def start(self) -> None:
        self._started = time.monotonic()

    def stop(self) -> list[PowerSample]:
        # 50 W over 0.2 s = 10 J.
        return [
            PowerSample(t_s=self._started, power_w=50.0),
            PowerSample(t_s=self._started + 0.2, power_w=50.0),
        ]


def _write_processed(tmp_path: Path) -> Path:
    processed = tmp_path / "processed"
    processed.mkdir()
    rows = [
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
    pd.DataFrame(rows).to_parquet(processed / "squad_questions.parquet", index=False)
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


def _write_raw(tmp_path: Path, per_row_j: float) -> Path:
    raw = tmp_path / "runs" / "test_run" / "raw.csv"
    raw.parent.mkdir(parents=True)
    rows = []
    for depth in (0, 2):
        for order, qid in enumerate(("q1", "q2")):
            row = {field: "" for field in RAW_FIELDS}
            row.update(
                {
                    "run_id": "test_run",
                    "question_id": qid,
                    "question_order": order,
                    "k": depth,
                    "order_in_question": 0,
                    "nonce": f"n{depth}{order}",
                    "correct_em": 1,
                    "correct_lenient": 1,
                    "f1": 1.0,
                    "prediction": "alpha",
                    "gold": "alpha",
                    "j_gpu_raw": per_row_j,
                    "j_gpu_calibrated": per_row_j,
                    "j_retrieval_proxy": 0.0,
                    "j_total": per_row_j,
                    "valid": 1,
                }
            )
            rows.append(row)
    with raw.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return raw


def test_run_block_calibration_writes_factors_and_calibrated_values(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path)
    config_path = _write_config(tmp_path)
    raw = _write_raw(tmp_path, per_row_j=5.0)

    blocks_path = run_block_calibration(
        config_path,
        root=tmp_path,
        processed_dir=processed,
        out_root=tmp_path / "runs",
        reader=FakeReader(),
        sampler_factory=BlockSampler,
        idle_power_w=0.0,
    )

    blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    assert len(blocks["depths"]) == 2
    assert all(item["factor"] == pytest.approx(1.0) for item in blocks["depths"])
    assert all(item["block_energy_j"] == pytest.approx(10.0) for item in blocks["depths"])

    rows = list(csv.DictReader(raw.open(encoding="utf-8", newline="")))
    assert all(float(row["j_gpu_calibrated"]) == pytest.approx(5.0) for row in rows)


def test_run_block_calibration_rejects_out_of_range_factor(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path)
    config_path = _write_config(tmp_path)
    _write_raw(tmp_path, per_row_j=0.5)

    with pytest.raises(ValueError, match="factor"):
        run_block_calibration(
            config_path,
            root=tmp_path,
            processed_dir=processed,
            out_root=tmp_path / "runs",
            reader=FakeReader(),
            sampler_factory=BlockSampler,
            idle_power_w=0.0,
        )
