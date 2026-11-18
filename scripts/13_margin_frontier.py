#!/usr/bin/env python
"""13 - Margin-indexed certification frontier.

For each margin, select the cheapest feasible depth, run the paired
non-inferiority test at that margin, and report the derived sample size needed
for the observed effect. The 5 pp row is the preregistered confirmatory margin;
all other rows are exploratory.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

from rag_energy.stats.p1 import (  # noqa: E402
    load_rows,
    margin_sensitivity,
    noninferiority,
    paired_questions,
    summarize,
)

MARGINS = (0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)
REFERENCE = 32
Z_ONE_SIDED = 1.6448536269514722


def build_frontier(run_id: str, raw_path: Path) -> dict:
    rows = load_rows(raw_path)
    summaries = summarize(rows, correct_key="em")
    by_k = {summary.k: summary for summary in summaries}
    selected_rows = margin_sensitivity(summaries, margins=MARGINS, reference_depth=REFERENCE)
    frontier = []
    for row in selected_rows:
        selected = row["selected_depth"]
        margin = float(row["margin_pp"]) / 100.0
        if selected is None:
            frontier.append({**row, "ni_lower": None, "ni_p": None, "required_n": None})
            continue
        cand, ref, _excluded = paired_questions(rows, int(selected), REFERENCE)
        result = noninferiority(
            [int(r["correct_em"]) for r in cand],
            [int(r["correct_em"]) for r in ref],
            margin=margin,
        )
        gap = margin - abs(result.mean_diff)
        if gap > 0 and result.se > 0:
            required_n = round(result.n_pairs * (Z_ONE_SIDED * result.se / gap) ** 2)
        else:
            required_n = None
        frontier.append(
            {
                **row,
                "ni_lower": result.lower_bound,
                "ni_p": result.p_value,
                "ni_non_inferior": result.non_inferior,
                "required_n": required_n,
            }
        )
    return {
        "run_id": run_id,
        "reference_depth": REFERENCE,
        "note": "Only 5 pp is confirmatory; other margins are exploratory.",
        "frontier": frontier,
        "depths": {summary.k: summary.accuracy for summary in summaries},
        "savings": {summary.k: by_k[summary.k].e_per_correct for summary in summaries},
    }


def write_outputs(payload: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "margin_frontier.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    lines = [
        f"# Margin frontier — {payload['run_id']}",
        "",
        "Only the 5 pp row is confirmatory; all other margins are exploratory.",
        "",
        "| Margin | k | A(k) | Savings | NI lower | NI p | Required n |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["frontier"]:
        k = row["selected_depth"]
        if k is None:
            lines.append(f"| {row['margin_pp']:.0f} pp | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {row['margin_pp']:.0f} pp | {k} | {row['accuracy']:.4f} | "
            f"{row['savings_pct']:.2f}% | {100 * row['ni_lower']:.2f} pp | "
            f"{row['ni_p']:.4f} | {row['required_n']} |"
        )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Margin-indexed certification frontier.")
    parser.add_argument("--run-id", default="squad_qwen4b_p1")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.root)
    raw = root / "runs" / args.run_id / "raw.csv"
    out = Path(args.out) if args.out else root / "analysis" / args.run_id
    payload = build_frontier(args.run_id, raw)
    write_outputs(payload, out)
    print(f"Frontier: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
