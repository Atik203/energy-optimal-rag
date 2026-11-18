#!/usr/bin/env python
"""14 - NVML power probe for per-query window bias.

For each depth, runs 20 queries with a continuous sampler and a 3 s quiet
window after each query. Reports how long the power signal takes to return to
the local floor and whether the pre-query floor matches the global idle.

Diagnostic only; does not change any registered calibration or gate.
"""

from __future__ import annotations

import argparse
import csv
import json
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
    _measure_idle,
    load_run_spec,
    make_nonce,
)

BINS = (0.0, 0.2, 0.4, 0.6, 1.0, 2.0, 3.0)


def _bin_means(samples, start, end, idle):
    out = []
    for left, right in zip(BINS[:-1], BINS[1:], strict=True):
        points = [
            sample.power_w for sample in samples if start + left <= sample.t_s < start + right
        ]
        out.append(
            {
                "window_s": [left, right],
                "mean_net_w": (sum(points) / len(points) - idle) if points else None,
                "n": len(points),
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="NVML power-window probe.")
    parser.add_argument("--config", default="configs/runs/squad_qwen15b.toml")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    parser.add_argument("--questions", type=int, default=20)
    parser.add_argument("--quiet-s", type=float, default=3.0)
    parser.add_argument("--interval-ms", type=int, default=100)
    args = parser.parse_args()
    root = Path(args.root)
    config_path = Path(args.config)
    spec = load_run_spec(config_path, root=root)
    config = spec.config
    run_id = args.run_id or spec.run_id
    k_grid = [int(k) for k in config["k_grid"]]
    split = load_prepared_split(
        root / "data" / "processed",
        str(config.get("dataset", "squad")),
        str(config["id_split"]),
    )
    questions = {
        str(row.qid): str(row.question)
        for row in split.questions.head(args.questions).itertuples(index=False)
    }
    qids = list(questions)
    index = RetrievalIndex.from_corpus(split.corpus)
    reader = _default_reader(config)
    idle = _measure_idle(NvmlSampler, args.interval_ms, 10.0)
    idle_w = float(idle.mean_w)
    print(f"idle {idle_w:.3f} W (cv {idle.cv:.4f})")

    records = []
    samples_out = []
    for depth in k_grid:
        # Warm up two queries.
        for qid in qids[:2]:
            retrieved = index.search(qid, questions[qid], depth)
            reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(10))
        sampler = NvmlSampler(args.interval_ms)
        sampler.start()
        windows = []
        for qid in qids:
            retrieved = index.search(qid, questions[qid], depth)
            start = time.monotonic()
            reader.generate(questions[qid], [p.text for p in retrieved], make_nonce(10))
            end = time.monotonic()
            windows.append((qid, start, end))
            time.sleep(args.quiet_s)
        samples = sampler.stop()
        for sample in samples:
            samples_out.append(
                {
                    "k": depth,
                    "t_s": round(sample.t_s - samples[0].t_s, 6),
                    "power_w": sample.power_w,
                    "temperature_c": sample.temperature_c,
                    "sm_clock_mhz": sample.sm_clock_mhz,
                }
            )
        for qid, start, end in windows:
            post = _bin_means(samples, end, end + args.quiet_s, idle_w)
            pre_points = [s.power_w for s in samples if end - 0.2 <= s.t_s < end]
            records.append(
                {
                    "k": depth,
                    "question_id": qid,
                    "latency_s": round(end - start, 6),
                    "pre_net_w": (sum(pre_points) / len(pre_points) - idle_w)
                    if pre_points
                    else None,
                    "post_bins": post,
                }
            )
        print(f"k={depth}: {len(windows)} queries")

    out_dir = Path(args.out) if args.out else root / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "probe.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "idle_w": idle_w,
                "idle_cv": idle.cv,
                "bins_s": BINS,
                "records": records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with (out_dir / "probe_samples.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["k", "t_s", "power_w", "temperature_c", "sm_clock_mhz"]
        )
        writer.writeheader()
        writer.writerows(samples_out)
    print(f"wrote {out_dir / 'probe.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
