#!/usr/bin/env python
"""35 - Phase 8 Step 3b dense reader run (GPU).

Reads the frozen dense rankings from ``data/processed/dense_minilm/`` (produced by
``scripts/31_qc_dense_precompute.py`, revision pinned in ``prereg/qc_prereg.md``) and
runs the same block protocol as the BM25 runs: randomized block order, 120 s cooldown,
idle sampled from the tail of each block's cooldown, discard-first queries, per-block
segment integrals.

Writes ``runs/<run_id>/``: ``blocks_design.json`` (same schema as
``scripts/22_run_blocks_design.py``, so ``scripts/23_phase7_analysis.py``-style
analyses apply), ``raw.csv`` (per-question rows), ``manifest.json``. Resume ledger:
``distractor``-style ``blocks_design.partial.jsonl`` with ``PROTOCOL`` tag.

Retriever energy is measured separately: per-block CPU retrieval wall time is
recorded and reported through the 20 W proxy, never folded into the GPU integral.

CPU work (question encoding) happens once before any block, outside all measured
windows. GPU only for the reader.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.blocks import BlockObservation  # noqa: E402
from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.energy.nvml_sampler import NvmlSampler  # noqa: E402
from rag_energy.runner import (  # noqa: E402
    _default_reader,
    _integrate,
    _measure_idle,
    load_run_spec,
    make_nonce,
)
from rag_energy.scoring import correctness  # noqa: E402

DEFAULT_CONFIG = "configs/runs/squad_qwen4b_qc_dense.toml"
IDLE_SECONDS = 10.0
PROTOCOL = "qc-dense-v1"
RETRIEVAL_PROXY_W = 20.0


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_resume(path: Path, protocol: str) -> dict[tuple[int, int], dict[str, Any]]:
    done: dict[tuple[int, int], dict[str, Any]] = {}
    if not path.is_file():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("protocol") != protocol:
            continue
        done[(int(item["k"]), int(item["replicate"]))] = item
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 8 dense reader run.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--replicates", type=int, default=None)
    parser.add_argument("--questions", type=int, default=None,
                        help="Override questions per block (scale testing).")
    parser.add_argument("--cooldown-s", type=float, default=None,
                        help="Override cooldown seconds (scale testing).")
    parser.add_argument("--interval-ms", type=int, default=100)
    parser.add_argument(
        "--settle-s",
        type=float,
        default=0.0,
        help="One-off settle before the first block's idle baseline. Smoke mode sets "
        "this to 45 s: with no inter-block cooldown the baseline would otherwise be "
        "sampled on a warm GPU and over-subtract every block.",
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--smoke", action="store_true",
                        help="One block, 3 questions, no cooldown, in a _smoke run directory.")
    args = parser.parse_args(argv)

    root = Path(args.root)
    spec = load_run_spec(Path(args.config), root=root)
    config = spec.config
    if str(config.get("retrieval", {}).get("backend", "")) != "dense":
        raise SystemExit("config retrieval.backend must be 'dense'")
    run_id = args.run_id or spec.run_id
    k_grid = [int(k) for k in config["k_grid"]]
    seed = int(config.get("seed", 20261115))
    nonce_chars = int(config.get("energy", {}).get("nonce_hex_chars", 10))
    interval_ms = int(args.interval_ms)

    blocks_cfg = config.get("blocks", {})
    replicates = int(blocks_cfg.get("replicates", 5)) if args.replicates is None else int(args.replicates)
    q_per_block = int(blocks_cfg.get("questions_per_block", 200)) if args.questions is None else int(args.questions)
    discard = int(blocks_cfg.get("discard_first", 2))
    cooldown = float(blocks_cfg.get("cooldown_s", 120.0)) if args.cooldown_s is None else float(args.cooldown_s)

    if args.smoke:
        run_id = f"{run_id}_smoke"
        replicates = 1
        q_per_block = 3
        discard = 0
        cooldown = 0.0
        args.settle_s = 45.0
        print("mode          smoke (one block, 3 questions, no cooldown)")

    split = load_prepared_split(
        root / "data" / "processed",
        str(config.get("dataset", "squad")),
        str(config["id_split"]),
    )
    all_qids = [str(q) for q in split.questions["qid"]]
    needed = replicates * q_per_block
    if len(all_qids) < needed:
        raise SystemExit(f"need {needed} questions, have {len(all_qids)}")
    shards = {
        r: all_qids[r * q_per_block : (r + 1) * q_per_block] for r in range(replicates)
    }
    questions = {str(row.qid): str(row.question) for row in split.questions.itertuples(index=False)}
    golds = split.questions.set_index("qid")["gold"].to_dict()

    # Frozen dense index (CPU, before any measurement).
    import numpy as np
    import pandas as pd

    dense_dir = root / "data" / "processed" / "dense_minilm"
    manifest = json.loads((dense_dir / "manifest.json").read_text(encoding="utf-8"))
    expected_rev = str(config.get("retrieval", {}).get("encoder_revision", ""))
    if manifest.get("revision_hash") != expected_rev:
        raise SystemExit(
            f"dense revision {manifest.get('revision_hash')} != preregistered {expected_rev}"
        )
    passage_ids = json.loads((dense_dir / "passage_ids.json").read_text(encoding="utf-8"))
    corpus = pd.read_parquet(root / "data" / "processed" / "squad_corpus.parquet")
    corpus = corpus.sort_values("passage_id").reset_index(drop=True)
    if [str(v) for v in corpus["passage_id"]] != [str(v) for v in passage_ids]:
        raise SystemExit("corpus order does not match frozen passage_ids")
    passage_texts = [str(v) for v in corpus["text"]]
    embeddings = np.load(dense_dir / "embeddings.npy")
    assert embeddings.shape[0] == len(passage_texts)

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from sentence_transformers import SentenceTransformer

    encoder = SentenceTransformer(
        str(config.get("retrieval", {}).get("encoder", "")),
        device="cpu",
        trust_remote_code=False,
    )
    print("encoding questions on CPU (outside all measured windows)")
    q_texts = [questions[qid] for r in range(replicates) for qid in shards[r]]
    q_embs = encoder.encode(
        q_texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False
    )
    q_vecs = {qid: q_embs[i] for i, qid in enumerate(
        [qid for r in range(replicates) for qid in shards[r]])}

    def retrieve(qid: str, k: int) -> tuple[list[str], float]:
        start = time.perf_counter()
        scores = embeddings @ q_vecs[qid]
        top = scores.argsort()[::-1][:k]
        wall = time.perf_counter() - start
        return [passage_texts[i] for i in top], wall

    index_reader = _default_reader(config)

    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    partial = run_dir / "blocks_design.partial.jsonl"
    done = {} if args.fresh else load_resume(partial, PROTOCOL)
    if done:
        print(f"resuming: {len(done)} block(s) on record ({PROTOCOL})")
    elif partial.is_file() and not args.fresh:
        print("no block on record matches this protocol; starting from block 0")

    for row in list(split.questions.head(2).itertuples(index=False)):
        qid = str(row.qid)
        ctx, _ = retrieve(qid, k_grid[-1])
        index_reader.generate(questions[qid], ctx, make_nonce(nonce_chars))

    order = [(k, r) for k in k_grid for r in range(replicates)]
    random.Random(seed).shuffle(order)

    rows: list[dict[str, Any]] = []
    observations: list[BlockObservation] = []
    started = _utc_now()
    if args.settle_s > 0 and not done:
        print(f"settling      {args.settle_s:.0f} s before the first idle baseline")
        time.sleep(args.settle_s)
    for position, (k, r) in enumerate(order):
        if (k, r) in done:
            obs = done[(k, r)]
            observations.append(
                BlockObservation(k=k, replicate=r, energy_j=float(obs["energy_j"]),
                                 correct=int(obs["correct"]), n=int(obs["n"]),
                                 duration_s=float(obs["duration_s"]))
            )
            continue
        settle = max(0.0, cooldown - IDLE_SECONDS)
        if settle > 0:
            print(f"cooldown      {cooldown:.0f} s before block {position} (k={k})")
            time.sleep(settle)
        idle = _measure_idle(NvmlSampler, interval_ms, IDLE_SECONDS)
        print(f"block {position:3d}  k={k:<3} idle {idle.mean_w:.2f} W (CV {idle.cv:.3f})")

        block_qids = shards[r]
        for _ in range(discard):
            ctx, _ = retrieve(block_qids[0], k)
            index_reader.generate(questions[block_qids[0]], ctx, make_nonce(nonce_chars))

        sampler = NvmlSampler(interval_ms)
        sampler.start()
        correct = 0
        retrieval_wall = 0.0
        block_rows: list[dict[str, Any]] = []
        try:
            for qid in block_qids:
                ctx, wall = retrieve(qid, k)
                retrieval_wall += wall
                result = index_reader.generate(questions[qid], ctx, make_nonce(nonce_chars))
                hit = correctness(result.text, str(golds[qid]), "normalized_em")
                correct += hit
                block_rows.append({
                    "run_id": run_id, "block_order": position, "replicate": r, "k": k,
                    "question_id": qid, "nonce": make_nonce(nonce_chars),
                    "correct_em": hit, "prediction": result.text,
                    "j_window_raw": "", "latency_s": round(result.latency_s, 6),
                    "prompt_tokens": result.prompt_tokens,
                    "retrieval_backend": "dense", "retrieval_wall_s": round(wall, 6),
                    "gpu_temp_c": "", "sm_clock_mhz": "", "valid": 1,
                })
        finally:
            samples = sampler.stop()
        total, _avg, duration = _integrate(samples, idle.mean_w)
        energy = max(total, 0.0)
        for row in block_rows:
            row["gpu_temp_c"] = samples[-1].temperature_c if samples else ""
            row["sm_clock_mhz"] = samples[-1].sm_clock_mhz if samples else ""
        rows.extend(block_rows)
        obs = BlockObservation(k=k, replicate=r, energy_j=energy, correct=correct,
                               n=len(block_qids), duration_s=duration)
        observations.append(obs)
        with partial.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "k": k, "replicate": r, "protocol": PROTOCOL,
                "energy_j": energy, "correct": correct, "n": len(block_qids),
                "duration_s": duration, "idle_mean_w": idle.mean_w,
                "retrieval_wall_s": retrieval_wall,
                "retrieval_proxy_j": retrieval_wall * RETRIEVAL_PROXY_W,
            }) + "\n")

    raw_path = run_dir / "raw.csv"
    with raw_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    totals: dict[int, dict[str, float]] = {}
    for o in observations:
        t = totals.setdefault(o.k, {"j": 0.0, "c": 0, "n": 0})
        t["j"] += o.energy_j
        t["c"] += o.correct
        t["n"] += o.n
    payload = {
        "run_id": run_id, "created_utc": _utc_now(), "started_utc": started,
        "estimand": "E(k) = sum_b J_block(k,b) / sum_b C(k,b)",
        "n_blocks": len(observations), "replicates": replicates,
        "questions_per_block": q_per_block, "disjoint_question_sets": True,
        "discard_first": discard, "cooldown_s": cooldown,
        "protocol": PROTOCOL, "retrieval_backend": "dense",
        "encoder_revision": manifest.get("revision_hash"),
        "depths": {str(k): {"energy_j": v["j"], "correct": int(v["c"]), "n": int(v["n"])} for k, v in sorted(totals.items())},
        "blocks": [
            {"k": o.k, "replicate": o.replicate, "energy_j": o.energy_j,
             "correct": o.correct, "n": o.n, "duration_s": o.duration_s}
            for o in observations
        ],
    }
    (run_dir / "blocks_design.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {run_dir} ({len(observations)} blocks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
