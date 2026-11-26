"""Figure: accuracy against depth for each reader tested.

Every point is read from the registered estimates CSV of that arm.
Shows the central claim of the deck: the shape of A(k) depends on the reader.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Slides" / "figures"

INK = "#14241B"
FOREST = "#1F5134"
TEAL = "#0F766E"
AMBER = "#8A4B00"
MUTED = "#4A5A52"
GRIDC = "#D5DFD8"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 12,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)

ARMS = [
    ("Qwen3.5-4B (main)", "analysis/squad_qwen4b_p1/estimates.csv", FOREST, "o", "-"),
    ("Llama-3.2-3B", "analysis/squad_llama3b_p2/estimates.csv", AMBER, "s", "--"),
    ("Qwen2.5-1.5B", "analysis/squad_qwen15b_p2/estimates.csv", TEAL, "^", ":"),
]


def load(path: Path) -> tuple[list[int], list[float]]:
    ks, acc = [], []
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k = int(r["k"])
            if k == 0:
                continue
            ks.append(k)
            acc.append(100 * float(r["accuracy"]))
    return ks, acc


def main() -> int:
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    for label, rel, colour, marker, style in ARMS:
        ks, acc = load(ROOT / rel)
        ax.plot(ks, acc, marker=marker, markersize=7, linewidth=2.3, color=colour,
                linestyle=style, label=label)

    ax.set_xlabel("retrieval depth k (passages in the prompt)")
    ax.set_ylabel("accuracy, exact match (%)")
    ax.set_xticks([1, 2, 4, 8, 16, 32])
    ax.set_ylim(28, 54)
    ax.grid(axis="y", color=GRIDC, linewidth=0.8)
    ax.legend(frameon=False, fontsize=10, loc="upper left")

    ax.annotate("keeps rising", xy=(32, 49.3), xytext=(16.5, 51.4), fontsize=9.5, color=FOREST,
                arrowprops=dict(arrowstyle="->", color=FOREST, linewidth=1.1))
    ax.annotate("peaks at 4, then falls", xy=(16, 43.8), xytext=(17.4, 40.0), fontsize=9.5, color=AMBER,
                arrowprops=dict(arrowstyle="->", color=AMBER, linewidth=1.1))
    ax.annotate("flat", xy=(32, 34.0), xytext=(22.0, 31.0), fontsize=9.5, color=TEAL,
                arrowprops=dict(arrowstyle="->", color=TEAL, linewidth=1.1))

    ax.set_title("Same questions, same retriever, three readers", fontsize=10.5, color=MUTED,
                 loc="left", pad=9)
    fig.savefig(OUT / "fig_readers.png", dpi=300, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print(f"  fig_readers.png  {(OUT / 'fig_readers.png').stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
