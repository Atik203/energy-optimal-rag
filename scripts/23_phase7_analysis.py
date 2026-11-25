#!/usr/bin/env python
"""23 - Phase 7 analysis: block estimator, convergence, affine fit.

Reads ``runs/squad_qwen4b_p7_blocks/blocks_design.json`` and writes
``analysis/measurement_hardening/``:

* ``estimates.json`` - per-depth ratio-of-sums energy, accuracy, CV, savings with
  a cluster-bootstrap interval;
* ``affine.json`` - weighted fit on ``k >= 1`` with intervals; ``k=0`` as a floor;
* ``convergence.json`` - block estimate against the sweep and calibration-invariant
  reference values at the frozen 3 pp tolerance (G7);
* ``report.md`` - human-readable summary.

CPU only; no GPU, no network.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.blocks import (  # noqa: E402
    BlockObservation,
    bootstrap_savings,
    convergence,
    cv_by_depth,
    depth_totals,
)

RUN_ID = "squad_qwen4b_p7_blocks"
CANDIDATE = 4
REFERENCE = 32
TOLERANCE_PP = 3.0
# Registered comparison values, both from P1 (docs/P1_RESULTS.md).
SWEEP_SAVINGS_PCT = 58.17
BLOCK_SAVINGS_PCT = 64.30
RAW_SAVINGS_PCT = 68.47


def _observations(payload: dict[str, Any]) -> list[BlockObservation]:
    return [
        BlockObservation(
            k=int(block["k"]),
            replicate=int(block["replicate"]),
            energy_j=float(block["energy_j"]),
            correct=int(block["correct"]),
            n=int(block["n"]),
            duration_s=float(block.get("duration_s", 0.0)),
        )
        for block in payload["blocks"]
    ]


def _affine(totals: dict[int, dict[str, float]], blocks: list[BlockObservation]) -> dict[str, Any]:
    depths = sorted(d for d in totals if d >= 1)
    xs = [float(d) for d in depths]
    means = [totals[d]["energy_j"] / totals[d]["n"] for d in depths]
    # Weight by the number of blocks: the block mean is the observation.
    ses: list[float] = []
    for d in depths:
        values = [b.energy_j / b.n for b in blocks if b.k == d]
        mean = sum(values) / len(values)
        var = sum((v - mean) ** 2 for v in values) / (len(values) - 1) if len(values) > 1 else 0.0
        ses.append(math.sqrt(var / len(values)) if var > 0 else 1e-9)
    weights = [1.0 / (s * s) for s in ses]
    sw = sum(weights)
    swx = sum(w * x for w, x in zip(weights, xs, strict=True))
    swy = sum(w * y for w, y in zip(weights, means, strict=True))
    swxx = sum(w * x * x for w, x in zip(weights, xs, strict=True))
    swxy = sum(w * x * y for w, x, y in zip(weights, xs, means, strict=True))
    det = sw * swxx - swx * swx
    if abs(det) < 1e-12:
        return {"error": "singular design"}
    a = (swy * swxx - swx * swxy) / det
    b = (sw * swxy - swx * swy) / det
    resid = [y - (a + b * x) for x, y in zip(xs, means, strict=True)]
    dof = len(xs) - 2
    s2 = sum(w * r * r for w, r in zip(weights, resid, strict=True)) / dof
    se_a = math.sqrt(s2 * swxx / det)
    se_b = math.sqrt(s2 * sw / det)
    tcrit = 2.776 if dof == 4 else 2.0
    return {
        "depths_used": depths,
        "intercept_a_j": a,
        "slope_b_j_per_passage": b,
        "se_a": se_a,
        "se_b": se_b,
        "ci95_a": [a - tcrit * se_a, a + tcrit * se_a],
        "ci95_b": [b - tcrit * se_b, b + tcrit * se_b],
        "positive_slope": b - tcrit * se_b > 0,
        "k0_floor_j_per_query": totals.get(0, {}).get("energy_j", float("nan"))
        / totals.get(0, {}).get("n", 1)
        if 0 in totals
        else None,
        "note": "k=0 is a floor and is excluded from the fit.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 analysis.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)
    run_dir = root / "runs" / args.run_id
    src = run_dir / "blocks_design.json"
    if not src.is_file():
        raise SystemExit(f"missing block output: {src}")
    payload = json.loads(src.read_text(encoding="utf-8"))
    blocks = _observations(payload)
    totals = depth_totals(blocks)
    out_dir = root / "analysis" / "measurement_hardening"
    out_dir.mkdir(parents=True, exist_ok=True)

    estimates = {
        "run_id": args.run_id,
        "estimand": "E(k) = sum_b J_block(k,b) / sum_b C(k,b)",
        "n_blocks": len(blocks),
        "idle": payload.get("idle"),
        "depths": {str(k): v for k, v in sorted(totals.items())},
        "cv_by_depth": {str(k): v for k, v in sorted(cv_by_depth(blocks).items())},
    }
    if CANDIDATE in totals and REFERENCE in totals:
        boot = bootstrap_savings(blocks, CANDIDATE, REFERENCE, seed=20261115)
        estimates["savings"] = {
            "candidate_depth": CANDIDATE,
            "reference_depth": REFERENCE,
            "point": boot["point"],
            "ci95": boot["ci"],
            "n_valid": boot["n_valid"],
        }
    (out_dir / "estimates.json").write_text(json.dumps(estimates, indent=2), encoding="utf-8")

    affine = _affine(totals, blocks)
    (out_dir / "affine.json").write_text(json.dumps(affine, indent=2), encoding="utf-8")

    if "savings" in estimates:
        conv = {
            "block_vs_sweep": convergence(
                blocks,
                CANDIDATE,
                REFERENCE,
                alternative_savings_pct=SWEEP_SAVINGS_PCT,
                tolerance_pp=TOLERANCE_PP,
            ),
            "block_vs_block_calibration": convergence(
                blocks,
                CANDIDATE,
                REFERENCE,
                alternative_savings_pct=BLOCK_SAVINGS_PCT,
                tolerance_pp=TOLERANCE_PP,
            ),
            "block_vs_raw": convergence(
                blocks,
                CANDIDATE,
                REFERENCE,
                alternative_savings_pct=RAW_SAVINGS_PCT,
                tolerance_pp=TOLERANCE_PP,
            ),
        }
        (out_dir / "convergence.json").write_text(json.dumps(conv, indent=2), encoding="utf-8")

    lines = [
        "# Phase 7 - block estimator",
        "",
        f"Run `{args.run_id}`; {len(blocks)} blocks.",
        "",
        "| k | A(k) | J/query | E (J/correct) | blocks | CV |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    cvs = cv_by_depth(blocks)
    for k in sorted(totals):
        entry = totals[k]
        cv = cvs.get(k, {}).get("cv", float("nan"))
        lines.append(
            f"| {k} | {entry['accuracy']:.4f} | {entry['energy_j'] / entry['n']:.2f} | "
            f"{entry['energy_per_correct']:.2f} | {int(entry['blocks'])} | {cv:.3f} |"
        )
    if "savings" in estimates:
        s = estimates["savings"]
        lines += [
            "",
            f"Savings at k={CANDIDATE} vs k={REFERENCE}: "
            f"{100 * s['point']:.2f}% [{100 * s['ci95'][0]:.2f}, {100 * s['ci95'][1]:.2f}]",
        ]
    if "slope_b_j_per_passage" in affine:
        lines += [
            "",
            f"Affine (k>=1): a = {affine['intercept_a_j']:.2f} J, "
            f"b = {affine['slope_b_j_per_passage']:.3f} J/passage, "
            f"95% b interval [{affine['ci95_b'][0]:.3f}, {affine['ci95_b'][1]:.3f}].",
        ]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
