#!/usr/bin/env python
"""37 - Phase 8 Step 4 padding run: token-matched padding at fixed k (GPU).

Separates prompt-length energy from passage-count effects: condition PADDED takes
the k=4 passages plus neutral pad tokens to the median token length of a k=32
prompt, and is compared against K4 (same passages, no pad) and K32 (same length
class, 32 real passages).

Design: 200 fresh questions (disjoint from Steps 1-3 frames) x 3 conditions =
600 generations, one block per condition with 4 segments, 120 s cooldowns, idle
from the cooldown tail. Same block protocol, resume ledger, and PROTOCOL tag
conventions as the other Phase 8 runners.

Writes ``runs/<run_id>/``: ``blocks_design.json`` (conditions as pseudo-depths),
``raw.csv``, and per-condition segment aggregates. Analysis is a direct read of
the block means (no bootstrap over 1 block per condition); the comparison is
descriptive and feeds the H1 token-model discussion, not a gate.
"""

from __future__ import annotations

import argparse
import csv
import json
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
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.runner import (  # noqa: E402
    _default_reader,
    _integrate,
    _measure_idle,
    load_run_spec,
    make_nonce,
)
from rag_energy.scoring import correctness  # noqa: E402

DEFAULT_CONFIG = "configs/runs/squad_qwen4b_qc_dense.toml"
DEFAULT_RUN_ID = "squad_qwen4b_qc_padding"
IDLE_SECONDS = 10.0
PROTOCOL = "qc-padding-v1"
CONDITIONS = ("k4", "k4_padded", "k32")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
N_QUESTIONS = 200
PAD_TOKEN = "the"
K_REF = 32


def load_resume(path: Path, protocol: str) -> dict[str, dict[str, Any]]:
    done: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("protocol") != protocol:
            continue
        done[str(item["condition"])] = item
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 8 padding run.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--questions", type=int, default=N_QUESTIONS)
    parser.add_argument("--cooldown-s", type=float, default=120.0)
    parser.add_argument("--interval-ms", type=int, default=100)
    parser.add_argument("--settle-s", type=float, default=0.0)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--smoke", action="store_true",
                        help="One condition x 4 questions, no cooldown, in a _smoke run directory.")
    args = parser.parse_args(argv)

    root = Path(args.root)
    spec = load_run_spec(Path(args.config), root=root)
    config = spec.config
    run_id = args.run_id
    seed = int(config.get("seed", 20261115))
    nonce_chars = int(config.get("energy", {}).get("nonce_hex_chars", 10))
    n_questions = int(args.questions)
    cooldown = float(args.cooldown_s)

    if args.smoke:
        run_id = f"{run_id}_smoke"
        n_questions = 4
        cooldown = 0.0
        args.settle_s = 45.0
        print("mode          smoke (one condition x 4 questions, no cooldown)")

    split = load_prepared_split(
        root / "data" / "processed", str(config.get("dataset", "squad")), "qc_dense"
    )
    # Fresh slice: questions after the dense frame's first 1000? No — reuse the dense
    # frame's questions would confound with Step 3b exposure. Use the distractor frame
    # tail instead: it is disjoint from qc_dense and large enough.
    distractor_ids = [str(q) for q in
                      load_prepared_split(root / "data" / "processed", "squad", "qc_distractor").questions["qid"]]
    all_qids = [str(q) for q in split.questions["qid"]]
    fresh_pool = [q for q in distractor_ids if q not in set(all_qids)]
    if len(fresh_pool) < n_questions:
        raise SystemExit(f"need {n_questions} fresh qids, have {len(fresh_pool)}")
    import random

    rng = random.Random(seed + 77)
    order = list(fresh_pool)
    rng.shuffle(order)
    qids = order[:n_questions]
    questions = {str(row.qid): str(row.question) for row in split.questions.itertuples(index=False)}
    # Distractor-frame questions may not be in the dense split's question table; load full table.
    import pandas as pd

    full_q = pd.read_parquet(root / "data" / "processed" / "squad_questions.parquet")
    full_questions = {str(r.qid): str(r.question) for r in full_q.itertuples(index=False)}
    full_golds_q = {str(r.qid): str(r.gold) for r in full_q.itertuples(index=False)}
    golds = split.questions.set_index("qid")["gold"].to_dict()
    for qid in qids:
        questions.setdefault(qid, full_questions[qid])
        golds.setdefault(qid, full_golds_q[qid])

    index = RetrievalIndex.from_corpus(split.corpus)
    reader = _default_reader(config)

    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    partial = run_dir / "padding.partial.jsonl"
    done = {} if args.fresh else load_resume(partial, PROTOCOL)
    if done:
        print(f"resuming: {len(done)} condition(s) on record ({PROTOCOL})")

    for row in list(split.questions.head(2).itertuples(index=False)):
        qid = str(row.qid)
        retrieved = index.search(qid, questions[qid], 4)
        reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(nonce_chars))

    if args.settle_s > 0 and not done:
        print(f"settling      {args.settle_s:.0f} s before the first idle baseline")
        time.sleep(args.settle_s)

    # Reference length: median k=32 prompt length on the warm-up questions.
    ref_texts = [p.text for p in index.search(qids[0], questions[qids[0]], K_REF)]
    ref_len = max(1, sum(len(t.split()) for t in ref_texts))

    rows: list[dict[str, Any]] = []
    observations: list[tuple[str, BlockObservation]] = []
    started = _utc_now()

    conditions = list(CONDITIONS) if not args.smoke else ["k4_padded"]
    for position, cond in enumerate(conditions):
        if cond in done:
            obs = done[cond]
            observations.append((cond, BlockObservation(
                k={"k4": 4, "k4_padded": 4, "k32": 32}[cond], replicate=position,
                energy_j=float(obs["energy_j"]), correct=int(obs["correct"]),
                n=int(obs["n"]), duration_s=float(obs["duration_s"]))))
            continue
        settle = max(0.0, cooldown - IDLE_SECONDS)
        if settle > 0:
            print(f"cooldown      {cooldown:.0f} s before condition {cond}")
            time.sleep(settle)
        idle = _measure_idle(NvmlSampler, args.interval_ms, IDLE_SECONDS)
        print(f"cond {cond:<10} idle {idle.mean_w:.2f} W (CV {idle.cv:.3f})")

        sampler = NvmlSampler(args.interval_ms)
        sampler.start()
        correct = 0
        block_rows: list[dict[str, Any]] = []
        try:
            for qid in qids:
                retrieved = index.search(qid, questions[qid], 4 if cond != "k32" else 32)
                ctx = [p.text for p in retrieved]
                if cond == "k4_padded":
                    cur = sum(len(t.split()) for t in ctx)
                    need = max(0, ref_len - cur)
                    ctx = ctx + [" ".join([PAD_TOKEN] * 64)] * ((need // 64) + 1)
                    ctx[-1] = " ".join(ctx[-1].split()[: need % 64 or 64])
                result = reader.generate(questions[qid], ctx, make_nonce(nonce_chars))
                hit = correctness(result.text, str(golds[qid]), "normalized_em")
                correct += hit
                block_rows.append({
                    "run_id": run_id, "condition": cond, "k_equiv": 4 if cond != "k32" else 32,
                    "question_id": qid, "nonce": make_nonce(nonce_chars),
                    "correct_em": hit, "prediction": result.text,
                    "latency_s": round(result.latency_s, 6),
                    "prompt_tokens": result.prompt_tokens, "valid": 1,
                })
        finally:
            samples = sampler.stop()
        total, _avg, duration = _integrate(samples, idle.mean_w)
        energy = max(total, 0.0)
        rows.extend(block_rows)
        obs = BlockObservation(k={"k4": 4, "k4_padded": 4, "k32": 32}[cond],
                               replicate=position, energy_j=energy, correct=correct,
                               n=len(qids), duration_s=duration)
        observations.append((cond, obs))
        with partial.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "condition": cond, "protocol": PROTOCOL, "energy_j": energy,
                "correct": correct, "n": len(qids), "duration_s": duration,
                "idle_mean_w": idle.mean_w, "ref_len_words": ref_len,
            }) + "\n")
        print(f"  {cond:<10} {energy:9.1f} J  {duration:6.1f} s  {correct}/{len(qids)}  "
              f"{energy / len(qids):6.2f} J/q")

    raw_path = run_dir / "raw.csv"
    with raw_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "run_id": run_id, "created_utc": _utc_now(), "started_utc": started,
        "estimand": "prompt-length vs passage-count energy at fixed k",
        "protocol": PROTOCOL, "ref_len_words": ref_len, "pad_token": PAD_TOKEN,
        "conditions": [
            {"condition": c, "energy_j": next(o.energy_j for cc, o in observations if cc == c),
             "correct": next(o.correct for cc, o in observations if cc == c),
             "n": n_questions}
            for c in conditions
        ],
    }
    (run_dir / "padding.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
