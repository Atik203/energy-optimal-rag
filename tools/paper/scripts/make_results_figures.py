"""Results figures from registered analysis outputs (no new experiments).

Outputs (``paper/figures``):

* ``p1_contrasts.png`` -- forest plot of the P1 primary contrast with the 5 pp
  margin plus the two P2 replication contrasts, and the bootstrap selection
  probabilities P(k*).
* ``rq_curves.png`` -- recall R(k) and conditional precision Q(k) curves for
  the four reader/task arms.

Every number is read from a registered analysis output; missing inputs stop
the run with a clear error. Run from the repository root::

    python tools/paper/scripts/make_results_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = ROOT / "paper" / "figures"
P1_DIR = ROOT / "analysis" / "squad_qwen4b_p1"
QWEN_DIR = ROOT / "analysis" / "squad_qwen15b_p2"
HOT_DIR = ROOT / "analysis" / "hotpot_qwen4b_p2"
RQ_PATH = ROOT / "analysis" / "recall_precision.json"

DPI = 650
BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREEN = "#009E73"
ORANGE = "#E69F00"
GRAY = "#6E6E6E"
INK = "#1A1A1A"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"missing or invalid registered output: {path}") from exc


def _despine(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def figure_contrasts() -> None:
    """Forest plot of the three accuracy contrasts plus selection bars."""
    p1_ni = _read_json(P1_DIR / "noninferiority.json")
    p1_boot = _read_json(P1_DIR / "bootstrap.json")
    qwen = _read_json(QWEN_DIR / "direction.json")
    hot = _read_json(HOT_DIR / "direction.json")

    primary = p1_ni["primary"]
    p1_point = float(primary["mean_diff"]) * 100.0
    p1_se = float(primary["se"]) * 100.0
    p1_lower_onesided = float(primary["lower_bound"]) * 100.0
    p1_two = (p1_point - 1.96 * p1_se, p1_point + 1.96 * p1_se)

    q_point = float(qwen["mean_diff"]) * 100.0
    q_se = float(qwen["se"]) * 100.0
    q_upper = float(qwen["one_sided_upper_zero"]) * 100.0
    q_two = (q_point - 1.96 * q_se, q_point + 1.96 * q_se)

    h_point = float(hot["mean_diff"]) * 100.0
    h_se = float(hot["se"]) * 100.0
    h_upper = float(hot["one_sided_upper_zero"]) * 100.0
    h_two = (h_point - 1.96 * h_se, h_point + 1.96 * h_se)

    p_opt = p1_boot["p_k_optimal"]
    depths = [0, 1, 2, 4, 8, 16, 32]
    probs = [float(p_opt.get(str(k), 0.0)) for k in depths]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(8.2, 3.5))
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.20, top=0.86, wspace=0.35)

    # Panel (a): forest plot, all in percentage points.
    rows = [
        ("P1 ($n=1{,}000$)", p1_point, p1_two, p1_lower_onesided, None, -0.36, 0.14),
        ("Qwen1.5B ($n=500$)", q_point, q_two, None, q_upper, -0.30, 0.24),
        ("HotpotQA ($n=500$)", h_point, h_two, None, h_upper, -0.36, 0.16),
    ]
    ys = np.arange(len(rows))[::-1]
    for y, (_label, point, two, lower, upper, dy_point, dy_bound) in zip(ys, rows, strict=True):
        ax_a.errorbar(
            [point],
            [y],
            xerr=np.array([[point - two[0]], [two[1] - point]]),
            fmt="o",
            color=BLUE,
            ecolor=BLUE,
            elinewidth=1.6,
            capsize=4,
            capthick=1.4,
            markersize=6,
            zorder=3,
        )
        if lower is not None:
            ax_a.annotate(
                "",
                xy=(lower, y),
                xytext=(point, y),
                arrowprops={"arrowstyle": "-|>", "color": VERMILLION, "linewidth": 1.4},
            )
            ax_a.text(
                lower - 0.25,
                y + 0.04,
                f"{lower:.2f}",
                ha="right",
                va="center",
                fontsize=7.5,
                color=VERMILLION,
            )
        if upper is not None:
            ax_a.annotate(
                "",
                xy=(upper, y),
                xytext=(point, y),
                arrowprops={"arrowstyle": "-|>", "color": VERMILLION, "linewidth": 1.4},
            )
            ax_a.text(
                upper,
                y + dy_bound,
                f"{upper:+.2f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=VERMILLION,
            )
        ax_a.text(
            point, y + dy_point, f"{point:+.2f} pp", ha="center", va="top", fontsize=7.5, color=INK
        )
    ax_a.set_yticks(list(ys))
    ax_a.set_yticklabels([r[0] for r in rows], fontsize=8.0)
    ax_a.tick_params(axis="y", pad=2)
    ax_a.axvline(-5, color=VERMILLION, linewidth=1.2, linestyle="--", label="5 pp margin")
    ax_a.axvline(0, color=GRAY, linewidth=0.9, linestyle=":", label="no difference")
    ax_a.set_xlabel("paired accuracy difference (pp)", fontsize=9.5)
    ax_a.set_title("(a) Accuracy contrasts with bounds", fontsize=10.5, pad=6)
    ax_a.set_xlim(-16.5, 8)
    ax_a.set_ylim(-0.9, 2.9)
    ax_a.legend(fontsize=7.5, loc="lower right")
    ax_a.grid(axis="x", alpha=0.35)
    ax_a.set_axisbelow(True)
    _despine(ax_a)

    # Panel (b): bootstrap selection probabilities.
    colors = [VERMILLION if k == 4 else BLUE for k in depths]
    ax_b.bar(
        [str(k) for k in depths], probs, color=colors, edgecolor="white", linewidth=0.8, zorder=3
    )
    ax_b.axhline(0.8, color=GRAY, linewidth=1.0, linestyle="--")
    ax_b.text(6.4, 0.81, "0.8 gate", ha="right", va="bottom", fontsize=7.5, color=GRAY)
    for k, pr in zip(depths, probs, strict=True):
        if pr > 0.01:
            ax_b.text(
                str(k), pr + 0.015, f"{pr:.3f}", ha="center", va="bottom", fontsize=7.5, color=INK
            )
    ax_b.set_xlabel("depth $k$", fontsize=9.5)
    ax_b.set_ylabel("$P(k^{*}$ optimal$)$", fontsize=9.5)
    ax_b.set_title("(b) Selection probability $P(k^{*})$", fontsize=10.5, pad=6)
    ax_b.set_ylim(0, 1.0)
    ax_b.grid(axis="y", alpha=0.35)
    ax_b.set_axisbelow(True)
    _despine(ax_b)

    fig.text(
        0.5,
        0.015,
        "Sources: registered P1/P2 analyses. Whiskers: two-sided 95% CI; arrows: one-sided 95% bounds.",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=GRAY,
    )
    path = FIG_DIR / "p1_contrasts.png"
    fig.savefig(path, dpi=DPI, facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def figure_rq() -> None:
    """Recall and conditional-precision curves for the four arms."""
    rq = _read_json(RQ_PATH)
    arms = [
        ("squad_qwen4b_p1", "P1 Qwen4B", BLUE),
        ("squad_qwen15b_p2", "Qwen1.5B", VERMILLION),
        ("squad_llama3b_p2", "Llama 3B", GREEN),
        ("hotpot_qwen4b_p2", "HotpotQA", ORANGE),
    ]
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.5, 3.6), sharex=True)
    fig.tight_layout(rect=(0.0, 0.12, 1.0, 0.92), w_pad=2.0)
    for key, label, color in arms:
        entry = rq[key]
        ks = np.array(entry["depths"], dtype=float)
        r = np.array([entry["recall"][str(int(k))] for k in ks], dtype=float)
        q = np.array([entry["precision"][str(int(k))] for k in ks], dtype=float)
        ax_a.plot(ks, r, "o-", color=color, markersize=4.5, linewidth=1.6, label=label)
        ax_b.plot(ks, q, "o-", color=color, markersize=4.5, linewidth=1.6, label=label)
    for ax, title, ylabel in (
        (ax_a, "(a) Recall $R(k)$ rises with depth", "recall (proportion)"),
        (ax_b, "(b) Precision $Q(k)$ falls except on HotpotQA", "precision (proportion)"),
    ):
        ax.set_xscale("symlog", linthresh=1)
        ax.set_xlim(-0.2, 40)
        ax.set_xticks([0, 1, 2, 4, 8, 16, 32])
        ax.set_xticklabels(["0", "1", "2", "4", "8", "16", "32"])
        ax.set_xlabel("depth $k$", fontsize=9.5)
        ax.set_ylabel(ylabel, fontsize=9.5)
        ax.set_title(title, fontsize=11.5, pad=6)
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.35)
        ax.set_axisbelow(True)
        _despine(ax)
    ax_b.legend(fontsize=7.5, loc="upper left")
    fig.text(
        0.5,
        0.015,
        "Sources: recall-precision analysis (registered). $A(k)=R(k)Q(k)$; the plateau is a precision decline.",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=GRAY,
    )
    path = FIG_DIR / "rq_curves.png"
    fig.savefig(path, dpi=DPI, facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> int:
    figure_contrasts()
    figure_rq()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
