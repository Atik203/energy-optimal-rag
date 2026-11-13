"""Generate the slide-12 flow diagram as SVG and a 600-DPI PNG.

The diagram is intentionally typographic: large labels, thick borders, and
high-contrast text so it remains readable on a projector. Run from the web/
directory with the repository's Python:

    python scripts/make_flow_diagram.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
PUBLIC.mkdir(parents=True, exist_ok=True)

INK = "#000000"
INK_SOFT = "#111827"
WHITE = "#ffffff"
DEEP = "#123a2a"
TEAL = "#0f766e"
AMBER = "#9a4f00"
ROSE = "#a3112f"
LINE = "#b8c0c8"

plt.rcParams.update(
    {
        "font.family": "Segoe UI",
        "font.size": 18,
        "svg.fonttype": "none",
    }
)

FIG_W, FIG_H = 16.0, 6.7
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=600)
fig.patch.set_facecolor(WHITE)
ax.set_facecolor(WHITE)
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")


def rounded_box(
    x: float,
    y: float,
    w: float,
    h: float,
    number: str,
    title: str,
    subtitle: str,
    color: str,
    title_size: float,
    subtitle_size: float,
) -> None:
    """Draw one high-contrast step box with a numbered badge."""
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.18",
            linewidth=3.2,
            edgecolor=color,
            facecolor=WHITE,
            zorder=2,
        )
    )
    # Badge, top-left, above the title
    ax.add_patch(
        FancyBboxPatch(
            (x + 0.16, y + h - 0.55),
            0.52,
            0.34,
            boxstyle="round,pad=0.01,rounding_size=0.08",
            linewidth=0,
            facecolor=color,
            zorder=3,
        )
    )
    ax.text(
        x + 0.42,
        y + h - 0.38,
        number,
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color=WHITE,
        fontfamily="Consolas",
        zorder=4,
    )
    ax.text(
        x + 0.16,
        y + h - 0.78,
        title,
        ha="left",
        va="top",
        fontsize=title_size,
        fontweight="bold",
        color=INK,
        zorder=4,
    )
    ax.text(
        x + 0.16,
        y + 0.28,
        subtitle,
        ha="left",
        va="bottom",
        fontsize=subtitle_size,
        fontweight="semibold",
        color=INK_SOFT,
        linespacing=1.25,
        zorder=4,
    )


def arrow(x0: float, y0: float, x1: float, y1: float, color: str) -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=22,
            linewidth=3.2,
            color=color,
            shrinkA=0,
            shrinkB=0,
            zorder=1,
        )
    )


# ---------------------------------------------------------------------------
# Lane 1 — experiment pipeline
# ---------------------------------------------------------------------------

ax.text(0.08, 6.22, "EXPERIMENT PIPELINE", fontsize=21, fontweight="bold", color=TEAL, ha="left")
ax.text(0.08, 5.86, "one controlled sweep", fontsize=14.5, fontweight="semibold", color=INK_SOFT, ha="left")

top = [
    ("01", "PREPARE", "SQuAD +\nHotpotQA", TEAL),
    ("02", "INDEX", "BM25\ncorpus", DEEP),
    ("03", "SWEEP", "7 depths\n× n", TEAL),
    ("04", "MEASURE", "NVML +\nblocks", DEEP),
    ("05", "SCORE", "EM +\nbootstrap", TEAL),
    ("06", "ANALYZE", "E(k), N*,\npolicy", DEEP),
]

top_y, top_h, top_w, top_gap = 3.55, 2.0, 2.35, 0.25
top_x0 = 0.35
for i, (num, title, sub, color) in enumerate(top):
    x = top_x0 + i * (top_w + top_gap)
    rounded_box(x, top_y, top_w, top_h, num, title, sub, color, 20.0, 14.5)
    if i < len(top) - 1:
        arrow(x + top_w + 0.02, top_y + top_h / 2, x + top_w + top_gap - 0.02, top_y + top_h / 2, TEAL)


# ---------------------------------------------------------------------------
# Lane 2 — decision flow
# ---------------------------------------------------------------------------

ax.text(0.08, 2.98, "DECISION FLOW", fontsize=21, fontweight="bold", color=AMBER, ha="left")
ax.text(0.08, 2.62, "pre-registered gates", fontsize=14.5, fontweight="semibold", color=INK_SOFT, ha="left")

bottom = [
    ("1", "FREEZE PREREG", "before\noutcomes", AMBER),
    ("2", "P0 GOLDEN", "200-question\ncheck", DEEP),
    ("3", "P1 POWERED", "n = 1,000\n× 7", AMBER),
    ("4", "GATES", "G1–G5\nK1–K7", ROSE),
    ("5", "P2 / P3 / P4", "replication\npolicy · theory", DEEP),
]

bot_y, bot_h, bot_w, bot_gap = 0.55, 1.95, 2.86, 0.30
bot_x0 = 0.30
for i, (num, title, sub, color) in enumerate(bottom):
    x = bot_x0 + i * (bot_w + bot_gap)
    rounded_box(x, bot_y, bot_w, bot_h, num, title, sub, color, 19.0, 14.0)
    if i < len(bottom) - 1:
        arrow(x + bot_w + 0.02, bot_y + bot_h / 2, x + bot_w + bot_gap - 0.02, bot_y + bot_h / 2, AMBER)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

svg_path = PUBLIC / "flow-diagram.svg"
png_path = PUBLIC / "flow-diagram.png"
fig.savefig(svg_path, format="svg", bbox_inches="tight", pad_inches=0.06, facecolor=WHITE)
fig.savefig(png_path, format="png", dpi=600, bbox_inches="tight", pad_inches=0.06, facecolor=WHITE)
plt.close(fig)

print(f"wrote {svg_path} ({svg_path.stat().st_size:,} bytes)")
print(f"wrote {png_path} ({png_path.stat().st_size:,} bytes)")
