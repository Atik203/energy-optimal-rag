#!/usr/bin/env python
"""27 - Phase 7 carryover regression on the P1 sweep rows.

Fits ``J_i = a + b k_i + g k_{i-1} + d temp_i + e clock_i`` with question-clustered
standard errors, where ``k_{i-1}`` is the depth of the immediately preceding request.
This is prereg item 5 and it is CPU only.

Caveat reported with the result: the predecessor determines the thermal state that the
current request runs in, so ``g`` remains partly confounded with thermal history even
with the temperature and clock controls. The regression bounds the effect; it does not
identify a pure carryover.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_RUN_ID = "squad_qwen4b_p1"
NAMES = ("intercept", "k_depth", "k_prev_depth", "temp_c", "clock_mhz")


def _load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row.get("valid", "1") == "1"]


def _with_predecessor(rows: list[dict[str, str]]) -> list[dict[str, float | str]]:
    """Order the sweep as it ran and attach each request's predecessor depth."""
    by_question: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_question[row["question_id"]].append(row)
    for items in by_question.values():
        items.sort(key=lambda r: float(r["order_in_question"]))

    ordered: list[dict[str, str]] = []
    for question_order in sorted(by_question, key=lambda q: float(by_question[q][0]["question_order"])):
        ordered.extend(by_question[question_order])

    out: list[dict[str, float | str]] = []
    for index, row in enumerate(ordered):
        if index == 0:
            continue
        prev = ordered[index - 1]
        try:
            energy = float(row["j_gpu_raw"])
            temp = float(row["gpu_temp_c"])
            clock = float(row["sm_clock_mhz"])
        except (TypeError, ValueError):
            continue
        if not energy > 0 or not temp > 0 or not clock > 0:
            continue
        out.append(
            {
                "question_id": row["question_id"],
                "j": energy,
                "k": float(row["k"]),
                "k_prev": float(prev["k"]),
                "temp": temp,
                "clock": clock,
            }
        )
    return out


def _fit(
    data: list[dict[str, float | str]], use_controls: bool
) -> dict[str, Any]:
    """OLS with question-clustered sandwich standard errors."""
    y = np.array([float(row["j"]) for row in data])
    columns = [
        np.ones(len(data)),
        np.array([float(row["k"]) for row in data]),
        np.array([float(row["k_prev"]) for row in data]),
    ]
    if use_controls:
        columns.append(np.array([float(row["temp"]) for row in data]))
        columns.append(np.array([float(row["clock"]) for row in data]))
    x = np.column_stack(columns)
    names = list(NAMES[: x.shape[1]])

    xtx_inv = np.linalg.pinv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    resid = y - x @ beta

    clusters: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(data):
        clusters[str(row["question_id"])].append(index)

    meat = np.zeros((x.shape[1], x.shape[1]))
    for indices in clusters.values():
        xg = x[indices]
        ug = resid[indices]
        score = xg.T @ ug
        meat += np.outer(score, score)
    n_obs, n_par = x.shape
    groups = len(clusters)
    correction = (groups / (groups - 1)) * ((n_obs - 1) / (n_obs - n_par))
    cov = xtx_inv @ meat @ xtx_inv * correction
    se = np.sqrt(np.diag(cov))
    t_stat = beta / se

    # Normal approximation: the cluster count is large (hundreds), so t is close.
    p_value = 2 * (1 - 0.5 * (1 + np.vectorize(_erf)(np.abs(t_stat) / np.sqrt(2))))

    ss_tot = float(((y - y.mean()) ** 2).sum())
    ss_res = float((resid**2).sum())
    return {
        "terms": [
            {
                "name": name,
                "coef": float(beta[i]),
                "se_cluster": float(se[i]),
                "t": float(t_stat[i]),
                "p_normal_approx": float(p_value[i]),
                "ci95": [float(beta[i] - 1.96 * se[i]), float(beta[i] + 1.96 * se[i])],
            }
            for i, name in enumerate(names)
        ],
        "n_obs": n_obs,
        "n_clusters": groups,
        "r_squared": 1 - ss_res / ss_tot if ss_tot else None,
        "controls": use_controls,
    }


def _erf(x: np.ndarray) -> np.ndarray:
    """Abramowitz-Stegun 7.1.26, plenty for a p-value on a t of order 1-100."""
    sign = np.sign(x)
    ax = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * ax)
    poly = t * (
        0.254829592
        + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))
    )
    return sign * (1 - poly * np.exp(-ax * ax))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 carryover regression.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)
    raw = root / "runs" / args.run_id / "raw.csv"
    if not raw.is_file():
        raise SystemExit(f"missing input: {raw}")

    data = _with_predecessor(_load(raw))
    if len(data) < 100:
        raise SystemExit(f"too few usable rows: {len(data)}")

    bare = _fit(data, use_controls=False)
    controlled = _fit(data, use_controls=True)

    gamma_bare = next(t for t in bare["terms"] if t["name"] == "k_prev_depth")
    gamma_ctrl = next(t for t in controlled["terms"] if t["name"] == "k_prev_depth")

    payload = {
        "run_id": args.run_id,
        "estimand": "J_i = a + b k_i + g k_{i-1} + d temp_i + e clock_i",
        "n_obs": bare["n_obs"],
        "n_clusters": bare["n_clusters"],
        "gamma_without_controls": gamma_bare,
        "gamma_with_temp_clock": gamma_ctrl,
        "models": {"bare": bare, "controlled": controlled},
        "confounding_note": (
            "The predecessor sets the thermal state the current request runs in, so g is "
            "partly confounded with thermal history even with the controls. This bounds the "
            "carryover; it does not identify a pure effect."
        ),
    }

    out_dir = root / "analysis" / "measurement_hardening" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "carryover.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 7 - carryover regression",
        "",
        f"Run `{args.run_id}`; {bare['n_obs']} requests, {bare['n_clusters']} question clusters.",
        "",
        "| model | gamma J per depth of predecessor | 95% CI | t |",
        "|---|---:|---|---:|",
        f"| bare | {gamma_bare['coef']:.4f} | "
        f"[{gamma_bare['ci95'][0]:.4f}, {gamma_bare['ci95'][1]:.4f}] | {gamma_bare['t']:.2f} |",
        f"| with temp + clock | {gamma_ctrl['coef']:.4f} | "
        f"[{gamma_ctrl['ci95'][0]:.4f}, {gamma_ctrl['ci95'][1]:.4f}] | {gamma_ctrl['t']:.2f} |",
        "",
        f"R2: bare {bare['r_squared']:.4f}, controlled {controlled['r_squared']:.4f}.",
        "",
        payload["confounding_note"],
        "",
    ]
    (out_dir / "carryover.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
