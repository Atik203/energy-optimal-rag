"""R/Q figure with the registered per-arm deltas (Qwen precision is -2.8, not -4.3)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Slides" / "figures"

INK = "#14241B"
TEAL = "#0F766E"
AMBER = "#8A4B00"
GRIDC = "#D5DFD8"
W_PT, H_PT = 410, 230
BASE = 13

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": BASE,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": "#4A5A52",
        "xtick.labelsize": BASE - 1,
        "ytick.labelsize": BASE - 1,
        "axes.labelsize": BASE,
        "legend.fontsize": BASE - 1,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def main() -> int:
    d = json.loads((ROOT / "analysis" / "recall_precision.json").read_text(encoding="utf-8"))
    labels, dr, dq = [], [], []
    for arm, v in d.items():
        if not isinstance(v, dict) or "recall" not in v:
            continue
        hi = "32" if "32" in v["recall"] else str(v["depths"][-1])
        labels.append(
            {"squad_qwen4b_p1": "Qwen4B", "squad_qwen15b_p2": "Qwen1.5B",
             "squad_llama3b_p2": "Llama3B", "hotpot_qwen4b_p2": "HotpotQA"}.get(arm, arm)
        )
        dr.append(100 * (v["recall"][hi] - v["recall"]["4"]))
        dq.append(100 * (v["precision"][hi] - v["precision"]["4"]))

    fig, ax = plt.subplots(figsize=(W_PT / 72, H_PT / 72))
    x = range(len(labels))
    w = 0.36
    ax.bar([i - w / 2 for i in x], dr, w, color=TEAL, label="recall")
    ax.bar([i + w / 2 for i in x], dq, w, color=AMBER, label="precision")
    ax.axhline(0, color=INK, linewidth=1.0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("change (pp)")
    ax.legend(frameon=False, loc="lower left", handlelength=1.2)
    ax.grid(axis="y", color=GRIDC, linewidth=0.6)
    ax.set_ylim(min(dq) - 5, max(dr) + 4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig_rq.png", dpi=300)
    plt.close(fig)
    print("  fig_rq.png  pairs:", list(zip(labels, [round(v, 1) for v in dr], [round(v, 1) for v in dq])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
