"""70 - Regenerate every deck figure at its FINAL on-slide size.

Why this exists
---------------
The first figure pass drew each chart 7-12 inches wide and then placed it 4.6-7.1
inches wide on the slide. Every label inside the PNG therefore shrank by that
ratio, so type that was 10 pt in the source arrived as 6-8 pt on screen. The
deck audit only inspected PowerPoint text boxes, so it reported a clean 14 pt
floor while the figures were far below it.

Rule used here: each figure is created at exactly the size it will occupy on the
slide (points / 72 = inches), and every font inside it is set in final points.
Nothing is scaled at placement time, so what is drawn is what is projected.

The slide places each image at the same nominal size recorded in SIZES.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Slides" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#14241B"
FOREST = "#1F5134"
TEAL = "#0F766E"
AMBER = "#8A4B00"
MUTED = "#4A5A52"
LIME = "#C8F04F"
GRIDC = "#D5DFD8"

# Final placement on the slide, in points (width x height). The deck uses these
# same numbers, so 1 figure point = 1 slide point.
SIZES = {
    "fig_pipeline": (470, 161),
    "fig_readers": (384, 243),
    "fig_sweep": (520, 338),
    "fig_block_timeline": (852, 232),
    "fig_window_vs_block": (540, 258),
    "fig_drift": (556, 256),
    "fig_margin": (500, 214),
    "fig_rq": (410, 230),
    "fig_dose": (410, 230),
    "fig_token": (420, 205),
    "fig_savings_forest": (470, 162),
    "fig_ek": (500, 286),
}

BASE = 14.0


def _setup(name: str) -> tuple[plt.Figure, plt.Axes | None, float, float]:
    w_pt, h_pt = SIZES[name]
    w_in, h_in = w_pt / 72, h_pt / 72
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": BASE,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": BASE,
            "ytick.labelsize": BASE,
            "axes.labelsize": BASE,
            "legend.fontsize": BASE,
            "axes.titlesize": BASE + 1,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "lines.linewidth": 2.0,
        }
    )
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    return fig, ax, w_in, h_in


def _save(fig: plt.Figure, name: str) -> None:
    p = OUT / f"{name}.png"
    fig.savefig(p, dpi=300, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"  {name}.png  {p.stat().st_size // 1024} KB  {SIZES[name][0]}x{SIZES[name][1]} pt")


# ---------------------------------------------------------------- data loaders
def estimates(rel: str, drop_zero: bool = True) -> list[dict]:
    rows = []
    with (ROOT / rel).open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k = int(r["k"])
            if drop_zero and k == 0:
                continue
            rows.append({"k": k, "acc": float(r["accuracy"]), "epc": float(r.get("e_per_correct", 0) or 0)})
    return rows


# ---------------------------------------------------------------- diagrams
def fig_pipeline() -> None:
    fig, ax, _, _ = _setup("fig_pipeline")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 34)
    ax.axis("off")

    stages = [("Question", "SQuAD"), ("Retrieve", "BM25"), ("Prompt", "k = 0-32"), ("Reader", "4-bit"), ("Score", "exact")]
    xs = [1.0, 21.0, 41.0, 61.0, 81.0]
    w, h, y0 = 18.0, 14.0, 14.5
    for x, (head, sub) in zip(xs, stages):
        ax.add_patch(Rectangle((x, y0), w, h, facecolor="white", edgecolor=FOREST, linewidth=1.8, zorder=3))
        ax.text(x + w / 2, y0 + h * 0.66, head, ha="center", va="center", fontsize=BASE, fontweight="bold", color=INK, zorder=4)
        ax.text(x + w / 2, y0 + h * 0.28, sub, ha="center", va="center", fontsize=BASE - 1, color=MUTED, zorder=4)
    for i in range(4):
        ax.add_patch(FancyArrowPatch((xs[i] + w, y0 + h / 2), (xs[i + 1], y0 + h / 2), arrowstyle="-|>",
                                     mutation_scale=12, color=TEAL, linewidth=1.6, zorder=5))

    ax.add_patch(Rectangle((61.0, 9.6), 38.0, 3.2, facecolor="#DFF0E8", edgecolor=TEAL, linewidth=1.0, zorder=2))
    ax.text(80.0, 11.2, "GPU power measured", ha="center", va="center", fontsize=BASE - 1, color=FOREST,
            fontweight="bold", zorder=6)
    ax.text(30.0, 11.2, "CPU only", ha="center", va="center", fontsize=BASE - 1, color=AMBER, style="italic")

    ax.add_patch(Rectangle((66.0, 1.6), 28.0, 6.4, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.2, zorder=3))
    ax.text(80.0, 5.9, "NVML sensor", ha="center", va="center", fontsize=BASE - 1, fontweight="bold", color=FOREST, zorder=4)
    ax.text(80.0, 3.1, "every 100 ms", ha="center", va="center", fontsize=BASE - 2, color=MUTED, zorder=4)
    ax.annotate("", xy=(80.0, 9.3), xytext=(80.0, 8.2), arrowprops=dict(arrowstyle="-|>", color=TEAL, linewidth=1.2))

    _save(fig, "fig_pipeline")


def fig_readers() -> None:
    fig, ax, _, _ = _setup("fig_readers")
    arms = [
        ("Qwen3.5-4B", "analysis/squad_qwen4b_p1/estimates.csv", FOREST, "o", "-"),
        ("Llama-3.2-3B", "analysis/squad_llama3b_p2/estimates.csv", AMBER, "s", "--"),
        ("Qwen2.5-1.5B", "analysis/squad_qwen15b_p2/estimates.csv", TEAL, "^", ":"),
    ]
    for label, rel, colour, marker, style in arms:
        rows = estimates(rel)
        ax.plot([r["k"] for r in rows], [100 * r["acc"] for r in rows], marker=marker, markersize=5,
                linewidth=2.0, color=colour, linestyle=style, label=label)
    ax.set_xlabel("depth k", fontsize=BASE)
    ax.set_ylabel("accuracy (%)", fontsize=BASE)
    ax.set_xticks([1, 2, 4, 8, 16, 32])
    ax.tick_params(labelsize=BASE - 1)
    ax.set_ylim(28, 55)
    ax.grid(axis="y", color=GRIDC, linewidth=0.7)
    ax.legend(frameon=False, fontsize=BASE - 1, loc="lower right", handlelength=1.4)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_readers")


def fig_sweep() -> None:
    fig, ax, _, _ = _setup("fig_sweep")
    ks = [0, 1, 2, 4, 8, 16, 32]
    nrows = 10
    rng = [2, 5, 0, 6, 3, 1, 4, 6, 2, 0]
    for r in range(nrows):
        for c, _k in enumerate(ks):
            order = (c + rng[r]) % len(ks)
            alpha = 0.18 + 0.42 * (order / (len(ks) - 1))
            ax.add_patch(Rectangle((c + 0.05, r + 0.05), 0.90, 0.90, facecolor=TEAL, alpha=alpha, edgecolor="none"))
            ax.text(c + 0.5, r + 0.5, str(order + 1), ha="center", va="center", fontsize=BASE - 1,
                    color=INK, fontweight="bold")
    ax.set_xlim(0, len(ks))
    ax.set_ylim(0, nrows)
    ax.set_xticks([i + 0.5 for i in range(len(ks))])
    ax.set_xticklabels([f"{k}" for k in ks], fontsize=BASE - 1)
    ax.set_yticks([])
    ax.set_xlabel("depth k", fontsize=BASE)
    ax.tick_params(length=0)
    for s in ["left", "bottom"]:
        ax.spines[s].set_visible(False)
    fig.tight_layout(pad=0.3)
    _save(fig, "fig_sweep")


def fig_block_timeline() -> None:
    fig, ax, _, _ = _setup("fig_block_timeline")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 24)
    ax.axis("off")
    blocks = [(2, 16), (20, 16), (38, 16), (56, 16), (74, 16)]
    for i, (x, w) in enumerate(blocks):
        ax.add_patch(Rectangle((x, 7), w, 9, facecolor="#D8E9E2", edgecolor=TEAL, linewidth=1.2))
        ax.text(x + w / 2, 12.4, f"batch {i + 1}", ha="center", va="center", fontsize=BASE, fontweight="bold", color=FOREST)
        ax.text(x + w / 2, 9.4, "200 questions", ha="center", va="center", fontsize=BASE - 2, color=MUTED)
        if i < 4:
            ax.add_patch(Rectangle((x + w, 7), 2, 9, facecolor="white", edgecolor=GRIDC, linewidth=0.8, hatch="//"))
            ax.text(x + w + 1, 11.5, "rest\n120 s", ha="center", va="center", fontsize=BASE - 2, color=MUTED)
    ax.annotate("", xy=(2, 18.4), xytext=(18, 18.4), arrowprops=dict(arrowstyle="<|-|>", color=AMBER, linewidth=1.4))
    ax.text(10, 20.4, "one energy window", ha="center", fontsize=BASE - 1, color=AMBER, fontweight="bold")
    ax.text(50, 2.6, "idle power read from the end of each rest, so the GPU is cool and steady",
            ha="center", fontsize=BASE - 2, color=MUTED)
    _save(fig, "fig_block_timeline")


def fig_window_vs_block() -> None:
    fig, axes, _, _ = _setup("fig_window_vs_block")
    fig, axes = plt.subplots(2, 1, figsize=(SIZES["fig_window_vs_block"][0] / 72, SIZES["fig_window_vs_block"][1] / 72),
                             sharex=True, sharey=True)
    xs = [i / 200 * 10 for i in range(201)]
    ys = [3.0 + 4.2 * (1 - math.exp(-((x - 0.55) ** 2) / 0.9)) for x in xs]
    segs = [(0.6, 1.5), (1.7, 2.6), (2.8, 3.7)]

    ax = axes[0]
    ax.plot(xs, ys, color=FOREST, linewidth=2.0, zorder=3)
    for a, b in segs:
        ax.add_patch(Rectangle((a, 0), b - a, 7.2, facecolor=AMBER, alpha=0.25, edgecolor=AMBER, linewidth=1.0, zorder=2))
    for a, b in [(1.5, 1.7), (2.6, 2.8)]:
        ax.add_patch(Rectangle((a, 0), b - a, 7.2, facecolor="white", edgecolor=AMBER, linewidth=1.0, hatch="///", zorder=4))
    ax.set_title("one window per question: gaps are lost", fontsize=BASE, color=AMBER, loc="left", pad=4, fontweight="bold")
    ax.set_ylabel("power", fontsize=BASE - 1)

    ax = axes[1]
    ax.plot(xs, ys, color=FOREST, linewidth=2.0, zorder=3)
    ax.add_patch(Rectangle((0.6, 0), 3.1, 7.2, facecolor=TEAL, alpha=0.22, edgecolor=TEAL, linewidth=1.4, zorder=2))
    ax.set_title("one window per batch: every gap counted", fontsize=BASE, color=TEAL, loc="left", pad=4, fontweight="bold")
    ax.set_ylabel("power", fontsize=BASE - 1)
    ax.set_xlabel("time within one batch", fontsize=BASE - 1)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.6)
    for ax in axes:
        ax.set_xticks([])
        ax.grid(axis="y", color=GRIDC, linewidth=0.6)
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(labelsize=BASE - 2)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_window_vs_block")


# ---------------------------------------------------------------- charts
def fig_drift() -> None:
    fig, ax, _, _ = _setup("fig_drift")
    p = ROOT / "analysis" / "measurement_hardening" / "squad_qwen4b_p7_blocks_full" / "replays.json"
    rep = json.loads(p.read_text(encoding="utf-8"))
    ratios = [r["total_ratio"] for r in rep["per_replay"]]
    idx = list(range(1, len(ratios) + 1))
    ax.plot(idx, ratios, marker="o", markersize=5, color=AMBER, linewidth=2.0)
    ax.axhline(1.0, color=GRIDC, linewidth=1.4, linestyle="--")
    ax.text(9.8, 1.003, "batch level", fontsize=BASE - 2, color=MUTED, ha="right", va="bottom")
    ax.set_xlabel("replay number", fontsize=BASE)
    ax.set_ylabel("replay / batch", fontsize=BASE)
    ax.set_xticks(idx)
    ax.tick_params(labelsize=BASE - 2)
    ax.set_ylim(min(ratios) - 0.03, max(ratios) + 0.04)
    ax.grid(axis="y", color=GRIDC, linewidth=0.6)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_drift")


def fig_margin() -> None:
    fig, ax, _, _ = _setup("fig_margin")
    point, lo = -4.30, -6.17
    ax.axvline(-5, color=FOREST, linestyle="--", linewidth=1.8)
    ax.axvline(0, color=GRIDC, linewidth=1.2)
    ax.plot([lo, point], [1, 1], color=AMBER, linewidth=3.0, solid_capstyle="round")
    ax.plot(lo, 1, "o", color=AMBER, markersize=7)
    ax.plot(point, 1, "o", color=INK, markersize=8)
    ax.text(-5.2, 1.52, "5 pp limit", fontsize=BASE, color=FOREST, ha="right", fontweight="bold")
    ax.text(point + 0.2, 1.12, "measured -4.30", fontsize=BASE - 1, fontweight="bold", color=INK)
    ax.text(lo - 0.3, 0.68, "lower bound -6.17", fontsize=BASE - 1, color=AMBER, ha="left")
    ax.set_xlim(-9, 2)
    ax.set_ylim(0.4, 1.75)
    ax.set_yticks([])
    ax.set_xlabel("accuracy change (pp)", fontsize=BASE)
    ax.tick_params(labelsize=BASE - 1)
    ax.spines["left"].set_visible(False)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_margin")


def fig_rq() -> None:
    fig, ax, _, _ = _setup("fig_rq")
    arms = {
        "Qwen4B": (0.775, 0.892, 0.592, 0.549),
        "Qwen1.5B": (0.700, 0.814, 0.610, 0.530),
        "Llama3B": (0.690, 0.804, 0.600, 0.467),
        "HotpotQA": (0.780, 0.836, 0.560, 0.644),
    }
    x = range(len(arms))
    w = 0.36
    dr = [100 * (v[1] - v[0]) for v in arms.values()]
    dq = [100 * (v[3] - v[2]) for v in arms.values()]
    ax.bar([i - w / 2 for i in x], dr, w, color=TEAL, label="recall")
    ax.bar([i + w / 2 for i in x], dq, w, color=AMBER, label="precision")
    ax.axhline(0, color=INK, linewidth=1.0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(list(arms), fontsize=BASE - 2)
    ax.set_ylabel("change (pp)", fontsize=BASE)
    ax.legend(frameon=False, fontsize=BASE - 1, loc="lower left", handlelength=1.2)
    ax.grid(axis="y", color=GRIDC, linewidth=0.6)
    ax.tick_params(labelsize=BASE - 2)
    ax.set_ylim(min(dq) - 4, max(dr) + 3)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_rq")


def fig_dose() -> None:
    fig, ax, _, _ = _setup("fig_dose")
    d = json.loads((ROOT / "analysis" / "qc_distractor" / "dose_curve.json").read_text(encoding="utf-8"))
    per = d["per_dose"]
    doses = sorted(per, key=int)
    acc = [100 * per[k]["accuracy"] for k in doses]
    lo = [100 * per[k]["wilson_ci95"][0] for k in doses]
    hi = [100 * per[k]["wilson_ci95"][1] for k in doses]
    xs = list(range(len(doses)))
    ax.errorbar(xs, acc, yerr=[[a - l for a, l in zip(acc, lo)], [h - a for a, h in zip(acc, hi)]],
                fmt="o-", color=TEAL, linewidth=2.0, markersize=6, capsize=3, ecolor=MUTED)
    ax.set_xticks(xs)
    ax.set_xticklabels([str(k) for k in doses], fontsize=BASE - 1)
    ax.set_xlabel("distractors added", fontsize=BASE)
    ax.set_ylabel("accuracy (%)", fontsize=BASE)
    ax.grid(axis="y", color=GRIDC, linewidth=0.6)
    ax.tick_params(labelsize=BASE - 1)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_dose")


def fig_token() -> None:
    fig, ax, _, _ = _setup("fig_token")
    tpre = [0, 4000]
    j = [13.88, 13.88 + 0.02549 * 4000]
    ax.plot(tpre, j, color=TEAL, linewidth=2.2)
    for val, lab in [(26.22, "k=4"), (75.93, "padded"), (87.22, "k=32")]:
        ax.axhline(val, color=GRIDC, linewidth=1.0, linestyle=":")
        ax.text(3950, val + 2.5, f"{lab} {val:.1f} J", fontsize=BASE - 2, color=MUTED, ha="right")
    ax.set_xlabel("prefill tokens", fontsize=BASE)
    ax.set_ylabel("energy (J)", fontsize=BASE)
    ax.tick_params(labelsize=BASE - 2)
    ax.set_xlim(0, 4000)
    ax.set_ylim(0, 120)
    ax.grid(color=GRIDC, linewidth=0.5)
    ax.text(60, 108, "R2 = 0.9575", fontsize=BASE, fontweight="bold", color=FOREST)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_token")


def fig_savings_forest() -> None:
    fig, ax, _, _ = _setup("fig_savings_forest")
    blk = json.loads((ROOT / "analysis" / "measurement_hardening" / "squad_qwen4b_p7_blocks_full"
                      / "estimates.json").read_text(encoding="utf-8"))["savings"]
    vals = [
        ("windows", 58.17, 56.02, 60.14, AMBER),
        ("batch", 100 * blk["point"], 100 * blk["ci95"][0], 100 * blk["ci95"][1], TEAL),
        ("replay", 78.90, 73.85, 80.11, MUTED),
    ]
    for i, (lab, v, a, b, c) in enumerate(vals):
        y = len(vals) - i
        ax.plot([a, b], [y, y], color=c, linewidth=3.0, solid_capstyle="round")
        ax.plot(v, y, "o", color=c, markersize=7)
        ax.text(b + 1.4, y, f"{v:.1f}%", va="center", fontsize=BASE - 1, fontweight="bold", color=c)
    ax.axvline(20, color=FOREST, linestyle=":", linewidth=1.4)
    ax.text(21, len(vals) + 0.45, "20% floor", fontsize=BASE - 2, color=FOREST)
    ax.set_yticks(range(1, len(vals) + 1))
    ax.set_yticklabels([v[0] for v in vals][::-1], fontsize=BASE - 1)
    ax.set_xlabel("energy saved (%)", fontsize=BASE)
    ax.set_xlim(10, 92)
    ax.set_ylim(0.4, len(vals) + 0.9)
    ax.tick_params(axis="x", labelsize=BASE - 2)
    ax.tick_params(length=0)
    ax.grid(axis="x", color=GRIDC, linewidth=0.6)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_savings_forest")


def fig_ek() -> None:
    fig, ax, _, _ = _setup("fig_ek")
    rows = estimates("analysis/squad_qwen4b_p1/estimates.csv")
    ks = [r["k"] for r in rows]
    ax.plot(ks, [r["epc"] for r in rows], marker="o", markersize=6, color=TEAL, linewidth=2.2)
    ax.set_xlabel("depth k", fontsize=BASE)
    ax.set_ylabel("J per correct", fontsize=BASE)
    ax.set_xticks(ks)
    ax.tick_params(labelsize=BASE - 1)
    ax.set_ylim(0, 210)
    ax.grid(axis="y", color=GRIDC, linewidth=0.6)
    ax2 = ax.twinx()
    ax2.plot(ks, [100 * r["acc"] for r in rows], marker="s", markersize=5, color=AMBER, linewidth=1.8, linestyle="--")
    ax2.set_ylabel("accuracy (%)", fontsize=BASE, color=AMBER)
    ax2.tick_params(labelsize=BASE - 2, colors=AMBER)
    ax2.set_ylim(0, 60)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(AMBER)
    fig.tight_layout(pad=0.4)
    _save(fig, "fig_ek")


def main() -> int:
    for fn in (
        fig_pipeline, fig_readers, fig_sweep, fig_block_timeline, fig_window_vs_block,
        fig_drift, fig_margin, fig_rq, fig_dose, fig_token, fig_savings_forest, fig_ek,
    ):
        fn()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
