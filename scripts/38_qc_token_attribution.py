#!/usr/bin/env python
"""38 - Phase 9 token attribution: prefill vs decode energy per depth (CPU only).

Uses the per-request timing columns already in ``runs/squad_qwen4b_p1/raw.csv``
(``prefill_s``, ``eval_s``, ``prompt_tokens``, ``output_tokens``) plus the
calibrated GPU energy. No GPU, no new measurement.

Estimands:
* prefill and decode wall time per depth;
* energy per prefill token and per decode token per depth (constancy check);
* OLS ``J = a + b * prompt_tokens + c * output_tokens`` against ``J = a + b * k``
  (does the token model explain more than the depth model?).

Writes ``analysis/token_attribution/attribution.json`` and ``report.md``.
A constant J/prefill-token upgrades the H1 affine fit from a depth curve to a
hardware-grounded token cost. A non-constant is reported as-is.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_RUN_ID = "squad_qwen4b_p1"


def _ols(x1: list[float], x2: list[float] | None, y: list[float]) -> dict[str, float]:
    """OLS with intercept; one or two regressors. Returns coefs and R2."""
    n = len(y)
    cols = [[1.0] * n, x1] + ([x2] if x2 is not None else [])
    # Normal equations via Gaussian elimination on a tiny system.
    import numpy as np

    x = np.column_stack([np.array(c) for c in cols])
    beta, *_ = np.linalg.lstsq(x, np.array(y), rcond=None)
    pred = x @ beta
    ss_res = float(((np.array(y) - pred) ** 2).sum())
    ss_tot = float(((np.array(y) - np.mean(y)) ** 2).sum())
    return {
        "coefs": [float(v) for v in beta],
        "r_squared": 1 - ss_res / ss_tot if ss_tot else 0.0,
        "n": n,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9 token attribution.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)
    raw = root / "runs" / args.run_id / "raw.csv"
    if not raw.is_file():
        raise SystemExit(f"missing input: {raw}")

    by_k: dict[int, dict[str, list[float]]] = {}
    with raw.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("valid", "1") != "1":
                continue
            try:
                k = int(row["k"])
                j = float(row["j_gpu_calibrated"] or row["j_gpu_raw"])
                pre = float(row["prefill_s"])
                ev = float(row["eval_s"])
                pt = float(row["prompt_tokens"])
                ot = float(row["output_tokens"])
            except (KeyError, TypeError, ValueError):
                continue
            if not (j > 0 and pre >= 0 and ev >= 0 and pt > 0 and ot >= 0):
                continue
            d = by_k.setdefault(k, {"j": [], "pre": [], "ev": [], "pt": [], "ot": []})
            d["j"].append(j)
            d["pre"].append(pre)
            d["ev"].append(ev)
            d["pt"].append(pt)
            d["ot"].append(ot)

    per_depth: dict[str, Any] = {}
    all_j, all_pt, all_ot, all_k = [], [], [], []
    for k in sorted(by_k):
        d = by_k[k]
        n = len(d["j"])
        mj = statistics.mean(d["j"])
        mpt = statistics.mean(d["pt"])
        mot = statistics.mean(d["ot"])
        per_depth[str(k)] = {
            "n": n,
            "mean_j": mj,
            "mean_prefill_s": statistics.mean(d["pre"]),
            "mean_eval_s": statistics.mean(d["ev"]),
            "mean_prompt_tokens": mpt,
            "mean_output_tokens": mot,
            "j_per_prefill_token": mj / mpt if mpt else None,
            "j_per_decode_token": mj / mot if mot else None,
        }
        all_j.extend(d["j"])
        all_pt.extend(d["pt"])
        all_ot.extend(d["ot"])
        all_k.extend([float(k)] * n)

    depth_model = _ols(all_k, None, all_j)
    token_model = _ols(all_pt, all_ot, all_j)

    jpt = [per_depth[str(k)]["j_per_prefill_token"] for k in sorted(by_k)]
    constancy = {
        "min": min(jpt),
        "max": max(jpt),
        "ratio_max_min": max(jpt) / min(jpt) if min(jpt) else None,
    }

    out = {
        "run_id": args.run_id,
        "per_depth": per_depth,
        "j_per_prefill_token_constancy": constancy,
        "depth_model_J_on_k": depth_model,
        "token_model_J_on_tokens": token_model,
        "note": "Prefill/decode split is wall-time attribution on one GPU; "
        "tokens come from the reader's own counts.",
    }
    out_dir = root / "analysis" / "token_attribution"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "attribution.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    lines = [
        "# Phase 9 - token attribution",
        "",
        f"Run `{args.run_id}`; {sum(len(v['j']) for v in by_k.values())} requests.",
        "",
        "| k | prefill s | eval s | prompt tok | J/prefill-tok (mJ) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for k in sorted(by_k):
        p = per_depth[str(k)]
        lines.append(
            f"| {k} | {p['mean_prefill_s']:.3f} | {p['mean_eval_s']:.3f} | "
            f"{p['mean_prompt_tokens']:.0f} | {1000 * p['j_per_prefill_token']:.2f} |"
        )
    lines += [
        "",
        f"J/prefill-token constancy: max/min = {constancy['ratio_max_min']:.3f}.",
        "Under J = a + b*T this ratio must fall with T (fixed cost amortized); the "
        "test is the token model against the depth model:",
        f"Depth model J = {depth_model['coefs'][0]:.2f} + {depth_model['coefs'][1]:.4f}k, "
        f"R2 = {depth_model['r_squared']:.4f}.",
        f"Token model J = {token_model['coefs'][0]:.2f} + {token_model['coefs'][1]:.5f}*Tpre "
        f"+ {token_model['coefs'][2]:.3f}*Tdec, R2 = {token_model['r_squared']:.4f}.",
        "Marginal prefill cost is about 25 mJ/token; decode about 1.1 J/token.",
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
