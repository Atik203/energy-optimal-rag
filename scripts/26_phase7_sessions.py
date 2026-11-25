#!/usr/bin/env python
"""26 - Phase 7 session-variance run (ICC input).

Three independent measurement sessions, each re-baselining idle and re-running the same
three depths. The point is not a new depth comparison; it is to ask how much of the
energy variance is between sessions rather than within one.

Design note: a session with one block per depth cannot support a variance decomposition,
so each block is also integrated as contiguous segments. Segment energies are ordinary
block estimates applied to a shorter span, so they are valid without re-measuring, and
they supply the within-session replicates that ICC needs.

Writes ``runs/<run_id>/sessions.json`` and appends to ``sessions.partial.jsonl``.
"""

from __future__ import annotations

import argparse
import json
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
from rag_energy.scoring import correctness  # noqa: E402

DEFAULT_CONFIG = "configs/runs/squad_qwen4b_p7_blocks_full.toml"
DEFAULT_RUN_ID = "squad_qwen4b_p7_sessions"
DEPTHS = (1, 4, 32)
IDLE_SECONDS = 10.0


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 session-variance run.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--sessions", type=int, default=3)
    parser.add_argument("--questions", type=int, default=200)
    parser.add_argument("--segments", type=int, default=4)
    parser.add_argument("--cooldown-s", type=float, default=120.0)
    parser.add_argument("--settle-s", type=float, default=120.0)
    parser.add_argument("--interval-ms", type=int, default=100)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    spec = load_run_spec(Path(args.config), root=root)
    config = spec.config
    nonce_chars = int(config.get("energy", {}).get("nonce_hex_chars", 10))

    if args.questions % args.segments:
        raise SystemExit("questions must divide evenly into segments")
    seg_size = args.questions // args.segments

    split = load_prepared_split(
        root / "data" / "processed",
        str(config.get("dataset", "squad")),
        str(config["id_split"]),
    )
    rows = list(split.questions.head(args.questions).itertuples(index=False))
    questions = {str(row.qid): str(row.question) for row in rows}
    golds = {str(row.qid): str(row.answer) for row in rows}
    index = RetrievalIndex.from_corpus(split.corpus)
    reader = _default_reader(config)

    run_dir = root / "runs" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    partial = run_dir / "sessions.partial.jsonl"
    done: dict[int, dict[str, Any]] = {}
    if partial.is_file() and not args.fresh:
        for line in partial.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                done[int(item["session"])] = item
    if done:
        print(f"resuming: {len(done)} session(s) on record")

    # Warm up so the model is resident before any session's idle baseline.
    for row in rows[:2]:
        qid = str(row.qid)
        retrieved = index.search(qid, questions[qid], max(DEPTHS))
        reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(nonce_chars))

    for session in range(args.sessions):
        if session in done:
            continue
        if session == 0:
            print(f"settling {args.settle_s:.0f} s before the first idle baseline")
            time.sleep(args.settle_s)
        idle = _measure_idle(NvmlSampler, args.interval_ms, IDLE_SECONDS)
        print(f"session {session}  idle {idle.mean_w:.2f} W (CV {idle.cv:.3f})")

        blocks: list[dict[str, Any]] = []
        for depth in DEPTHS:
            if args.cooldown_s > 0:
                time.sleep(args.cooldown_s)
            sampler = NvmlSampler(args.interval_ms)
            sampler.start()
            windows: list[tuple[str, float, float, int]] = []
            correct = 0
            try:
                for qid in [str(row.qid) for row in rows]:
                    retrieved = index.search(qid, questions[qid], depth)
                    start = time.monotonic()
                    result = reader.generate(
                        questions[qid], [p.text for p in retrieved], make_nonce(nonce_chars)
                    )
                    end = time.monotonic()
                    hit = correctness(result.text, golds[qid], "normalized_em")
                    correct += hit
                    windows.append((qid, start, end, hit))
            finally:
                samples = sampler.stop()

            total, _avg, duration = _integrate(samples, idle.mean_w)
            segments = []
            for seg in range(args.segments):
                chunk = windows[seg * seg_size : (seg + 1) * seg_size]
                seg_energy = _window_energy(
                    samples, chunk[0][1], chunk[-1][2], idle.mean_w, clip=False
                )
                segments.append(
                    {
                        "segment": seg,
                        "start_s": chunk[0][1],
                        "end_s": chunk[-1][2],
                        "energy_j": seg_energy,
                        "n": len(chunk),
                        "correct": sum(w[3] for w in chunk),
                    }
                )
            blocks.append(
                {
                    "k": depth,
                    "energy_j": total,
                    "duration_s": duration,
                    "correct": correct,
                    "n": len(windows),
                    "energy_per_query_j": total / len(windows),
                    "segments": segments,
                }
            )
            print(
                f"  k={depth:<3} {total:9.1f} J  {duration:6.1f} s  "
                f"{correct}/{len(windows)}  {total / len(windows):6.2f} J/q"
            )

        item = {
            "session": session,
            "started_utc": _utc_now(),
            "idle_mean_w": idle.mean_w,
            "idle_cv": idle.cv,
            "questions": args.questions,
            "segments_per_block": args.segments,
            "segment_size": seg_size,
            "blocks": blocks,
        }
        with partial.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item) + "\n")
        done[session] = item

    payload = {
        "schema_version": 1,
        "run_id": args.run_id,
        "created_utc": _utc_now(),
        "source_config": args.config,
        "n_sessions": len(done),
        "depths": list(DEPTHS),
        "questions_per_block": args.questions,
        "segments_per_block": args.segments,
        "segment_size": seg_size,
        "sessions": [done[i] for i in sorted(done)],
    }
    out = run_dir / "sessions.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(done)} sessions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
