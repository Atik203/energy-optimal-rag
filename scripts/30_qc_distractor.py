#!/usr/bin/env python
"""30 - Phase 8 distractor dose-response run (H-overload causal test).

At fixed gold rank 1, append 0/1/3/7/15/31 distractors after the gold passage
(6 levels ~ k=1/2/4/8/16/32 in prompt length), paired by question across doses.
An optional position condition places the gold at rank 1/8/32 at fixed total
length to separate position sensitivity from pure length.

Measurement follows the Phase 7 session protocol: randomized block order, 120 s
cooldown separating blocks, idle baseline sampled from the tail of each block's
cooldown, ``PROTOCOL`` tag in the resume ledger, per-run analysis directory.
Per-query windows are diagnostic only; the block integral is the estimator.

GPU script: importing this module is CPU-only. ``main()`` drives the reader
and NVML and must pass ``--smoke`` first on every machine.

Writes ``runs/<run_id>/distractor.json``, appends to
``runs/<run_id>/distractor.partial.jsonl``, and writes the per-run summary to
``analysis/qc_distractor/<run_id>/``.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.scoring import correctness  # noqa: E402

DEFAULT_CONFIG = "configs/runs/squad_qwen4b_qc_distractor.toml"
DEFAULT_RUN_ID = "squad_qwen4b_qc_distractor"
DOSES = (0, 1, 3, 7, 15, 31)
POSITION_RANKS = (1, 8, 32)
FIXED_TOTAL = 32
IDLE_SECONDS = 10.0
# Bump when the measurement protocol changes. The resume ledger stores it and
# refuses entries from a different protocol, so a fixed method cannot inherit
# rows measured with the broken one.
PROTOCOL = "qc-distractor-v1"


@dataclass(frozen=True)
class DosePlanItem:
    """One scheduled block. ``order`` is the execution position."""

    order: int
    dose: int
    replicate: int
    position_rank: int = 1


def build_dose_plan(
    doses: tuple[int, ...] = DOSES,
    replicates: int = 1,
    *,
    seed: int,
    positions: tuple[int, ...] = (1,),
) -> list[DosePlanItem]:
    """Return a randomized schedule with ``replicates`` blocks per dose level.

    Randomizing the block order prevents thermal drift from being confounded
    with dose. The schedule is deterministic given ``seed``.
    """
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if not doses:
        raise ValueError("doses must not be empty")
    if not positions:
        raise ValueError("positions must not be empty")
    items = [
        (int(d), replicate, int(p))
        for d in doses
        for replicate in range(replicates)
        for p in positions
    ]
    random.Random(seed).shuffle(items)
    return [
        DosePlanItem(order=i, dose=d, replicate=r, position_rank=p)
        for i, (d, r, p) in enumerate(items)
    ]


def build_dose_context(gold_text: str, distractor_texts: list[str], dose: int) -> list[str]:
    """Gold-first context with ``dose`` distractors appended after the gold.

    Dose ``d`` uses ``d + 1`` passages, matching ``k = d + 1`` in prompt length.
    """
    if dose < 0:
        raise ValueError("dose must be non-negative")
    if len(distractor_texts) < dose:
        raise ValueError(f"need {dose} distractors, found {len(distractor_texts)}")
    return [gold_text, *distractor_texts[:dose]]


def build_position_context(
    gold_text: str, distractor_texts: list[str], total: int, gold_rank_1based: int
) -> list[str]:
    """Fixed-total-length context with the gold at a 1-based ``gold_rank_1based``.

    Separates position sensitivity from pure length: total prompt length is held
    at ``total`` while the gold moves.
    """
    if total <= 0:
        raise ValueError("total must be positive")
    if not 1 <= gold_rank_1based <= total:
        raise ValueError("gold rank must lie in [1, total]")
    if len(distractor_texts) < total - 1:
        raise ValueError(f"need {total - 1} distractors, found {len(distractor_texts)}")
    head = distractor_texts[: gold_rank_1based - 1]
    tail = distractor_texts[gold_rank_1based - 1 : total - 1]
    return [*head, gold_text, *tail]


def dose_accuracy_trend(
    dose_means: dict[int, float],
) -> dict[str, float]:
    """OLS slope of accuracy against log2(dose + 1) over the dose curve.

    The prereg trend test: a negative slope with a CI excluding flat supports
    H-overload. This point estimate is the CPU-only summary; the CI comes from
    the paired bootstrap over questions in the analysis step.
    """
    xs = [float((d + 1).bit_length() - 1) for d in dose_means]
    ys = [float(dose_means[d]) for d in dose_means]
    n = len(xs)
    if n < 2:
        return {"slope_per_doubling": float("nan"), "intercept": float("nan")}
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return {"slope_per_doubling": float("nan"), "intercept": mean_y}
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / denom
    return {"slope_per_doubling": slope, "intercept": mean_y - slope * mean_x}


def did_estimate(a_d4: float, a_d32: float, a_b4: float, a_b32: float) -> float:
    """Difference-in-differences: ``[A_d(4) - A_d(32)] - [A_b(4) - A_b(32)]``.

    Negative means dense retrieval degrades less than BM25 from k=4 to k=32
    (a smaller k=4→32 accuracy drop), i.e. the precision collapse travels
    with the retriever (H-dense). The sign convention is the prereg formula;
    do not flip it.
    """
    return (a_d4 - a_d32) - (a_b4 - a_b32)


def did_bootstrap_ci(
    dense_correct_4: list[int],
    dense_correct_32: list[int],
    bm25_correct_4: list[int],
    bm25_correct_32: list[int],
    *,
    resamples: int = 2000,
    seed: int = 20261115,
) -> dict[str, Any]:
    """Paired bootstrap CI for the dense-vs-BM25 DiD over questions."""
    n = len(dense_correct_4)
    if not (n == len(dense_correct_32) == len(bm25_correct_4) == len(bm25_correct_32)):
        raise ValueError("all four arms must cover the same questions")
    if n == 0:
        raise ValueError("arms must not be empty")

    def mean(values: list[int]) -> float:
        return sum(values) / len(values)

    point = did_estimate(
        mean(dense_correct_4),
        mean(dense_correct_32),
        mean(bm25_correct_4),
        mean(bm25_correct_32),
    )
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        draws.append(
            did_estimate(
                mean([dense_correct_4[i] for i in idx]),
                mean([dense_correct_32[i] for i in idx]),
                mean([bm25_correct_4[i] for i in idx]),
                mean([bm25_correct_32[i] for i in idx]),
            )
        )
    draws.sort()

    def quantile(q: float) -> float:
        position = q * (len(draws) - 1)
        lower = int(position)
        upper = min(lower + 1, len(draws) - 1)
        weight = position - lower
        return draws[lower] * (1 - weight) + draws[upper] * weight

    return {"point": point, "ci95": [quantile(0.025), quantile(0.975)], "n": n}


def _harmonize(energy_j: float, duration_s: float, idle_w: float, reference_w: float) -> float:
    """Re-express a block integral at a common idle baseline.

    Same convention as ``28_phase7_session_analysis._harmonize``: ``measured =
    gross - idle_w * duration``, so the gross is reconstructed and re-subtracted
    at ``reference_w``. Kept local so this script stays importable without the
    analysis module; equivalence is pinned by ``tests/test_qc_mechanism.py``.
    """
    if duration_s <= 0:
        return energy_j
    gross = energy_j + idle_w * duration_s
    return gross - reference_w * duration_s


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_resume(path: Path, protocol: str) -> dict[tuple[int, int, int], dict[str, Any]]:
    """Load a resume ledger, discarding rows measured with another protocol."""
    done: dict[tuple[int, int, int], dict[str, Any]] = {}
    if not path.is_file():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("protocol") != protocol:
            continue
        done[(int(item["dose"]), int(item["replicate"]), int(item.get("position", 1)))] = item
    return done


def summarize_dose_curve(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    """CPU-only summary: accuracy and J/query per dose plus the trend slope."""
    by_dose: dict[int, dict[str, float]] = {}
    for block in blocks:
        dose = int(block["dose"])
        entry = by_dose.setdefault(dose, {"correct": 0, "n": 0, "energy_j": 0.0})
        entry["correct"] += int(block["correct"])
        entry["n"] += int(block["n"])
        entry["energy_j"] += float(block["energy_j"])
    per_dose = {
        str(dose): {
            "accuracy": v["correct"] / v["n"] if v["n"] else 0.0,
            "j_per_query": v["energy_j"] / v["n"] if v["n"] else 0.0,
            "correct": v["correct"],
            "n": v["n"],
        }
        for dose, v in sorted(by_dose.items())
    }
    trend = dose_accuracy_trend({int(d): v["accuracy"] for d, v in per_dose.items()})
    return {"per_dose": per_dose, "trend": trend}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 8 distractor dose-response run.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--questions", type=int, default=500)
    parser.add_argument("--segments", type=int, default=4)
    parser.add_argument("--cooldown-s", type=float, default=120.0)
    parser.add_argument("--interval-ms", type=int, default=100)
    parser.add_argument(
        "--settle-s",
        type=float,
        default=0.0,
        help="One-off settle before the first block's idle baseline. Smoke mode sets "
        "this to 45 s: with no inter-block cooldown the baseline would otherwise be "
        "sampled on a warm GPU and over-subtract every block.",
    )
    parser.add_argument("--include-positions", action="store_true")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Two doses x 4 questions, no cooldown, in a _smoke run directory.",
    )
    args = parser.parse_args(argv)

    # Heavy imports stay inside main so the pure helpers remain CPU-importable
    # and the test module never touches the GPU, NVML, or the network.
    from rag_energy.data.loader import load_prepared_split
    from rag_energy.energy.nvml_sampler import NvmlSampler
    from rag_energy.retrieval.index import RetrievalIndex
    from rag_energy.runner import (
        _default_reader,
        _integrate,
        _measure_idle,
        _window_energy,
        load_run_spec,
        make_nonce,
    )

    root = Path(args.root)
    spec = load_run_spec(Path(args.config), root=root)
    config = spec.config
    nonce_chars = int(config.get("energy", {}).get("nonce_hex_chars", 10))
    seed = int(config.get("seed", 20261115))

    doses = list(DOSES)
    positions = list(POSITION_RANKS) if args.include_positions else [1]
    run_id = args.run_id
    if args.smoke:
        run_id = f"{run_id}_smoke"
        doses = [0, 1]
        positions = [1]
        args.replicates = 1
        args.questions = 4
        args.segments = 2
        args.cooldown_s = 0.0
        args.settle_s = 45.0
        print("mode          smoke (2 doses x 4 questions, no cooldown)")

    if args.questions % args.segments:
        raise SystemExit("questions must divide evenly into segments")
    seg_size = args.questions // args.segments

    plan = build_dose_plan(tuple(doses), args.replicates, seed=seed, positions=tuple(positions))
    print(f"run_id        {run_id}")
    print(f"doses         {doses} (gold rank 1; positions {positions})")
    print(f"blocks        {len(plan)}")
    print(f"per block     {args.questions} questions x {args.segments} segments")

    split = load_prepared_split(
        root / "data" / "processed",
        str(config.get("dataset", "squad")),
        str(config["id_split"]),
    )
    rows = list(split.questions.head(args.questions).itertuples(index=False))
    qids = [str(row.qid) for row in rows]
    questions = {str(row.qid): str(row.question) for row in rows}
    golds = split.questions.set_index("qid")["gold"].to_dict()
    index = RetrievalIndex.from_corpus(split.corpus)
    reader = _default_reader(config)

    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    partial = run_dir / "distractor.partial.jsonl"
    done = {} if args.fresh else load_resume(partial, PROTOCOL)
    if done:
        print(f"resuming: {len(done)} block(s) on record ({PROTOCOL})")

    max_passages = max(FIXED_TOTAL, max(doses) + 1)

    # Warm up so the model is resident before any block's idle baseline.
    for row in rows[:2]:
        qid = str(row.qid)
        retrieved = index.search(qid, questions[qid], 1)
        reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(nonce_chars))

    finished: list[dict[str, Any]] = [done[key] for key in sorted(done) for _ in [0]]
    if args.settle_s > 0 and not done:
        print(f"settling      {args.settle_s:.0f} s before the first idle baseline")
        time.sleep(args.settle_s)
    for item in plan:
        key = (item.dose, item.replicate, item.position_rank)
        if key in done:
            continue
        settle = max(0.0, args.cooldown_s - IDLE_SECONDS)
        if settle > 0:
            print(
                f"cooldown      {args.cooldown_s:.0f} s before dose={item.dose} "
                f"pos={item.position_rank}"
            )
            time.sleep(settle)
        idle = _measure_idle(NvmlSampler, args.interval_ms, IDLE_SECONDS)
        print(
            f"  dose={item.dose:<3} pos={item.position_rank:<2} "
            f"idle {idle.mean_w:.2f} W (CV {idle.cv:.3f})"
        )
        sampler = NvmlSampler(args.interval_ms)
        sampler.start()
        windows: list[tuple[str, float, float, int]] = []
        correct = 0
        try:
            for qid in qids:
                retrieved = index.search(qid, questions[qid], max_passages)
                texts = [p.text for p in retrieved]
                gold_text, distractors = texts[0], texts[1:]
                if item.position_rank == 1:
                    context = build_dose_context(gold_text, distractors, item.dose)
                else:
                    context = build_position_context(
                        gold_text, distractors, FIXED_TOTAL, item.position_rank
                    )
                start = time.monotonic()
                result = reader.generate(questions[qid], context, make_nonce(nonce_chars))
                end = time.monotonic()
                hit = correctness(result.text, str(golds[qid]), "normalized_em")
                correct += hit
                windows.append((qid, start, end, hit))
        finally:
            samples = sampler.stop()

        total, _avg, duration = _integrate(samples, idle.mean_w)
        segments = []
        for seg in range(args.segments):
            chunk = windows[seg * seg_size : (seg + 1) * seg_size]
            seg_energy = _window_energy(samples, chunk[0][1], chunk[-1][2], idle.mean_w, clip=False)
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
        record = {
            "dose": item.dose,
            "position": item.position_rank,
            "replicate": item.replicate,
            "protocol": PROTOCOL,
            "started_utc": _utc_now(),
            "energy_j": total,
            "duration_s": duration,
            "correct": correct,
            "n": len(windows),
            "energy_per_query_j": total / len(windows),
            "idle_mean_w": idle.mean_w,
            "idle_cv": idle.cv,
            "segments": segments,
        }
        with partial.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        done[key] = record
        finished.append(record)
        print(
            f"  dose={item.dose:<3} {total:9.1f} J  {duration:6.1f} s  "
            f"{correct}/{len(windows)}  {total / len(windows):6.2f} J/q"
        )

    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "created_utc": _utc_now(),
        "source_config": args.config,
        "protocol": PROTOCOL,
        "estimand": "accuracy dose curve at fixed gold rank 1; "
        "block energy per dose reported as a range",
        "doses": doses,
        "positions": positions,
        "n_blocks": len(finished),
        "questions_per_block": args.questions,
        "segments_per_block": args.segments,
        "segment_size": seg_size,
        "blocks": finished,
    }
    (run_dir / "distractor.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = summarize_dose_curve(finished)
    summary.update({"run_id": run_id, "protocol": PROTOCOL, "created_utc": _utc_now()})
    out_dir = root / "analysis" / "qc_distractor" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dose_curve.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# Phase 8 - distractor dose-response",
        "",
        f"Run `{run_id}` ({PROTOCOL}); {len(finished)} blocks, "
        f"{args.questions} paired questions per block.",
        "",
        "| dose | k-equiv | accuracy | J/query |",
        "|---:|---:|---:|---:|",
    ]
    for dose_s, values in summary["per_dose"].items():
        lines.append(
            f"| {dose_s} | {int(dose_s) + 1} | {values['accuracy']:.3f} | "
            f"{values['j_per_query']:.2f} |"
        )
    lines += [
        "",
        f"Trend slope: {summary['trend']['slope_per_doubling']:.4f} "
        "accuracy points per doubling of (dose + 1).",
        "",
    ]
    (out_dir / "dose_curve.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {run_dir / 'distractor.json'} and {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
