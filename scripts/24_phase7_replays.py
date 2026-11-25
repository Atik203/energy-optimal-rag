#!/usr/bin/env python
"""24 - Phase 7 permutation replays (H-M1 adjudication).

Runs ``R >= 10`` continuous replays of the depth sweep. A replay issues every depth for
a question with no gaps and no cooldown, in a permuted order, so the whole sequence is
one block. Comparing each replay's per-depth energy against the block design's per-depth
energy isolates the window/carryover bias that makes the two estimators disagree.

The replay produces **energy only**; accuracy comes from the block run, which is the
registered denominator.

Writes ``runs/<block_run_id>/replays.json`` and appends each replay to
``replays.partial.jsonl`` so an interrupted run resumes.

CPU only for the analysis step; the run itself needs the GPU.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

DEFAULT_CONFIG = "configs/runs/squad_qwen4b_p7_blocks_full.toml"
IDLE_SECONDS = 10.0


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _plan(
    rows: list[Any], k_grid: list[int], questions: dict[str, str], seed: int, replay: int
) -> list[tuple[str, int]]:
    """One replay's (qid, depth) sequence: every depth once per question, permuted."""
    plan: list[tuple[str, int]] = []
    for order, row in enumerate(rows):
        qid = str(row.qid)
        depths = list(k_grid)
        random.Random(seed + replay * 1_000_003 + order).shuffle(depths)
        plan.extend((qid, depth) for depth in depths)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 permutation replays.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", default=None, help="Block run ID to compare against.")
    parser.add_argument("--replays", type=int, default=10)
    parser.add_argument("--questions", type=int, default=20)
    parser.add_argument("--interval-ms", type=int, default=100)
    parser.add_argument(
        "--settle-s",
        type=float,
        default=120.0,
        help="Cool-down before the idle baseline, so the baseline is a settled GPU.",
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--fresh", action="store_true", help="Ignore the resume ledger.")
    args = parser.parse_args()

    root = Path(args.root)
    spec = load_run_spec(Path(args.config), root=root)
    config = spec.config
    run_id = args.run_id or spec.run_id
    k_grid = [int(k) for k in config["k_grid"]]
    seed = int(config.get("seed", 20261115))
    nonce_chars = int(config.get("energy", {}).get("nonce_hex_chars", 10))

    run_dir = root / "runs" / run_id
    block_path = run_dir / "blocks_design.json"
    if not block_path.is_file():
        raise SystemExit(f"missing block design: {block_path}")
    block_payload = json.loads(block_path.read_text(encoding="utf-8"))

    split = load_prepared_split(
        root / "data" / "processed",
        str(config.get("dataset", "squad")),
        str(config["id_split"]),
    )
    rows = list(split.questions.head(args.questions).itertuples(index=False))
    questions = {str(row.qid): str(row.question) for row in rows}
    index = RetrievalIndex.from_corpus(split.corpus)
    reader = _default_reader(config)

    partial = run_dir / "replays.partial.jsonl"
    done: dict[int, dict[str, Any]] = {}
    if partial.is_file() and not args.fresh:
        for line in partial.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                done[int(item["replay"])] = item
    if done:
        print(f"resuming: {len(done)} replay(s) already on record")

    # One warm-up, shared by all replays: the model must be resident before any
    # measurement starts, and warm-up is not part of a replay's window.
    for row in rows[:2]:
        qid = str(row.qid)
        retrieved = index.search(qid, questions[qid], k_grid[-1])
        reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(nonce_chars))

    # Idle baseline, measured once on a settled GPU. Measuring it straight after the
    # warm-up reads 20+ W instead of ~15 W and would understate every replay.
    if done:
        first = done[min(done)]
        idle_w = float(first["idle_mean_w"])
        idle_cv = float(first["idle_cv"])
        print(f"idle baseline reused from the resume ledger: {idle_w:.2f} W")
    else:
        print(f"settling {args.settle_s:.0f} s before the idle baseline")
        time.sleep(args.settle_s)
        idle = _measure_idle(NvmlSampler, args.interval_ms, IDLE_SECONDS)
        idle_w = float(idle.mean_w)
        idle_cv = float(idle.cv)
        print(f"idle {idle_w:.2f} W (CV {idle_cv:.3f}) after {args.settle_s:.0f} s settle")

    for replay in range(args.replays):
        if replay in done:
            continue
        plan = _plan(rows, k_grid, questions, seed, replay)

        sampler = NvmlSampler(args.interval_ms)
        sampler.start()
        windows = []
        for qid, depth in plan:
            retrieved = index.search(qid, questions[qid], depth)
            start = time.monotonic()
            reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(nonce_chars))
            windows.append((qid, depth, start, time.monotonic()))
        samples = sampler.stop()

        total, _avg, duration = _integrate(samples, idle_w)
        by_depth = {k: 0.0 for k in k_grid}
        counts = {k: 0 for k in k_grid}
        for _, depth, start, end in windows:
            by_depth[depth] += _window_energy(samples, start, end, idle_w, clip=False)
            counts[depth] += 1

        item = {
            "replay": replay,
            "started_utc": _utc_now(),
            "n_queries": len(plan),
            "questions_per_depth": args.questions,
            "idle_mean_w": idle_w,
            "idle_cv": idle_cv,
            "replay_total_j": total,
            "replay_duration_s": duration,
            "replay_by_depth_j": {str(k): v for k, v in by_depth.items()},
            "counts_by_depth": {str(k): v for k, v in counts.items()},
        }
        with partial.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item) + "\n")
        done[replay] = item
        print(f"replay {replay:2d}  total {total:9.1f} J  {duration:6.1f} s  idle {idle_w:.2f} W")

    replays = [done[i] for i in sorted(done)]
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "created_utc": _utc_now(),
        "source_config": args.config,
        "n_replays": len(replays),
        "questions_per_replay": args.questions,
        "k_grid": k_grid,
        "seed": seed,
        "blocks_reference": {
            "run_id": block_payload.get("run_id", run_id),
            "questions_per_block": block_payload.get("questions_per_block"),
            "replicates": block_payload.get("replicates"),
        },
        "replays": replays,
    }
    out = run_dir / "replays.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(replays)} replays)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
