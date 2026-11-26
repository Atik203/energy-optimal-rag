"""Fix the diagram figures: axes must fill the whole figure at final size."""

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
AMBER = "#8A4B00"
MUTED = "#4A5A52"
GRIDC = "#D5DFD8"

plt.rcParams.update({"font.family": "DejaVu Sans", "savefig.facecolor": "white", "figure.facecolor": "white"})


def full_axes(w_pt: float, h_pt: float):
    """Figure whose axes fill it exactly, so 1 unit of xlim = 1% of width."""
    fig = plt.figure(figsize=(w_pt / 72, h_pt / 72))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def pipeline() -> None:
    fig, ax = full_axes(470, 126)
    stages = [("Question", "SQuAD"), ("Retrieve", "BM25, top-k"), ("Reader", "4-bit GPU"), ("Score", "exact")]
    xs = [1.0, 25.5, 50.0, 74.5]
    w, h, y0 = 22.0, 40.0, 44.0
    for x, (head, sub) in zip(xs, stages):
        ax.add_patch(Rectangle((x, y0), w, h, facecolor="white", edgecolor=FOREST, linewidth=1.4, zorder=3))
        ax.text(x + w / 2, y0 + h * 0.68, head, ha="center", va="center", fontsize=13,
                fontweight="bold", color=INK, zorder=4)
        ax.text(x + w / 2, y0 + h * 0.26, sub, ha="center", va="center", fontsize=11, color=MUTED, zorder=4)
    for i in range(3):
        ax.add_patch(FancyArrowPatch((xs[i] + w, y0 + h / 2), (xs[i + 1], y0 + h / 2), arrowstyle="-|>",
                                     mutation_scale=10, color=TEAL, linewidth=1.3, zorder=5))

    ax.add_patch(Rectangle((50.0, 31.0), 49.0, 8.0, facecolor="#DFF0E8", edgecolor=TEAL, linewidth=0.9, zorder=2))
    ax.text(74.5, 35.0, "GPU power measured", ha="center", va="center", fontsize=11,
            color=FOREST, fontweight="bold", zorder=6)
    ax.text(36.0, 35.0, "CPU only", ha="center", va="center", fontsize=11, color=AMBER, style="italic")

    ax.add_patch(Rectangle((55.0, 4.0), 38.0, 16.0, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.0, zorder=3))
    ax.text(74.0, 12.0, "NVML sensor", ha="center", va="center", fontsize=11, fontweight="bold", color=FOREST, zorder=4)
    ax.annotate("", xy=(74.0, 30.4), xytext=(74.0, 20.6),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, linewidth=1.1))

    fig.savefig(OUT / "fig_pipeline.png", dpi=300)
    plt.close(fig)
    print("  fig_pipeline.png  470x126 pt")


def timeline() -> None:
    fig, ax = full_axes(852, 232)
    n, gap = 5, 4.2
    bw = (100 - 2 - gap * (n - 1)) / n
    for i in range(n):
        x = 1 + i * (bw + gap)
        ax.add_patch(Rectangle((x, 26), bw, 34, facecolor="#D8E9E2", edgecolor=TEAL, linewidth=1.1))
        ax.text(x + bw / 2, 47, f"batch {i + 1}", ha="center", va="center", fontsize=13,
                fontweight="bold", color=FOREST)
        ax.text(x + bw / 2, 34, "200 questions", ha="center", va="center", fontsize=11, color=MUTED)
        if i < n - 1:
            ax.add_patch(Rectangle((x + bw, 26), gap, 34, facecolor="white", edgecolor=GRIDC,
                                   linewidth=0.7, hatch="//"))
            ax.text(x + bw + gap / 2, 43, "rest\n120 s", ha="center", va="center", fontsize=8, color=MUTED)
    ax.annotate("", xy=(1, 68), xytext=(1 + bw, 68), arrowprops=dict(arrowstyle="<|-|>", color=AMBER, linewidth=1.3))
    ax.text(1 + bw / 2, 76, "one energy window", ha="center", fontsize=11, color=AMBER, fontweight="bold")
    ax.text(50, 12, "idle power is read from the end of each rest, then subtracted",
            ha="center", fontsize=10, color=MUTED)
    fig.savefig(OUT / "fig_block_timeline.png", dpi=300)
    plt.close(fig)
    print("  fig_block_timeline.png  852x232 pt")


def main() -> int:
    pipeline()
    timeline()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
