from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

ROOT = Path(r"E:\PROJECT\energy-optimal-rag")
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.config import resolve_run_config
from rag_energy.data.loader import load_squad_split
from rag_energy.energy.idle import summarize_idle
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
questions = list(split.questions.head(20).itertuples(index=False))


def integrate(samples, idle_w):
    points = [(sample.t_s, sample.power_w) for sample in samples]
    gross = trapezoid_joules(points)
    duration = points[-1][0] - points[0][0] if len(points) >= 2 else 0.0
    return idle_subtract(gross, duration, idle_w), mean_power(gross, duration), duration


sampler = NvmlSampler(100)
sampler.start()
time.sleep(30)
idle_samples = sampler.stop()
idle = summarize_idle([sample.power_w for sample in idle_samples])
print(f"idle mean={idle.mean_w:.3f} cv={idle.cv:.3f} n={idle.n}")


def per_query(gap_s: float):
    energies = []
    powers = []
    durations = []
    for row in questions:
        if gap_s:
            time.sleep(gap_s)
        sampler = NvmlSampler(100)
        sampler.start()
        try:
            reader.generate(
                str(row.question),
                [passage.text for passage in index.search(str(row.question), 0)],
                make_nonce(10),
            )
        finally:
            samples = sampler.stop()
        energy, power, duration = integrate(samples, idle.mean_w)
        energies.append(energy)
        powers.append(power)
        durations.append(duration)
    print(
        f"per_query gap={gap_s}: sum={sum(energies):.2f} mean_j={statistics.mean(energies):.3f} "
        f"power={statistics.mean(powers):.2f} duration={statistics.mean(durations):.3f}"
    )
    return sum(energies)


raw_nogap = per_query(0.0)
raw_gap = per_query(0.2)

sampler = NvmlSampler(100)
sampler.start()
try:
    for row in questions:
        reader.generate(
            str(row.question),
            [passage.text for passage in index.search(str(row.question), 0)],
            make_nonce(10),
        )
finally:
    samples = sampler.stop()
block_energy, block_power, block_duration = integrate(samples, idle.mean_w)
print(
    f"block: energy={block_energy:.2f} power={block_power:.2f} duration={block_duration:.3f} "
    f"factor_nogap={block_energy / raw_nogap:.3f} factor_gap={block_energy / raw_gap:.3f}"
)
