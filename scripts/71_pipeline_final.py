"""Pipeline at 14 pt: four stages, sized to fit 470x120 pt."""

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

W_PT, H_PT = 470, 126
BASE = 14

plt.rcParams.update({"font.family": "DejaVu Sans", "savefig.facecolor": "white", "figure.facecolor": "white"})


def main() -> int:
    fig, ax = plt.subplots(figsize=(W_PT / 72, H_PT / 72))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 27)
    ax.axis("off")

    stages = [("Question", "SQuAD"), ("Retrieve", "BM25, top-k"), ("Reader", "4-bit GPU"), ("Score", "exact")]
    xs = [0.5, 25.5, 50.5, 75.5]
    w, h, y0 = 23.0, 13.0, 10.0
    for x, (head, sub) in zip(xs, stages):
        ax.add_patch(Rectangle((x, y0), w, h, facecolor="white", edgecolor=FOREST, linewidth=1.6, zorder=3))
        ax.text(x + w / 2, y0 + h * 0.68, head, ha="center", va="center", fontsize=BASE - 1,
                fontweight="bold", color=INK, zorder=4)
        ax.text(x + w / 2, y0 + h * 0.27, sub, ha="center", va="center", fontsize=BASE - 3,
                color=MUTED, zorder=4)
    for i in range(3):
        ax.add_patch(FancyArrowPatch((xs[i] + w, y0 + h / 2), (xs[i + 1], y0 + h / 2), arrowstyle="-|>",
                                     mutation_scale=11, color=TEAL, linewidth=1.4, zorder=5))

    # measured span under the reader
    ax.add_patch(Rectangle((50.5, 6.0), 48.0, 2.6, facecolor="#DFF0E8", edgecolor=TEAL, linewidth=0.9, zorder=2))
    ax.text(74.5, 7.3, "GPU power measured", ha="center", va="center", fontsize=BASE - 3,
            color=FOREST, fontweight="bold", zorder=6)
    ax.text(37.0, 7.3, "CPU only", ha="center", va="center", fontsize=BASE - 3, color=AMBER, style="italic")

    # sensor chip
    ax.add_patch(Rectangle((56.0, 0.4), 32.0, 4.2, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.0, zorder=3))
    ax.text(72.0, 2.5, "NVML, every 100 ms", ha="center", va="center", fontsize=BASE - 3,
            fontweight="bold", color=FOREST, zorder=4)
    ax.annotate("", xy=(72.0, 5.9), xytext=(72.0, 4.8), arrowprops=dict(arrowstyle="-|>", color=TEAL, linewidth=1.0))

    fig.savefig(OUT / "fig_pipeline.png", dpi=300, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"  fig_pipeline.png  {(OUT / 'fig_pipeline.png').stat().st_size // 1024} KB  {W_PT}x{H_PT} pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
