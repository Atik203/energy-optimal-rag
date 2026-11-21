#!/usr/bin/env python
"""Build the measurement-validity figure from probe and window-bias outputs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PROBE = ROOT / "analysis" / "measurement" / "probe_qwen15b.json"
BIAS = ROOT / "analysis" / "calibration_bias.json"
OUT = ROOT / "paper" / "figures" / "measurement_validity.png"
DPI = 650


def main() -> int:
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    bias = json.loads(BIAS.read_text(encoding="utf-8"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 3.7))

    for depth, color in ((0, "#0072B2"), (8, "#009E73"), (32, "#D55E00")):
        records = [r for r in probe["records"] if r["k"] == depth]
        bins = records[0]["post_bins"]
        xs = [0.5 * (b["window_s"][0] + b["window_s"][1]) for b in bins]
        ys = []
        for index in range(len(bins)):
            vals = [
                r["post_bins"][index]["mean_net_w"]
                for r in records
                if r["post_bins"][index]["mean_net_w"] is not None
            ]
            ys.append(float(np.mean(vals)))
        ax1.plot(xs, ys, marker="o", label=f"k={depth}", color=color)
    ax1.axhline(0, color="black", linewidth=0.7, linestyle="--")
    ax1.set_xlabel("Time after query end (s)")
    ax1.set_ylabel("Power above pre-run idle (W)")
    ax1.set_title("Post-query floor does not settle")
    ax1.legend(fontsize=7)
    ax1.grid(alpha=0.25)

    for arm, color in (
        ("squad_qwen4b_p1", "#0072B2"),
        ("squad_qwen15b_p2", "#D55E00"),
        ("hotpot_qwen4b_p2", "#009E73"),
        ("squad_llama3b_p2", "#CC79A7"),
    ):
        values = bias[arm]["k0_by_previous_depth"]
        xs = sorted(int(k) for k in values)
        ys = [values[str(k)]["mean_j"] for k in xs]
        ax2.plot(
            xs,
            ys,
            marker="o",
            label=arm.replace("squad_", "").replace("_p1", "").replace("_p2", ""),
            color=color,
        )
    ax2.set_xlabel("Previous row's depth")
    ax2.set_ylabel("k=0 energy (J)")
    ax2.set_title("k=0 depends on the neighbour")
    ax2.legend(fontsize=6)
    ax2.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(OUT, dpi=DPI)
    print(f"wrote {OUT} at {DPI} dpi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
