#!/usr/bin/env python
"""15 - Replay the sweep's depth permutation as one continuous block.

Compares the total energy of a replay (same 20 questions, same within-question
depth order as the sweep, no gaps) with the sum of the constant-depth block
energies. Diagnostic only.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.energy.nvml_sampler import NvmlSampler  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.runner import (  # noqa: E402
    _default_reader,
    _integrate,
    _measure_idle,
    _window_energy,
    load_run_spec,
    make_nonce,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay the sweep depth permutation.")
    parser.add_argument("--config", default="configs/runs/squad_qwen15b.toml")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--questions", type=int, default=20)
    parser.add_argument("--interval-ms", type=int, default=100)
    args = parser.parse_args()
    root = Path(args.root)
    spec = load_run_spec(Path(args.config), root=root)
    config = spec.config
    run_id = args.run_id or spec.run_id
    k_grid = [int(k) for k in config["k_grid"]]
    seed = int(config.get("seed", 20261115))
    split = load_prepared_split(
        root / "data" / "processed",
        str(config.get("dataset", "squad")),
        str(config["id_split"]),
    )
    rows = list(split.questions.head(args.questions).itertuples(index=False))
    questions = {str(row.qid): str(row.question) for row in rows}
    index = RetrievalIndex.from_corpus(split.corpus)
    reader = _default_reader(config)
    idle = _measure_idle(NvmlSampler, args.interval_ms, 10.0)
    idle_w = float(idle.mean_w)

    # Warm up two queries.
    for row in rows[:2]:
        qid = str(row.qid)
        retrieved = index.search(qid, questions[qid], k_grid[-1])
        reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(10))

    plan = []
    for order, row in enumerate(rows):
        qid = str(row.qid)
        depths = list(k_grid)
        random.Random(seed + order).shuffle(depths)
        for depth in depths:
            plan.append((qid, depth))

    sampler = NvmlSampler(args.interval_ms)
    sampler.start()
    windows = []
    for qid, depth in plan:
        retrieved = index.search(qid, questions[qid], depth)
        start = time.monotonic()
        reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(10))
        end = time.monotonic()
        windows.append((qid, depth, start, end))
    samples = sampler.stop()
    total, _avg, duration = _integrate(samples, idle_w)
    per_query = [_window_energy(samples, s, e, idle_w, clip=False) for _, _, s, e in windows]
    by_depth = {k: 0.0 for k in k_grid}
    for (_, depth, _, _), energy in zip(windows, per_query, strict=True):
        by_depth[depth] += energy
    blocks_path = root / "runs" / run_id / "blocks.json"
    block_sum = None
    if blocks_path.is_file():
        blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
        block_sum = sum(float(item["raw_sum_block_j"]) for item in blocks["depths"])
    payload = {
        "run_id": run_id,
        "n_queries": len(plan),
        "replay_total_j": total,
        "replay_duration_s": duration,
        "replay_by_depth_j": by_depth,
        "sum_constant_depth_block_j": block_sum,
        "ratio_replay_to_blocks": (total / block_sum) if block_sum else None,
    }
    out = root / "runs" / run_id / "replay.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
