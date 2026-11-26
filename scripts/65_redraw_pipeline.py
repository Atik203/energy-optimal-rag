"""Pipeline figure, second attempt: short labels that fit, clear sensor scope."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "Slides" / "figures"

INK = "#14241B"
FOREST = "#1F5134"
TEAL = "#0F766E"
MUTED = "#4A5A52"
AMBER = "#8A4B00"

plt.rcParams.update({"font.family": "DejaVu Sans", "savefig.facecolor": "white", "figure.facecolor": "white"})


def main() -> int:
    fig, ax = plt.subplots(figsize=(12.0, 4.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 34)
    ax.axis("off")

    w, h, y0 = 17.0, 10.5, 18.0
    xs = [1.5, 21.5, 41.5, 61.5, 81.5]
    heads = ["Question", "Retrieve", "Prompt", "Reader", "Score"]
    subs = ["SQuAD text", "BM25 search", "k = 0 ... 32", "4-bit model", "exact match"]

    for x, head, sub in zip(xs, heads, subs):
        ax.add_patch(Rectangle((x, y0), w, h, facecolor="white", edgecolor=FOREST, linewidth=2.0, zorder=3))
        ax.text(x + w / 2, y0 + h * 0.64, head, ha="center", va="center", fontsize=12,
                fontweight="bold", color=INK, zorder=4)
        ax.text(x + w / 2, y0 + h * 0.26, sub, ha="center", va="center", fontsize=9.5, color=MUTED, zorder=4)

    for i in range(4):
        ax.add_patch(FancyArrowPatch((xs[i] + w, y0 + h / 2), (xs[i + 1], y0 + h / 2),
                                     arrowstyle="-|>", mutation_scale=17, color=TEAL, linewidth=1.8, zorder=5))

    # measured span: reader only (and the answer is decoded inside the reader)
    ax.add_patch(Rectangle((61.5, 14.2), 37.0, 2.3, facecolor="#DFF0E8", edgecolor=TEAL, linewidth=1.2, zorder=2))
    ax.text(80.0, 15.35, "GPU power is measured here", ha="center", va="center", fontsize=9.5,
            color=FOREST, fontweight="bold", zorder=6)

    # CPU note under retrieval
    ax.text(xs[1] + w / 2, 15.3, "runs on the CPU", ha="center", va="center", fontsize=9.5,
            color=AMBER, style="italic")

    # sensor
    ax.add_patch(Rectangle((66.0, 3.2), 28.0, 7.0, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.6, zorder=3))
    ax.text(80.0, 8.4, "NVML power sensor", ha="center", va="center", fontsize=9.5,
            fontweight="bold", color=FOREST, zorder=4)
    ax.text(80.0, 5.2, "one reading every 100 ms", ha="center", va="center", fontsize=8.5,
            color=MUTED, zorder=4)
    ax.annotate("", xy=(80.0, 13.9), xytext=(80.0, 10.5),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, linewidth=1.5))

    ax.text(1.5, 8.8, "one question at seven depths, all on one GPU", fontsize=9.5, color=MUTED)

    fig.savefig(OUT / "fig_pipeline.png", dpi=300, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"  fig_pipeline.png  {(OUT / 'fig_pipeline.png').stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
