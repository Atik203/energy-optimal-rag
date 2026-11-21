#!/usr/bin/env python
"""Build the P1 margin-frontier figure from analysis/squad_qwen4b_p1/margin_frontier.json."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "analysis" / "squad_qwen4b_p1" / "margin_frontier.json"
OUT = ROOT / "paper" / "figures" / "p1_frontier.png"
DPI = 650


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    rows = [row for row in payload["frontier"] if row["selected_depth"] is not None]
    margins = [row["margin_pp"] for row in rows]
    savings = [row["savings_pct"] for row in rows]
    required = [row["required_n"] or np.nan for row in rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 3.7))
    ax1.plot(margins, savings, marker="o", color="#0072B2")
    ax1.set_xlabel("Non-inferiority margin (pp)")
    ax1.set_ylabel("Energy saving vs k=32 (%)")
    ax1.set_title("Selected depth and saving")
    ax1.grid(alpha=0.25)
    for margin, saving, row in zip(margins, savings, rows, strict=True):
        ax1.annotate(
            f"k={row['selected_depth']}",
            (margin, saving),
            fontsize=7,
            xytext=(3, 3),
            textcoords="offset points",
        )

    ax2.plot(margins, required, marker="o", color="#D55E00")
    ax2.set_yscale("log")
    ax2.set_xlabel("Non-inferiority margin (pp)")
    ax2.set_ylabel("Derived required n (log scale)")
    ax2.set_title("Sample size needed at observed effect")
    ax2.grid(alpha=0.25, which="both")
    ax2.axhline(1000, color="black", linestyle="--", linewidth=0.8)
    ax2.annotate("n=1,000", (margins[-1], 1000), fontsize=7, ha="right", va="bottom")

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=DPI)
    print(f"wrote {OUT} at {DPI} dpi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
