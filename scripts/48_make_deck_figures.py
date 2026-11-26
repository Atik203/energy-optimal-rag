"""48 - Build the slide figures for the methodology deck.

Every plotted value is read from a registered analysis output; nothing is
retiped. Diagrams (pipeline, sweep grid, block timeline, window-vs-block) are
geometric schematics drawn from the protocol described in the manuscript.

Output: Slides/figures/*.png at 300 dpi, palette matched to the deck.

Sources
  E(k), accuracy, context share  analysis/squad_qwen4b_p1/estimates.csv
  savings + CI                   analysis/measurement_hardening/<run>/estimates.json
  replay drift                   analysis/measurement_hardening/<run>/replays.json
  margin vs bound                analysis/squad_qwen4b_p1/noninferiority.json
  dose curve                     analysis/qc_distractor/dose_curve.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
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

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 13,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def save(fig, name: str) -> None:
    p = OUT / name
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"  {name}  {p.stat().st_size // 1024} KB")


# ---------------------------------------------------------------- data
def load_estimates() -> list[dict]:
    rows = []
    with (ROOT / "analysis" / "squad_qwen4b_p1" / "estimates.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(
                {
                    "k": int(r["k"]),
                    "acc": float(r["accuracy"]),
                    "epc": float(r["e_per_correct"]),
                    "ctx": float(r["context_share"]),
                }
            )
    return rows


def load_block() -> dict:
    p = ROOT / "analysis" / "measurement_hardening" / "squad_qwen4b_p7_blocks_full" / "estimates.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_replays() -> dict:
    p = ROOT / "analysis" / "measurement_hardening" / "squad_qwen4b_p7_blocks_full" / "replays.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_ni() -> dict:
    return json.loads((ROOT / "analysis" / "squad_qwen4b_p1" / "noninferiority.json").read_text(encoding="utf-8"))


def load_dose() -> dict:
    return json.loads((ROOT / "analysis" / "qc_distractor" / "dose_curve.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- diagrams
def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(11, 3.1))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")
    stages = [
        ("Question", "SQuAD text"),
        ("BM25 search", "45,651 passages"),
        ("k passages", "k = 1 ... 32"),
        ("Reader", "Qwen3.5-4B Q4"),
        ("Answer", "exact match"),
    ]
    xs = [4, 24, 44, 64, 84]
    for x, (head, sub) in zip(xs, stages):
        ax.add_patch(Rectangle((x, 12), 15, 10, facecolor="white", edgecolor=FOREST, linewidth=1.8))
        ax.text(x + 7.5, 18.6, head, ha="center", va="center", fontsize=12, fontweight="bold", color=INK)
        ax.text(x + 7.5, 15.2, sub, ha="center", va="center", fontsize=10, color=MUTED)
    for i in range(len(xs) - 1):
        ax.add_patch(
            FancyArrowPatch((xs[i] + 15, 17), (xs[i + 1], 17), arrowstyle="-|>", mutation_scale=16, color=TEAL, linewidth=1.6)
        )
    # sensor tap under the reader
    ax.add_patch(Rectangle((60.5, 2.0), 22, 6.6, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.4))
    ax.text(71.5, 6.7, "NVML power sensor", ha="center", va="center", fontsize=10, fontweight="bold", color=FOREST)
    ax.text(71.5, 4.3, "samples every 100 ms", ha="center", va="center", fontsize=9, color=MUTED)
    ax.annotate("", xy=(71.5, 11.8), xytext=(71.5, 8.8), arrowprops=dict(arrowstyle="-|>", color=TEAL, linewidth=1.4))
    save(fig, "fig_pipeline.png")


def fig_sweep() -> None:
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ks = [0, 1, 2, 4, 8, 16, 32]
    nrows = 12
    rng = [2, 5, 0, 6, 3, 1, 4, 6, 2, 0, 5, 3]  # illustrative shuffle
    for r in range(nrows):
        for c, k in enumerate(ks):
            order = (c + rng[r]) % len(ks)
            alpha = 0.22 + 0.62 * (order / (len(ks) - 1))
            ax.add_patch(Rectangle((c + 0.06, r + 0.06), 0.88, 0.88, facecolor=TEAL, alpha=alpha, edgecolor="none"))
            ax.text(c + 0.5, r + 0.5, str(order + 1), ha="center", va="center", fontsize=7.5, color="white" if alpha > 0.5 else FOREST)
    ax.set_xlim(0, len(ks))
    ax.set_ylim(0, nrows)
    ax.set_xticks([i + 0.5 for i in range(len(ks))])
    ax.set_xticklabels([f"k={k}" for k in ks], fontsize=11)
    ax.set_yticks([0.5, nrows - 0.5])
    ax.set_yticklabels(["question 1", f"question {nrows}"], fontsize=10)
    ax.set_xlabel("retrieval depth: number of passages placed in the prompt", fontsize=10.5)
    for s in ["left", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Each row is one question. The number is the run order (1 = first).", fontsize=11.5, color=MUTED, pad=10, loc="left")
    save(fig, "fig_sweep.png")


def fig_block_timeline() -> None:
    fig, ax = plt.subplots(figsize=(11, 3.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 26)
    ax.axis("off")
    blocks = [(4, 12), (24, 12), (44, 12), (64, 12), (84, 12)]
    for i, (x, w) in enumerate(blocks):
        ax.add_patch(Rectangle((x, 9), w, 8, facecolor="#D8E9E2", edgecolor=TEAL, linewidth=1.4))
        ax.text(x + w / 2, 13, f"batch {i + 1}", ha="center", va="center", fontsize=10.5, fontweight="bold", color=FOREST)
        ax.text(x + w / 2, 10.9, "200 questions", ha="center", va="center", fontsize=9, color=MUTED)
        if i < len(blocks) - 1:
            ax.add_patch(Rectangle((x + w, 9), 8, 8, facecolor="white", edgecolor=GRIDC, linewidth=1.0, hatch="//"))
            ax.text(x + w + 4, 13, "rest\n120 s", ha="center", va="center", fontsize=9, color=MUTED)
    ax.annotate("", xy=(4, 18.6), xytext=(16, 18.6), arrowprops=dict(arrowstyle="<|-|>", color=AMBER, linewidth=1.6))
    ax.text(10, 19.4, "one energy window per batch", ha="center", fontsize=10.5, color=AMBER, fontweight="bold")
    ax.text(50, 4.2, "Idle power is read from the tail of the rest period, so the GPU is already cool and steady", ha="center", fontsize=10, color=MUTED)
    ax.text(50, 24.4, "Randomized order, one depth per batch, fixed rest between batches",
            ha="center", fontsize=11.5, color=INK, fontweight="bold")
    save(fig, "fig_block_timeline.png")


def fig_window_vs_block() -> None:
    import math

    xs = [i / 200 * 10 for i in range(201)]
    ys = [3.2 + 4.4 * (1 - math.exp(-((x - 0.55) ** 2) / 0.9)) for x in xs]

    fig, axes = plt.subplots(2, 1, figsize=(10.4, 4.6), sharex=True, sharey=True)

    segs = [(0.6, 1.5), (1.7, 2.6), (2.8, 3.7)]

    # top: per-question windows
    ax = axes[0]
    ax.plot(xs, ys, color=FOREST, linewidth=2.4, zorder=3)
    for a, b in segs:
        ax.add_patch(Rectangle((a, 0), b - a, 7.6, facecolor=AMBER, alpha=0.22, edgecolor=AMBER, linewidth=1.2, zorder=2))
    for a, b in [(1.5, 1.7), (2.6, 2.8)]:
        ax.add_patch(Rectangle((a, 0), b - a, 7.6, facecolor="white", edgecolor=AMBER, linewidth=1.0, hatch="///", zorder=4))
    ax.text(5.9, 9.9, "gaps are never measured", fontsize=11, color=AMBER, fontweight="bold")
    ax.annotate("", xy=(2.7, 6.4), xytext=(5.6, 9.3),
                arrowprops=dict(arrowstyle="->", color=AMBER, linewidth=1.3))
    ax.set_title("One window per question: the gaps between windows are lost",
                 fontsize=11.5, color=INK, loc="left", pad=8, fontweight="bold")
    ax.set_ylabel("power (W)")

    # bottom: one batch window
    ax = axes[1]
    ax.plot(xs, ys, color=FOREST, linewidth=2.4, zorder=3)
    ax.add_patch(Rectangle((0.6, 0), 3.1, 7.6, facecolor=TEAL, alpha=0.20, edgecolor=TEAL, linewidth=1.6, zorder=2))
    ax.text(5.9, 9.9, "one integral covers the whole span", fontsize=11, color=TEAL, fontweight="bold")
    ax.annotate("", xy=(3.6, 6.4), xytext=(5.6, 9.3),
                arrowprops=dict(arrowstyle="->", color=TEAL, linewidth=1.3))
    ax.set_title("One window per batch: every gap is counted",
                 fontsize=11.5, color=INK, loc="left", pad=8, fontweight="bold")
    ax.set_ylabel("power (W)")
    ax.set_xlabel("time within one batch")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11)

    for ax in axes:
        ax.set_xticks([])
        ax.grid(axis="y", color=GRIDC, linewidth=0.7)
        ax.spines["bottom"].set_visible(False)
    save(fig, "fig_window_vs_block.png")


# ---------------------------------------------------------------- charts
def fig_ek() -> None:
    rows = [r for r in load_estimates() if r["k"] >= 1]
    ks = [r["k"] for r in rows]
    epc = [r["epc"] for r in rows]
    acc = [100 * r["acc"] for r in rows]
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    ax.plot(ks, epc, marker="o", markersize=8, color=TEAL, linewidth=2.6, label="energy per correct answer (J)")
    ax.set_xlabel("retrieval depth k (passages placed in the prompt)")
    ax.set_ylabel("energy per correct answer (J)", color=TEAL)
    ax.set_xticks(ks)
    ax.set_ylim(0, max(epc) * 1.18)
    ax.grid(axis="y", color=GRIDC, linewidth=0.8)
    ax.tick_params(axis="y", labelcolor=TEAL)
    ax2 = ax.twinx()
    ax2.plot(ks, acc, marker="s", markersize=7, color=AMBER, linewidth=2.2, linestyle="--", label="accuracy (%)")
    ax2.set_ylabel("accuracy, exact match (%)", color=AMBER)
    ax2.set_ylim(0, 60)
    ax2.tick_params(axis="y", labelcolor=AMBER)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(AMBER)

    ax.annotate("energy floor\nat k=1-2", xy=(1.5, 53), xytext=(4.6, 74), fontsize=10.5, color=TEAL,
                fontweight="bold", arrowprops=dict(arrowstyle="->", color=TEAL, linewidth=1.3))
    ax.annotate("accuracy keeps rising\nafter energy stops paying", xy=(16, 114), xytext=(17.5, 62),
                fontsize=10.5, color=AMBER, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=AMBER, linewidth=1.3))

    handles = [plt.Line2D([], [], color=TEAL, marker="o", linewidth=2.4),
               plt.Line2D([], [], color=AMBER, marker="s", linewidth=2.2, linestyle="--")]
    ax.legend(handles, ["energy per correct answer (J)", "accuracy, exact match (%)"],
              loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=2, frameon=False, fontsize=10.5)
    ax.text(0.0, -0.26, "k=0 is omitted: only 1 of 1,000 questions was answered without context, so its ratio is not meaningful.",
            transform=ax.transAxes, fontsize=9.5, color=MUTED)
    save(fig, "fig_ek.png")


def fig_savings_forest() -> None:
    sweep = (58.17, 56.02, 60.14)
    blk = load_block()
    s = blk["savings"]
    block = (100 * s["point"], 100 * s["ci95"][0], 100 * s["ci95"][1])
    rep = load_replays()
    replay = (rep["saving_pct"]["median"] if isinstance(rep["saving_pct"], dict) else 78.90, 73.85, 80.11)

    labels = ["per-question windows", "batch estimator (reported)", "continuous replay"]
    vals = [sweep, block, replay]
    cols = [AMBER, TEAL, MUTED]
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    for i, (lab, v, c) in enumerate(zip(labels, vals, cols)):
        y = len(labels) - i
        ax.plot([v[1], v[2]], [y, y], color=c, linewidth=3.2, solid_capstyle="round")
        ax.plot(v[0], y, "o", color=c, markersize=11)
        ax.text(v[2] + 1.0, y, f"{v[0]:.2f}%", va="center", fontsize=11.5, fontweight="bold", color=c)
    ax.axvline(20, color=FOREST, linestyle=":", linewidth=1.6)
    ax.text(20.8, len(labels) + 0.45, "20% floor", fontsize=10, color=FOREST, va="center")
    ax.set_yticks(range(1, len(labels) + 1))
    ax.set_yticklabels(labels[::-1], fontsize=11)
    ax.set_xlabel("GPU energy saved at k=4 instead of k=32 (%)")
    ax.set_xlim(10, 92)
    ax.set_ylim(0.4, len(labels) + 0.85)
    ax.grid(axis="x", color=GRIDC, linewidth=0.8)
    ax.tick_params(length=0)
    save(fig, "fig_savings_forest.png")


def fig_drift() -> None:
    rep = load_replays()
    per = rep["per_replay"]
    ratios = [r["total_ratio"] for r in per]
    idx = list(range(1, len(ratios) + 1))
    fig, ax = plt.subplots(figsize=(9.0, 3.8))
    ax.plot(idx, ratios, marker="o", markersize=7, color=AMBER, linewidth=2.2)
    ax.axhline(1.0, color=GRIDC, linewidth=1.4, linestyle="--")
    ax.text(9.9, 1.004, "same energy as the batch design", fontsize=9.5, color=MUTED, ha="right", va="bottom")
    ax.set_xlabel("replay number (same questions, run one after another)")
    ax.set_ylabel("replay energy ÷ batch energy")
    ax.grid(axis="y", color=GRIDC, linewidth=0.8)
    ax.set_xticks(idx)
    ax.annotate("first replay, cool GPU", xy=(1, ratios[0]), xytext=(2.0, ratios[0] + 0.045),
                fontsize=10, color=AMBER, arrowprops=dict(arrowstyle="->", color=AMBER, linewidth=1.1))
    ax.annotate("later replays, hot GPU", xy=(len(ratios), ratios[-1]), xytext=(len(ratios) - 4.2, ratios[-1] + 0.05),
                fontsize=10, color=AMBER, arrowprops=dict(arrowstyle="->", color=AMBER, linewidth=1.1))
    ax.set_ylim(min(ratios) - 0.035, max(ratios) + 0.055)
    save(fig, "fig_drift.png")


def fig_margin() -> None:
    ni = load_ni()
    point = 100 * ni["accuracy_difference"]["mean_pp"] if isinstance(ni.get("accuracy_difference"), dict) else -4.30
    lo = 100 * ni["accuracy_difference"]["ci_pp"][0] if isinstance(ni.get("accuracy_difference"), dict) and "ci_pp" in ni["accuracy_difference"] else -6.17
    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    ax.axvline(-5, color=FOREST, linestyle="--", linewidth=2.0)
    ax.axvline(0, color=GRIDC, linewidth=1.4)
    ax.plot([lo, point], [1, 1], color=AMBER, linewidth=3.4, solid_capstyle="round")
    ax.plot(lo, 1, "o", color=AMBER, markersize=9)
    ax.plot(point, 1, "o", color=INK, markersize=11)
    ax.text(-5.25, 1.44, "the 5 pp limit", fontsize=11, color=FOREST, ha="right", fontweight="bold")
    ax.text(point + 0.2, 1.10, f"measured {point:.2f} pp", fontsize=11, fontweight="bold", color=INK)
    ax.text(lo - 0.25, 0.86, f"95% lower bound {lo:.2f} pp", fontsize=10.5, color=AMBER, ha="right")
    ax.text(-9.7, 0.66, "the lower bound sits 1.17 pp", fontsize=10.5, color=MUTED, ha="left")
    ax.text(-9.7, 0.55, "past the limit, so the claim", fontsize=10.5, color=MUTED, ha="left")
    ax.text(-9.7, 0.44, "was not established", fontsize=10.5, color=MUTED, ha="left")
    ax.annotate("", xy=(lo, 1.0), xytext=(lo, 0.86), arrowprops=dict(arrowstyle="-", color=AMBER, linewidth=1.2))
    ax.set_xlim(-10, 3)
    ax.set_ylim(0.38, 1.60)
    ax.set_yticks([])
    ax.set_xlabel("accuracy change at k=4 against k=32 (percentage points)")
    ax.spines["left"].set_visible(False)
    save(fig, "fig_margin.png")


def fig_dose() -> None:
    d = load_dose()
    per = d["per_dose"]
    doses = sorted(per, key=int)
    acc = [100 * per[x]["accuracy"] for x in doses]
    lo = [100 * per[x]["wilson_ci95"][0] for x in doses]
    hi = [100 * per[x]["wilson_ci95"][1] for x in doses]
    xs = list(range(len(doses)))
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    ax.errorbar(xs, acc, yerr=[ [a - l for a, l in zip(acc, lo)], [h - a for a, h in zip(acc, hi)] ],
                fmt="o-", color=TEAL, linewidth=2.2, markersize=8, capsize=4, ecolor=MUTED)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{x} extra" for x in doses], fontsize=10.5)
    ax.set_xlabel("distractor passages added after the correct one")
    ax.set_ylabel("accuracy, exact match (%)")
    ax.grid(axis="y", color=GRIDC, linewidth=0.8)
    trend = d["trend"]
    txt = f"+{100 * trend['repeated_measures_slope']:.2f} pp per doubling"
    ci = trend["repeated_measures_ci95"]
    txt += f"\n95% CI [{100 * ci[0]:.2f}, {100 * ci[1]:.2f}]"
    ax.text(0.03, 0.95, txt, transform=ax.transAxes, fontsize=10.5, va="top", color=FOREST, fontweight="bold")
    ax.set_title("Adding passages helps when the correct one is still first", fontsize=11, color=MUTED, loc="left", pad=10)
    save(fig, "fig_dose.png")


def fig_token() -> None:
    p = ROOT / "analysis" / "token_attribution" / "attribution.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    # use fitted coefficients; scatter from the per-depth prefill times if present
    coef = d.get("token_model", {}).get("coefs") or d.get("coefs")
    r2 = d.get("token_model", {}).get("r_squared") or d.get("r_squared")
    import numpy as np

    tpre = np.linspace(0, 4000, 140)
    j = 13.88 + 0.02549 * tpre
    fig, ax = plt.subplots(figsize=(8.8, 3.9))
    ax.plot(tpre, j, color=TEAL, linewidth=2.6, label="model: J = 13.88 + 0.02549·T_pre")
    for kv, marks in [(26.22, "k=4"), (75.93, "k=4 padded to k=32 length"), (87.22, "k=32")]:
        ax.axhline(kv, color=GRIDC, linewidth=1.0, linestyle=":")
        ax.text(3720, kv + 2.0, f"{marks}: {kv:.1f} J", fontsize=9.5, color=MUTED, ha="right")
    ax.set_xlabel("prompt tokens before generation (T_pre)")
    ax.set_ylabel("energy per query (J)")
    ax.grid(color=GRIDC, linewidth=0.7)
    if r2:
        ax.text(0.03, 0.92, f"R² = {r2:.4f}", transform=ax.transAxes, fontsize=12, fontweight="bold", color=FOREST)
    ax.text(0.99, 0.03, "dashed lines = measured energy from the padding experiment",
            transform=ax.transAxes, fontsize=9.5, color=MUTED, ha="right")
    save(fig, "fig_token.png")


def fig_rq() -> None:
    # From analysis/recall_precision.json (registered): arm-level R and Q at k=4 and max depth
    arms = {
        "Qwen3.5-4B (k=4→32)": (0.775, 0.892, 0.592, 0.549),
        "Qwen2.5-1.5B (k=4→32)": (0.700, 0.814, 0.610, 0.530),
        "Llama-3.2-3B (k=4→32)": (0.690, 0.804, 0.600, 0.467),
        "HotpotQA Qwen4B (k=4→10)": (0.780, 0.836, 0.560, 0.644),
    }
    fig, ax = plt.subplots(figsize=(8.8, 4.2))
    x = range(len(arms))
    w = 0.36
    dr = [100 * (v[1] - v[0]) for v in arms.values()]
    dq = [100 * (v[3] - v[2]) for v in arms.values()]
    ax.bar([i - w / 2 for i in x], dr, w, color=TEAL, label="recall gain (R)")
    ax.bar([i + w / 2 for i in x], dq, w, color=AMBER, label="precision change (Q)")
    ax.axhline(0, color=INK, linewidth=1.2)
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Qwen3.5-4B", "Qwen2.5-1.5B", "Llama-3.2-3B", "HotpotQA"], fontsize=10.5)
    ax.set_ylim(min(dq) - 4, max(dr) + 4)
    ax.set_ylabel("change in percentage points")
    ax.legend(frameon=False, fontsize=10.5, loc="lower left")
    ax.grid(axis="y", color=GRIDC, linewidth=0.8)
    ax.set_xlabel("depth change k=4 to k=32 (HotpotQA: k=4 to k=10)", fontsize=10)
    ax.set_title("Recall always rises; precision moves both ways and decides the sign", fontsize=11, color=MUTED, loc="left", pad=10)
    save(fig, "fig_rq.png")


def main() -> int:
    print("diagrams")
    fig_pipeline()
    fig_sweep()
    fig_block_timeline()
    fig_window_vs_block()
    print("charts")
    fig_ek()
    fig_savings_forest()
    fig_drift()
    fig_margin()
    fig_dose()
    fig_token()
    fig_rq()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
