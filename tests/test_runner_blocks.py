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
from rag_energy.runner import RAW_FIELDS, _window_energy, run_block_calibration


class FakeReader:
    name = "fake"

    def generate(self, question: str, passages: list[str], nonce: str) -> ReaderResult:
        time.sleep(0.1)
        return ReaderResult(
            text="alpha",
            latency_s=0.1,
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
        now = time.monotonic()
        count = max(2, int((now - self._started) / 0.01) + 1)
        samples = [
            PowerSample(t_s=self._started + index * 0.01, power_w=50.0) for index in range(count)
        ]
        samples.append(PowerSample(t_s=now, power_w=50.0))
        return samples


class SpikeSampler(BlockSampler):
    def stop(self) -> list[PowerSample]:
        samples = super().stop()
        last = samples[-1].t_s
        # A normal boundary sample, then an out-of-window spike. The spike is
        # included in the block total but not in any query window.
        samples.append(PowerSample(t_s=last + 0.01, power_w=50.0))
        samples.append(PowerSample(t_s=last + 0.11, power_w=500.0))
        return samples


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
                    "j_retrieval_proxy": 7.0,
                    "j_total": per_row_j + 7.0,
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
    raw = _write_raw(tmp_path, per_row_j=5.5)

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
    factors = {item["k"]: item["factor_csv"] for item in blocks["depths"]}
    for item in blocks["depths"]:
        factor = item["factor_csv"]
        assert 0.8 <= factor <= 1.4
        assert item["factor_block"] == pytest.approx(1.0, abs=0.1)
        assert item["consistency"] == pytest.approx(1.0 / factor, rel=0.1)
        assert item["block_energy_j"] > 0
        assert item["raw_sum_csv_j"] == pytest.approx(11.0)
        assert item["raw_sum_block_j"] > 0

    rows = list(csv.DictReader(raw.open(encoding="utf-8", newline="")))
    for row in rows:
        factor = factors[int(row["k"])]
        assert float(row["j_gpu_calibrated"]) == pytest.approx(5.5 * factor, rel=1e-6)
        assert float(row["j_total"]) == pytest.approx(5.5 * factor + 7.0, rel=1e-6)


def test_window_energy_integrates_exact_interval_without_neighbor_leak() -> None:
    samples = [PowerSample(t_s=0.0, power_w=10.0), PowerSample(t_s=1.0, power_w=10.0)]

    energy = _window_energy(samples, 0.2, 0.4, idle_power_w=0.0)

    assert energy == pytest.approx(2.0)


def test_window_energy_does_not_borrow_a_spike_after_the_end() -> None:
    samples = [
        PowerSample(t_s=0.0, power_w=10.0),
        PowerSample(t_s=0.5, power_w=10.0),
        PowerSample(t_s=0.6, power_w=500.0),
    ]

    energy = _window_energy(samples, 0.1, 0.55, idle_power_w=0.0, clip=False)

    assert energy == pytest.approx(4.5)


def test_run_block_calibration_rejects_sweep_block_mismatch(tmp_path: Path) -> None:
    processed = _write_processed(tmp_path)
    config_path = _write_config(tmp_path)
    _write_raw(tmp_path, per_row_j=100.0)

    with pytest.raises(ValueError, match="block factor"):
        run_block_calibration(
            config_path,
            root=tmp_path,
            processed_dir=processed,
            out_root=tmp_path / "runs",
            reader=FakeReader(),
            sampler_factory=BlockSampler,
            idle_power_w=0.0,
        )


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
            sampler_factory=SpikeSampler,
            idle_power_w=0.0,
        )
