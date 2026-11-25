#!/usr/bin/env python
"""25 - Phase 7 replay analysis (H-M1 adjudication).

Compares the permutation replays against the block design:

* ``replay/block`` per depth and in total, as a distribution over replays rather than
  one number;
* the saving each replay implies when paired with the block run's accuracy;
* a position-trend test, because a monotone decline across replays would mean the
  replays are not exchangeable and the distribution is a drift artifact.

CPU only; reads ``replays.json`` and ``blocks_design.json``.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_RUN_ID = "squad_qwen4b_p7_blocks_full"
CANDIDATE = 4
REFERENCE = 32
N_BOOT = 2000
SEED = 20261115


def _blocks_per_query(payload: dict[str, Any]) -> dict[int, float]:
    """Block energy per query at each depth, pooled over blocks (ratio of sums)."""
    totals: dict[int, float] = {}
    counts: dict[int, int] = {}
    for block in payload["blocks"]:
        k = int(block["k"])
        totals[k] = totals.get(k, 0.0) + float(block["energy_j"])
        counts[k] = counts.get(k, 0) + int(block["n"])
    return {k: totals[k] / counts[k] for k in totals}


def _blocks_accuracy(payload: dict[str, Any]) -> dict[int, float]:
    correct: dict[int, int] = {}
    counts: dict[int, int] = {}
    for block in payload["blocks"]:
        k = int(block["k"])
        correct[k] = correct.get(k, 0) + int(block["correct"])
        counts[k] = counts.get(k, 0) + int(block["n"])
    return {k: correct[k] / counts[k] for k in correct}


def _replays_per_query(replay: dict[str, Any]) -> dict[int, float]:
    energy = {int(k): float(v) for k, v in replay["replay_by_depth_j"].items()}
    counts = {int(k): int(v) for k, v in replay["counts_by_depth"].items()}
    return {k: energy[k] / counts[k] for k in energy if counts.get(k)}


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    pos = q * (len(ordered) - 1)
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def _ols_slope(xs: list[float], ys: list[float]) -> dict[str, float]:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys, strict=True))
    return {
        "slope_j_per_replay": slope,
        "intercept_j": intercept,
        "r_squared": 1 - ss_res / ss_tot if ss_tot else 0.0,
    }


def _spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        for rank, idx in enumerate(order):
            out[idx] = float(rank)
        return out

    rx, ry = ranks(xs), ranks(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 replay analysis.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)
    run_dir = root / "runs" / args.run_id
    replay_path = run_dir / "replays.json"
    block_path = run_dir / "blocks_design.json"
    for path in (replay_path, block_path):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")

    replay_payload = json.loads(replay_path.read_text(encoding="utf-8"))
    block_payload = json.loads(block_path.read_text(encoding="utf-8"))
    replays = replay_payload["replays"]
    k_grid = [int(k) for k in replay_payload["k_grid"]]
    block_jq = _blocks_per_query(block_payload)
    accuracy = _blocks_accuracy(block_payload)
    q_per_depth = int(replay_payload["questions_per_replay"])

    # Per-replay per-depth energy per query, and the implied total at the block's
    # 20-question scale.
    per_replay: list[dict[str, Any]] = []
    for item in replays:
        jq = _replays_per_query(item)
        block_scale = sum(block_jq[k] * q_per_depth for k in k_grid)
        saving = None
        if (
            CANDIDATE in jq
            and REFERENCE in jq
            and accuracy.get(CANDIDATE)
            and accuracy.get(REFERENCE)
        ):
            e_cand = jq[CANDIDATE] / accuracy[CANDIDATE]
            e_ref = jq[REFERENCE] / accuracy[REFERENCE]
            saving = 1 - e_cand / e_ref
        per_replay.append(
            {
                "replay": int(item["replay"]),
                "j_per_query": {str(k): jq[k] for k in k_grid if k in jq},
                "ratio_to_block": {
                    str(k): jq[k] / block_jq[k] for k in k_grid if k in jq and block_jq.get(k)
                },
                "total_ratio": float(item["replay_total_j"]) / block_scale,
                "saving_pct": None if saving is None else 100 * saving,
            }
        )

    totals = [r["total_ratio"] for r in per_replay]
    savings = [r["saving_pct"] for r in per_replay if r["saving_pct"] is not None]
    by_depth: dict[str, dict[str, float]] = {}
    for k in k_grid:
        ratios = [r["ratio_to_block"][str(k)] for r in per_replay if str(k) in r["ratio_to_block"]]
        if ratios:
            by_depth[str(k)] = {
                "median": statistics.median(ratios),
                "min": min(ratios),
                "max": max(ratios),
                "sd": statistics.stdev(ratios) if len(ratios) > 1 else 0.0,
            }

    # Bootstrap over replays. Ten units is few: the interval is reported as a spread,
    # not as a precise confidence statement.
    import random

    rng = random.Random(SEED)
    boot_median = [
        statistics.median([totals[rng.randrange(len(totals))] for _ in totals])
        for _ in range(N_BOOT)
    ]
    boot_saving = (
        [
            statistics.median([savings[rng.randrange(len(savings))] for _ in savings])
            for _ in range(N_BOOT)
        ]
        if savings
        else []
    )

    order = [float(r["replay"]) for r in per_replay]
    trend = _ols_slope(order, totals)
    trend["spearman_rho"] = _spearman(order, totals)

    block_saving_pct = None
    if accuracy.get(CANDIDATE) and accuracy.get(REFERENCE) and block_jq.get(CANDIDATE):
        e_cand = block_jq[CANDIDATE] / accuracy[CANDIDATE]
        e_ref = block_jq[REFERENCE] / accuracy[REFERENCE]
        block_saving_pct = 100 * (1 - e_cand / e_ref)

    payload = {
        "run_id": args.run_id,
        "n_replays": len(per_replay),
        "questions_per_depth": q_per_depth,
        "block_j_per_query": {str(k): block_jq[k] for k in sorted(block_jq)},
        "block_saving_pct": block_saving_pct,
        "total_ratio": {
            "median": statistics.median(totals),
            "mean": statistics.mean(totals),
            "min": min(totals),
            "max": max(totals),
            "sd": statistics.stdev(totals) if len(totals) > 1 else 0.0,
            "cv": (statistics.stdev(totals) / statistics.mean(totals)) if len(totals) > 1 else 0.0,
            "boot_median_ci95": [_quantile(boot_median, 0.025), _quantile(boot_median, 0.975)],
        },
        "saving_pct": {
            "median": statistics.median(savings) if savings else None,
            "min": min(savings) if savings else None,
            "max": max(savings) if savings else None,
            "sd": statistics.stdev(savings) if len(savings) > 1 else None,
            "boot_median_ci95": (
                [_quantile(boot_saving, 0.025), _quantile(boot_saving, 0.975)]
                if boot_saving
                else None
            ),
        },
        "ratio_by_depth": by_depth,
        "position_trend": trend,
        "per_replay": per_replay,
    }

    out_dir = root / "analysis" / "measurement_hardening" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "replays.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 7 - permutation replays",
        "",
        f"Run `{args.run_id}`; {len(per_replay)} replays of {q_per_depth} questions per depth.",
        "",
        "| replay | total ratio | saving % |",
        "|---:|---:|---:|",
    ]
    for r in per_replay:
        sv = "-" if r["saving_pct"] is None else f"{r['saving_pct']:.2f}"
        lines.append(f"| {r['replay']} | {r['total_ratio']:.3f} | {sv} |")
    tr = payload["total_ratio"]
    lines += [
        "",
        f"Total replay/block: median {tr['median']:.3f} "
        f"(range {tr['min']:.3f}-{tr['max']:.3f}, CV {100 * tr['cv']:.1f}%).",
    ]
    if payload["saving_pct"]["median"] is not None:
        sp = payload["saving_pct"]
        lines.append(
            f"Saving implied by the replays: median {sp['median']:.2f}% "
            f"(range {sp['min']:.2f}-{sp['max']:.2f}); block estimator "
            f"{block_saving_pct:.2f}%."
        )
    lines += [
        "",
        "| depth | replay/block median | range |",
        "|---:|---:|---|",
    ]
    for k in sorted(by_depth, key=int):
        item = by_depth[k]
        lines.append(f"| {k} | {item['median']:.3f} | {item['min']:.3f}-{item['max']:.3f} |")
    lines += [
        "",
        f"Position trend: {trend['slope_j_per_replay']:.4f} per replay "
        f"(R2 {trend['r_squared']:.3f}, Spearman rho {trend['spearman_rho']:.3f}).",
        "",
    ]
    (out_dir / "replays.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
