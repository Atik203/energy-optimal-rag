#!/usr/bin/env python
"""18 - Continuous-optimum identity diagnostic.

Interpolates A(k) with a monotone cubic, uses the affine J(k), and finds the
continuous minimizer of E=J/A. Reports the identity gap there. Exploratory;
does not re-adjudicate H3.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.stats.p1 import affine_lack_of_fit, summarize  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuous-optimum identity diagnostic.")
    parser.add_argument("--run-id", default="squad_qwen4b_p1")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.root)
    rows = list(csv.DictReader((root / "runs" / args.run_id / "raw.csv").open(encoding="utf-8")))
    summaries = summarize(rows, correct_key="em")
    depths = [s.k for s in summaries]
    accuracy = [s.accuracy for s in summaries]
    fit = affine_lack_of_fit([(s.k, s.mean_j) for s in summaries])
    a, b = float(fit["a"]), float(fit["b"])

    from scipy.interpolate import PchipInterpolator
    from scipy.optimize import minimize_scalar

    interp = PchipInterpolator(depths, accuracy)

    def objective(k: float) -> float:
        acc = float(interp(k))
        return (a + b * k) / acc if acc > 0 else float("inf")

    result = minimize_scalar(objective, bounds=(0.0, max(depths)), method="bounded")
    k_star = float(result.x)
    acc = float(interp(k_star))
    j = a + b * k_star
    # Numerical elasticities at the continuous optimum.
    eps_j = k_star * b / j
    h = 1e-4
    dacc = (float(interp(k_star + h)) - float(interp(k_star - h))) / (2 * h)
    eps_a = k_star * dacc / acc
    payload = {
        "run_id": args.run_id,
        "a": a,
        "b": b,
        "k_star_continuous": k_star,
        "accuracy": acc,
        "e_per_correct": j / acc,
        "epsilon_j": eps_j,
        "epsilon_a": eps_a,
        "identity_gap": eps_j - eps_a,
        "grid_depths": depths,
        "note": "Exploratory; H3 remains adjudicated at k=4.",
    }
    out = Path(args.out) if args.out else root / "analysis" / "identity_continuous.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
