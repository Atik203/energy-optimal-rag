#!/usr/bin/env python
"""22 - Phase 7 block-design sweep.

Runs the randomized block schedule that replaces the falsified per-query window
estimator. Each block is one depth, ``questions_per_block`` queries, measured as
a single integrated window with an idle baseline taken once at the start.

Outputs, under ``runs/<run_id>/``:

* ``blocks_design.json`` - per-block energy, correctness, temperature, clock, and
  the aggregated per-depth estimates with a cluster bootstrap.
* ``raw.csv`` - one row per answered query, for traceability only. These rows are
  **not** the estimator.
* ``manifest.json`` - full environment record, including the fields the P0/P1
  manifests were missing.

Use ``--plan-only`` to print the schedule and the estimated cost without touching
the GPU.

The script never downloads weights, never changes the power mode, and stops if
the idle baseline is unstable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.blocks import (  # noqa: E402
    BlockObservation,
    bootstrap_savings,
    build_block_plan,
    cv_by_depth,
    depth_totals,
)
from rag_energy.config import resolve_run_config  # noqa: E402
from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.energy.idle import summarize_idle  # noqa: E402
from rag_energy.energy.integrate import idle_subtract, mean_power, trapezoid_joules  # noqa: E402
from rag_energy.energy.nonce import make_nonce  # noqa: E402
from rag_energy.energy.nvml_sampler import NvmlSampler  # noqa: E402
from rag_energy.readers.base import Reader  # noqa: E402
from rag_energy.registry import append_registry_row  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.scoring import correctness  # noqa: E402

RAW_FIELDS = (
    "run_id",
    "block_order",
    "replicate",
    "k",
    "question_id",
    "nonce",
    "correct_em",
    "prediction",
    "j_window_raw",
    "latency_s",
    "prompt_tokens",
    "gpu_temp_c",
    "sm_clock_mhz",
    "valid",
)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    return completed.stdout.strip()


def _nvidia_smi(field: str) -> str:
    try:
        completed = subprocess.run(
            ["nvidia-smi", f"--query-gpu={field}", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    value = completed.stdout.strip().splitlines()
    return value[0].strip() if value else "unknown"


def _environment(config: dict[str, Any]) -> dict[str, str]:
    reader = config.get("reader", {})
    return {
        "nvidia_driver": _nvidia_smi("driver_version"),
        "cuda_version": _nvidia_smi("compute_cap"),
        "gpu_name": _nvidia_smi("name"),
        "power_mode": str(config.get("measurement", {}).get("power_mode", "unknown")),
        "batch_size": str(config.get("measurement", {}).get("batch_size", 1)),
        "concurrent_jobs": str(config.get("measurement", {}).get("concurrent_jobs", False)),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "reader_backend": str(reader.get("backend", "")),
        "reader_model": str(reader.get("model", "")),
        "num_ctx": str(reader.get("num_ctx", "")),
        "quantization": str(reader.get("quantization", "")),
        "ollama_version": "unknown",
        "ambient_temp_c": "unknown",
    }


def _reader(config: dict[str, Any]) -> Reader:
    reader = config.get("reader", {})
    backend = str(reader.get("backend", "ollama"))
    if backend == "hf":
        from rag_energy.readers.hf_reader import HFConfig, HFReader

        return HFReader(
            HFConfig(
                model=str(reader.get("model", "Qwen/Qwen2.5-1.5B-Instruct")),
                device=str(reader.get("device", "cuda")),
                dtype=str(reader.get("dtype", "float16")),
                num_ctx=int(reader.get("num_ctx", 4096)),
                num_predict=int(reader.get("num_predict", 24)),
                temperature=float(reader.get("temperature", 0.0)),
                top_k=int(reader.get("top_k", 1)),
                seed=int(reader.get("seed", 42)),
            )
        )
    from rag_energy.readers.ollama_reader import OllamaConfig, OllamaReader

    return OllamaReader(
        OllamaConfig(
            model=str(reader.get("model", "qwen3.5:4b")),
            host=str(reader.get("host", "http://127.0.0.1:11434")),
            num_ctx=int(reader.get("num_ctx", 4096)),
            num_predict=int(reader.get("num_predict", 24)),
            temperature=float(reader.get("temperature", 0.0)),
            top_k=int(reader.get("top_k", 1)),
            seed=int(reader.get("seed", 42)),
            think=bool(reader.get("think", False)),
            keep_alive=str(reader.get("keep_alive", "2h")),
            timeout_s=float(reader.get("timeout_s", 120.0)),
        )
    )


def _block_energy(samples: list[Any], idle_power_w: float) -> tuple[float, float, float]:
    if len(samples) < 2:
        raise RuntimeError("sampler returned fewer than two samples")
    raw = trapezoid_joules(samples)
    energy = idle_subtract(raw, samples, idle_power_w)
    power = mean_power(samples)
    duration = samples[-1].t_s - samples[0].t_s
    return max(energy, 0.0), power, duration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 7 block-design sweep.")
    parser.add_argument("--config", default="configs/runs/squad_qwen4b_p7_blocks.toml")
    parser.add_argument("--plan-only", action="store_true", help="Print the plan and stop.")
    parser.add_argument("--limit-blocks", type=int, default=None, help="Stop after N blocks.")
    args = parser.parse_args(argv)

    resolved = resolve_run_config(Path(args.config), root=ROOT)
    config = resolved.data
    run_id = resolved.run_id
    k_grid = [int(k) for k in config["k_grid"]]
    replicates = int(config.get("blocks", {}).get("replicates", 5))
    q_per_block = int(config.get("energy", {}).get("block_size", 20))
    discard = int(config.get("blocks", {}).get("discard_first", 2))
    cooldown = float(config.get("blocks", {}).get("cooldown_s", 120.0))
    seed = int(config.get("seed", 20261115))
    interval_ms = int(config.get("energy", {}).get("sample_interval_ms", 100))
    idle_seconds = float(config.get("energy", {}).get("idle_baseline_s", 60.0))
    nonce_hex = int(config.get("energy", {}).get("nonce_hex_chars", 10))
    candidate = int(config.get("blocks", {}).get("candidate_depth", 4))
    reference = int(config.get("blocks", {}).get("reference_depth", 32))

    plan = build_block_plan(k_grid, replicates, seed=seed)
    n_generations = len(plan) * (q_per_block + discard)
    print(f"run_id        {run_id}")
    print(f"depths        {k_grid}")
    print(f"blocks        {len(plan)} ({replicates} per depth)")
    print(f"per block     {q_per_block} measured + {discard} discarded")
    print(f"generations   {n_generations}")
    print(f"cooldown      {cooldown:.0f} s between blocks")
    print(f"estimated     {n_generations * 1.2 / 3600:.1f} GPU-h of decoding + cooldowns")
    if args.plan_only:
        for item in plan:
            print(f"  {item.order:03d}  k={item.k:<2}  replicate={item.replicate}")
        return 0

    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_path = run_dir / "raw.csv"

    split = load_prepared_split(
        ROOT / "data" / "processed",
        str(config.get("dataset", "squad")),
        str(config.get("id_split", "p1_primary")),
    )
    questions = split.questions.set_index("qid")["question"].to_dict()
    golds = split.questions.set_index("qid")["gold"].to_dict()
    index = RetrievalIndex.from_corpus(split.corpus)
    block_qids = [str(q) for q in split.questions.head(q_per_block)["qid"]]
    if len(block_qids) < q_per_block:
        raise SystemExit(f"need {q_per_block} questions, found {len(block_qids)}")

    reader = _reader(config)
    idle_stats = summarize_idle(
        [sample.power_w for sample in _idle_samples(interval_ms, idle_seconds)]
    )
    idle_max_cv = float(config.get("energy", {}).get("idle_max_cv", 0.20))
    if idle_stats.cv > idle_max_cv:
        raise SystemExit(
            f"idle CV {idle_stats.cv:.4f} exceeds {idle_max_cv:.2f}; stabilize the machine first"
        )
    idle_power_w = idle_stats.mean_w
    print(f"idle          {idle_power_w:.2f} W (CV {idle_stats.cv:.3f})")

    observations: list[BlockObservation] = []
    rows: list[dict[str, Any]] = []
    started = _utc_now()
    for item in plan:
        if args.limit_blocks is not None and len(observations) >= args.limit_blocks:
            break
        if cooldown > 0:
            print(f"cooldown      {cooldown:.0f} s before block {item.order} (k={item.k})")
            time.sleep(cooldown)
        # Discard: return the device to the measured steady state.
        for _ in range(discard):
            qid = block_qids[0]
            retrieved = index.search(qid, str(questions[qid]), item.k)
            reader.generate(str(questions[qid]), [p.text for p in retrieved], make_nonce(nonce_hex))

        sampler = NvmlSampler(interval_ms)
        sampler.start()
        correct = 0
        block_rows: list[dict[str, Any]] = []
        try:
            for qid in block_qids:
                retrieved = index.search(qid, str(questions[qid]), item.k)
                result = reader.generate(
                    str(questions[qid]), [p.text for p in retrieved], make_nonce(nonce_hex)
                )
                hit = correctness(result.text, str(golds[qid]), "normalized_em")
                correct += hit
                block_rows.append(
                    {
                        "run_id": run_id,
                        "block_order": item.order,
                        "replicate": item.replicate,
                        "k": item.k,
                        "question_id": qid,
                        "nonce": make_nonce(nonce_hex),
                        "correct_em": hit,
                        "prediction": result.text,
                        "j_window_raw": "",
                        "latency_s": round(result.latency_s, 6),
                        "prompt_tokens": result.prompt_tokens,
                        "gpu_temp_c": "",
                        "sm_clock_mhz": "",
                        "valid": 1,
                    }
                )
        finally:
            samples = sampler.stop()
        energy_j, power_w, duration_s = _block_energy(samples, idle_power_w)
        for row in block_rows:
            row["gpu_temp_c"] = samples[-1].temperature_c if samples else ""
            row["sm_clock_mhz"] = samples[-1].sm_clock_mhz if samples else ""
        rows.extend(block_rows)
        observations.append(
            BlockObservation(
                k=item.k,
                replicate=item.replicate,
                energy_j=energy_j,
                correct=correct,
                n=len(block_qids),
                duration_s=duration_s,
            )
        )
        print(
            f"block {item.order:03d}  k={item.k:<2}  E={energy_j:7.2f} J  "
            f"{correct}/{len(block_qids)}  {power_w:5.1f} W  {duration_s:5.1f} s"
        )

    with raw_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    totals = depth_totals(observations)
    boot = (
        bootstrap_savings(observations, candidate, reference, seed=seed)
        if candidate in totals and reference in totals
        else None
    )
    payload = {
        "run_id": run_id,
        "phase": config.get("phase", "P7"),
        "created_utc": _utc_now(),
        "started_utc": started,
        "estimand": "E(k) = sum_b J_block(k,b) / sum_b C(k,b)",
        "n_blocks": len(observations),
        "replicates": replicates,
        "questions_per_block": q_per_block,
        "discard_first": discard,
        "cooldown_s": cooldown,
        "idle": {
            "mean_w": idle_stats.mean_w,
            "sd_w": idle_stats.sd_w,
            "cv": idle_stats.cv,
            "n": idle_stats.n,
        },
        "depths": {str(k): v for k, v in sorted(totals.items())},
        "cv_by_depth": {str(k): v for k, v in sorted(cv_by_depth(observations).items())},
        "savings": None
        if boot is None
        else {
            "candidate_depth": candidate,
            "reference_depth": reference,
            "point": boot["point"],
            "ci95": boot["ci"],
            "n_valid": boot["n_valid"],
        },
        "blocks": [
            {
                "k": b.k,
                "replicate": b.replicate,
                "energy_j": b.energy_j,
                "correct": b.correct,
                "n": b.n,
                "duration_s": b.duration_s,
            }
            for b in observations
        ],
    }
    (run_dir / "blocks_design.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    manifest = {
        "run_id": run_id,
        "phase": config.get("phase", "P7"),
        "dataset": config.get("dataset", ""),
        "id_split": config.get("id_split", ""),
        "k_grid": k_grid,
        "seed": seed,
        "started_utc": started,
        "finished_utc": _utc_now(),
        "config_path": str(Path(args.config)),
        "config_sha256": _sha256(Path(args.config)),
        "prereg_sha256": _sha256(ROOT / "prereg" / "measurement_hardening_prereg.md")
        if (ROOT / "prereg" / "measurement_hardening_prereg.md").is_file()
        else "missing",
        "git_commit": _git_commit(),
        "environment": _environment(config),
        "counts": {
            "blocks": len(observations),
            "generations": len(rows) + len(observations) * discard,
            "questions_per_block": q_per_block,
        },
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    saving_note = f"{payload['savings']['point']:.4f}" if payload["savings"] else "not estimated"
    append_registry_row(
        ROOT / "runs" / "registry.csv",
        {
            "run_id": run_id,
            "timestamp_utc": started,
            "phase": config.get("phase", "P7"),
            "dataset": config.get("dataset", ""),
            "reader": str(config.get("reader", {}).get("model", "")),
            "retriever": str(config.get("retrieval", {}).get("backend", "bm25")),
            "k_grid": "|".join(str(k) for k in k_grid),
            "n_questions": q_per_block,
            "seed": str(seed),
            "energy_sampler": "nvml",
            "status": "completed",
            "git_commit": _git_commit(),
            "config_path": str(Path(args.config)),
            "config_sha256": _sha256(Path(args.config)),
            "prereg_sha256": manifest["prereg_sha256"],
            "model_digest": "unknown",
            "raw_csv": "raw.csv",
            "notes": f"block design: {len(observations)} blocks; saving {saving_note}",
        },
    )

    if payload["savings"]:
        print(
            f"savings       {100 * payload['savings']['point']:.2f}% "
            f"[{100 * payload['savings']['ci95'][0]:.2f}, {100 * payload['savings']['ci95'][1]:.2f}]"
        )
    print(f"wrote {run_dir}")
    return 0


def _idle_samples(interval_ms: int, seconds: float) -> list[Any]:
    sampler = NvmlSampler(interval_ms)
    sampler.start()
    try:
        time.sleep(seconds)
    finally:
        samples = sampler.stop()
    return samples


if __name__ == "__main__":
    raise SystemExit(main())
