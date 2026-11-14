"""Run orchestration.

The runner owns the order of operations for one depth sweep:

1. load and validate the run config,
2. build the BM25 index once,
3. warm up, measure idle, run randomized blocks of questions at each depth,
4. attach the per-request nonce, record raw rows,
5. run block calibration and write ``blocks.json``,
6. register the run in ``runs/registry.csv``.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag_energy.config import REPO_ROOT, load_toml, resolve_run_config
from rag_energy.data.loader import SquadSplit, load_squad_split
from rag_energy.energy.idle import IdleStats, summarize_idle
from rag_energy.energy.integrate import idle_subtract, mean_power, trapezoid_joules
from rag_energy.energy.nonce import make_nonce
from rag_energy.energy.nvml_sampler import NvmlSampler, PowerSample
from rag_energy.readers.base import Reader, ReaderError
from rag_energy.registry import append_registry_row, update_registry_status
from rag_energy.retrieval.bm25 import BM25Index, build_index
from rag_energy.retrieval.proxy_energy import cpu_retrieval_joules
from rag_energy.scoring import correctness, token_f1

RAW_FIELDS: tuple[str, ...] = (
    "run_id",
    "question_id",
    "question_order",
    "k",
    "order_in_question",
    "nonce",
    "correct_em",
    "correct_lenient",
    "f1",
    "prediction",
    "gold",
    "j_gpu_raw",
    "j_gpu_calibrated",
    "j_retrieval_proxy",
    "j_total",
    "latency_s",
    "prompt_tokens",
    "output_tokens",
    "load_s",
    "prefill_s",
    "eval_s",
    "gpu_temp_c",
    "sm_clock_mhz",
    "power_mean_w",
    "valid",
    "invalid_reason",
)


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    config_path: Path
    config: dict[str, Any]
    config_sha256: str = ""
    sources: tuple[Path, ...] = ()


def load_run_spec(config_path: Path, root: Path | None = None) -> RunSpec:
    """Resolve base, run, and optional grid, returning a typed spec."""
    resolved = resolve_run_config(config_path, root=root)
    return RunSpec(
        run_id=resolved.run_id,
        config_path=resolved.config_path,
        config=resolved.data,
        config_sha256=resolved.config_sha256,
        sources=resolved.sources,
    )


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_commit(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return completed.stdout.strip()


def _prereg_sha256(root: Path) -> str:
    config_path = root / "configs" / "analysis" / "prereg.toml"
    if not config_path.is_file():
        return ""
    try:
        config = load_toml(config_path)
    except Exception:
        return ""
    if not config.get("frozen", False):
        return ""
    digest = hashlib.sha256()
    for path in (
        root / "prereg" / "PREREGISTRATION.md",
        root / "prereg" / "analysis_plan.md",
    ):
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _default_reader(config: dict[str, Any]) -> Reader:
    reader = config.get("reader", {})
    if reader.get("backend") != "ollama":
        raise NotImplementedError("only the Ollama reader is implemented in P0")
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


def _model_digest(reader: Reader, config: dict[str, Any]) -> str:
    host = str(config.get("reader", {}).get("host", "http://127.0.0.1:11434"))
    model = str(config.get("reader", {}).get("model", ""))
    try:
        import requests

        response = requests.get(f"{host.rstrip('/')}/api/tags", timeout=5)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return "unknown"
    for item in payload.get("models", []):
        if item.get("name") == model or item.get("model") == model:
            return str(item.get("digest", "unknown"))
    return "unknown"


def _measure_idle(
    sampler_factory: Callable[[int], Any],
    interval_ms: int,
    seconds: float,
) -> IdleStats:
    if seconds <= 0:
        raise ValueError("idle_baseline_s must be positive")
    sampler = sampler_factory(interval_ms)
    sampler.start()
    try:
        time.sleep(seconds)
    finally:
        samples = sampler.stop()
    return summarize_idle([sample.power_w for sample in samples])


def _integrate(samples: Sequence[PowerSample], idle_power_w: float) -> tuple[float, float, float]:
    points = [(sample.t_s, sample.power_w) for sample in samples]
    gross = trapezoid_joules(points)
    duration = points[-1][0] - points[0][0] if len(points) >= 2 else 0.0
    raw = idle_subtract(gross, duration, idle_power_w)
    average = mean_power(gross, duration) if duration > 0 else 0.0
    return raw, average, duration


def _completed_rows(raw_path: Path) -> set[tuple[str, int]]:
    if not raw_path.is_file():
        return set()
    with raw_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {(row["question_id"], int(row["k"])) for row in reader}


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    temp.replace(path)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _registry_row(
    spec: RunSpec,
    split: SquadSplit,
    raw_path: Path,
    root: Path,
    git_commit: str,
    prereg_sha256: str,
    model_digest: str,
) -> dict[str, Any]:
    config = spec.config
    return {
        "run_id": spec.run_id,
        "timestamp_utc": _utc_now(),
        "phase": config.get("phase", ""),
        "dataset": config.get("dataset", ""),
        "reader": config.get("reader", {}).get("model", ""),
        "retriever": config.get("retrieval", {}).get("backend", ""),
        "k_grid": list(config.get("k_grid", [])),
        "n_questions": len(split.questions),
        "seed": int(config.get("seed", 0)),
        "energy_sampler": config.get("energy", {}).get("sampler", ""),
        "status": "planned",
        "git_commit": git_commit,
        "config_path": _relative(spec.config_path, root),
        "config_sha256": spec.config_sha256,
        "prereg_sha256": prereg_sha256,
        "model_digest": model_digest,
        "raw_csv": _relative(raw_path, root),
        "notes": f"{config.get('phase', '')} sweep; split={config.get('id_split', '')}",
    }


def run_depth_sweep(
    config_path: Path,
    *,
    root: Path | None = None,
    processed_dir: Path | None = None,
    out_root: Path | None = None,
    registry_path: Path | None = None,
    reader: Reader | None = None,
    sampler_factory: Callable[[int], Any] | None = None,
    idle_power_w: float | None = None,
    limit_questions: int | None = None,
    model_digest: str | None = None,
    resume: bool = False,
) -> Path:
    """Execute one depth sweep and return the raw CSV path."""
    root = (root or REPO_ROOT).resolve()
    spec = load_run_spec(config_path, root=root)
    config = spec.config
    processed_dir = Path(processed_dir or root / "data" / "processed")
    out_root = Path(out_root or root / "runs")
    registry_path = Path(registry_path or root / "runs" / "registry.csv")
    sampler_factory = sampler_factory or NvmlSampler
    split_name = str(config.get("id_split", ""))
    if not split_name:
        raise ValueError(f"{config_path}: id_split is required")

    split = load_squad_split(processed_dir, split_name, limit=limit_questions)
    k_grid = [int(k) for k in config["k_grid"]]
    run_dir = out_root / spec.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_path = run_dir / str(config.get("output", {}).get("raw_csv", "raw.csv"))
    if raw_path.exists() and not resume:
        raise FileExistsError(f"{raw_path} already exists; use resume=True or a new run_id")

    completed = _completed_rows(raw_path) if resume else set()
    rows_written = 0
    started = _utc_now()

    pairs = list(zip(split.corpus["passage_id"], split.corpus["text"], strict=True))
    index_started = time.perf_counter()
    index: BM25Index = build_index(pairs)
    index_build_s = time.perf_counter() - index_started

    reader = reader or _default_reader(config)
    digest = model_digest if model_digest is not None else _model_digest(reader, config)
    prereg_hash = _prereg_sha256(root)
    git_commit = _git_commit(root)
    registry_row = _registry_row(spec, split, raw_path, root, git_commit, prereg_hash, digest)
    append_registry_row(registry_path, registry_row)
    update_registry_status(registry_path, spec.run_id, "running")

    interval_ms = int(config.get("energy", {}).get("sample_interval_ms", 100))
    warmup_queries = int(config.get("energy", {}).get("warmup_queries", 20))
    nonce_hex_chars = int(config.get("energy", {}).get("nonce_hex_chars", 10))
    proxy_watts = float(config.get("energy", {}).get("cpu_retrieval_proxy_watts", 20.0))
    seed = int(config.get("seed", 0))
    idle_stats: IdleStats | None = None

    try:
        if split.questions.empty:
            raise ValueError(f"split {split_name!r} is empty")
        first = split.questions.iloc[0]
        for index_number in range(max(0, warmup_queries)):
            depth = k_grid[index_number % len(k_grid)]
            retrieved = index.search(str(first["question"]), depth)
            reader.generate(
                str(first["question"]),
                [passage.text for passage in retrieved],
                make_nonce(nonce_hex_chars),
            )

        if idle_power_w is None:
            idle_seconds = float(config.get("energy", {}).get("idle_baseline_s", 60))
            idle_stats = _measure_idle(sampler_factory, interval_ms, idle_seconds)
            idle_power_w = idle_stats.mean_w
        if idle_power_w < 0:
            raise ValueError("idle_power_w must be non-negative")

        with raw_path.open("a" if resume else "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS, lineterminator="\n")
            if not resume:
                writer.writeheader()
            for question_order, question_row in enumerate(split.questions.itertuples(index=False)):
                qid = str(question_row.qid)
                question = str(question_row.question)
                gold = str(question_row.gold)
                depths = list(k_grid)
                random.Random(seed + question_order).shuffle(depths)
                for order_in_question, depth in enumerate(depths):
                    if (qid, depth) in completed:
                        continue
                    nonce = make_nonce(nonce_hex_chars)
                    retrieval_started = time.perf_counter()
                    retrieved = index.search(question, depth)
                    retrieval_s = time.perf_counter() - retrieval_started
                    retrieval_j = cpu_retrieval_joules(retrieval_s, proxy_watts)

                    sampler = sampler_factory(interval_ms)
                    sampler.start()
                    result = None
                    reader_error: str | None = None
                    try:
                        result = reader.generate(
                            question,
                            [passage.text for passage in retrieved],
                            nonce,
                        )
                    except ReaderError as exc:
                        reader_error = str(exc)
                    finally:
                        samples = sampler.stop()

                    raw_j, average_w, _duration = _integrate(samples, idle_power_w)
                    valid = 1
                    invalid_reason = ""
                    if reader_error is not None:
                        valid = 0
                        invalid_reason = "reader_error"
                    elif len(samples) < 2:
                        valid = 0
                        invalid_reason = "sampler_error"
                    elif result is not None and result.load_s is not None and result.load_s > 1.0:
                        valid = 0
                        invalid_reason = "model_reload"

                    prediction = result.text if result is not None else ""
                    row = {
                        "run_id": spec.run_id,
                        "question_id": qid,
                        "question_order": question_order,
                        "k": depth,
                        "order_in_question": order_in_question,
                        "nonce": nonce,
                        "correct_em": correctness(prediction, gold, "normalized_em"),
                        "correct_lenient": correctness(prediction, gold, "lenient_span"),
                        "f1": round(token_f1(prediction, gold), 6),
                        "prediction": prediction,
                        "gold": gold,
                        "j_gpu_raw": round(raw_j, 6),
                        "j_gpu_calibrated": round(raw_j, 6),
                        "j_retrieval_proxy": round(retrieval_j, 6),
                        "j_total": round(raw_j + retrieval_j, 6),
                        "latency_s": round(result.latency_s, 6) if result else 0.0,
                        "prompt_tokens": result.prompt_tokens if result else "",
                        "output_tokens": result.output_tokens if result else "",
                        "load_s": round(result.load_s, 6)
                        if result and result.load_s is not None
                        else "",
                        "prefill_s": round(result.prompt_eval_s, 6)
                        if result and result.prompt_eval_s is not None
                        else "",
                        "eval_s": round(result.eval_s, 6)
                        if result and result.eval_s is not None
                        else "",
                        "gpu_temp_c": samples[-1].temperature_c if samples else "",
                        "sm_clock_mhz": samples[-1].sm_clock_mhz if samples else "",
                        "power_mean_w": round(average_w, 3),
                        "valid": valid,
                        "invalid_reason": invalid_reason,
                    }
                    writer.writerow(row)
                    handle.flush()
                    rows_written += 1

        finished = _utc_now()
        manifest = {
            "run_id": spec.run_id,
            "phase": config.get("phase", ""),
            "dataset": config.get("dataset", ""),
            "id_split": split_name,
            "k_grid": k_grid,
            "n_questions": len(split.questions),
            "seed": seed,
            "started_utc": started,
            "finished_utc": finished,
            "config_path": _relative(spec.config_path, root),
            "config_sha256": spec.config_sha256,
            "prereg_sha256": prereg_hash,
            "model_digest": digest,
            "git_commit": git_commit,
            "sources": [_relative(path, root) for path in spec.sources],
            "counts": {
                "rows": rows_written + len(completed),
                "questions": len(split.questions),
                "depths": len(k_grid),
                "corpus_passages": len(split.corpus),
            },
            "index_build_s": round(index_build_s, 6),
            "idle": None
            if idle_stats is None
            else {
                "mean_w": round(idle_stats.mean_w, 6),
                "sd_w": round(idle_stats.sd_w, 6),
                "cv": round(idle_stats.cv, 6),
                "n": idle_stats.n,
            },
            "environment": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
            },
        }
        _write_json_atomic(run_dir / "manifest.json", manifest)
        update_registry_status(registry_path, spec.run_id, "completed")
    except BaseException as exc:
        with contextlib.suppress(Exception):
            update_registry_status(registry_path, spec.run_id, "aborted", notes=str(exc))
        raise

    return raw_path


def run_block_calibration(config_path: Path) -> Path:
    """Run 20-query block calibration and return ``blocks.json``. Implemented in P0."""
    raise NotImplementedError("run_block_calibration is implemented in P0.")
