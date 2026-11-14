from __future__ import annotations

import csv
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(r"E:\PROJECT\energy-optimal-rag")
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.config import resolve_run_config
from rag_energy.data.loader import load_squad_split
from rag_energy.energy.integrate import idle_subtract, mean_power, trapezoid_joules
from rag_energy.energy.nonce import make_nonce
from rag_energy.energy.nvml_sampler import NvmlSampler
from rag_energy.readers.ollama_reader import OllamaConfig, OllamaReader
from rag_energy.retrieval.bm25 import build_index

spec = resolve_run_config(ROOT / "configs" / "runs" / "squad_qwen4b_p0.toml")
config = spec.data
split = load_squad_split(ROOT / "data" / "processed", "p0_golden")
index = build_index(list(zip(split.corpus["passage_id"], split.corpus["text"], strict=True)))
reader = OllamaReader(
    OllamaConfig(
        model=str(config["reader"]["model"]),
        num_ctx=int(config["reader"]["num_ctx"]),
        num_predict=int(config["reader"]["num_predict"]),
        temperature=float(config["reader"]["temperature"]),
        top_k=int(config["reader"]["top_k"]),
        seed=int(config["reader"]["seed"]),
        think=bool(config["reader"]["think"]),
    )
)
questions = split.questions.set_index("qid")["question"].to_dict()
raw_rows = list(
    csv.DictReader(
        (ROOT / "runs" / "golden_squad_qwen4b_p0" / "raw.csv").open(
            encoding="utf-8", newline=""
        )
    )
)
block_rows = [row for row in raw_rows if int(row["k"]) == 1][:20]
raw_sum = sum(float(row["j_gpu_raw"]) for row in block_rows)
print("raw_sum", round(raw_sum, 3), "mean", round(raw_sum / len(block_rows), 3))


def integrate(samples, idle_w):
    points = [(sample.t_s, sample.power_w) for sample in samples]
    gross = trapezoid_joules(points)
    duration = points[-1][0] - points[0][0] if len(points) >= 2 else 0.0
    return idle_subtract(gross, duration, idle_w), mean_power(gross, duration), duration


warm_questions = [str(row["question_id"]) for row in block_rows]
for index_number in range(120):
    qid = warm_questions[index_number % len(warm_questions)]
    question = str(questions[qid])
    retrieved = index.search(question, 32)
    reader.generate(question, [p.text for p in retrieved], make_nonce(10))

sampler = NvmlSampler(100)
sampler.start()
try:
    for row in block_rows:
        qid = str(row["question_id"])
        question = str(questions[qid])
        retrieved = index.search(question, 1)
        reader.generate(question, [p.text for p in retrieved], make_nonce(10))
finally:
    samples = sampler.stop()
energy, power, duration = integrate(samples, 17.026568)
print(
    f"hot block: energy={energy:.2f} power={power:.2f} duration={duration:.3f} "
    f"factor={energy / raw_sum:.3f}"
)
print("last_sample", samples[-1])
