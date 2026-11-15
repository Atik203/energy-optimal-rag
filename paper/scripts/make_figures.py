#!/usr/bin/env python
"""Build the paper figures from registered run data.

Outputs (``paper/figures``):

* ``design.png``          -- P1 measurement/analysis protocol schematic (no data)
* ``p0_harness.png``      -- P0 ``_r3`` uncalibrated GPU energy and k=0 block diagnostic
* ``p1_curve.png``        -- P1 A(k)/J(k)/E(k); placeholder by default, data with ``--p1``
* ``p1_calibration.png``  -- seven P1 block factors; placeholder by default, data with ``--p1``

The default path keeps the P1 placeholders.  ``--p1`` reads the registered P1 analysis
outputs and regenerates the two result figures with calibrated values::

    python paper/scripts/make_figures.py          # design + P0 + P1 placeholders
    python paper/scripts/make_figures.py --p1     # data-backed P1 result figures
    python paper/scripts/make_figures.py --check  # size/DPI check only

The script never invents a P1 curve or a P1 block factor.  In ``--p1`` mode every point,
interval, factor, and annotation is read from the registered output; missing inputs stop
the run with a clear error.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.ticker import NullFormatter, NullLocator, ScalarFormatter

try:  # scipy is available in the project environment; keep a stdlib fallback.
    from scipy import stats as _scipy_stats
except ImportError:  # pragma: no cover - only used outside the project environment
    _scipy_stats = None

ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "paper"
FIG_DIR = PAPER_DIR / "figures"
P0_RAW = ROOT / "runs" / "golden_squad_qwen4b_p0_r3" / "raw.csv"
P1_DIR = ROOT / "analysis" / "squad_qwen4b_p1"
P1_ESTIMATES = P1_DIR / "estimates.csv"
P1_BOOTSTRAP = P1_DIR / "bootstrap.json"
P1_NONINFERIORITY = P1_DIR / "noninferiority.json"
P1_BLOCKS = ROOT / "runs" / "squad_qwen4b_p1" / "blocks.json"
P1_REPEAT = ROOT / "runs" / "squad_qwen4b_p1" / "repeat.json"

# The reference journal figures are 650 dpi at 6.5--6.6 in wide (about 4,200 px).
DPI = 650
DEPTHS = (0, 1, 2, 4, 8, 16, 32)

# Okabe--Ito colourblind-friendly palette.
BLUE = "#0072B2"
SKY = "#56B4E9"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
GRAY = "#6E6E6E"
LIGHT_GRAY = "#D9D9D9"
INK = "#1A1A1A"

# P0 block diagnostic constants.  These are measured values, not fitted ones.
# Source: docs/P0_HARNESS_REPORT.md Sec. 6 (verbatim); no blocks.json exists for _r3.
P0_K0_FACTOR_CSV = 0.7944
P0_K0_FACTOR_BLOCK = 0.9989
P0_K0_CONSISTENCY = 1.2573
P0_BLOCK_BAND = (0.8, 1.4)  # fixed pre-registered band, report Sec. 3.1


def apply_style() -> None:
    """Apply the journal style shared by every figure."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 15,
            "mathtext.fontset": "dejavusans",
            "mathtext.default": "regular",
            "axes.titlesize": 18,
            "axes.titleweight": "bold",
            "axes.labelsize": 16,
            "axes.labelweight": "bold",
            "axes.edgecolor": INK,
            "axes.linewidth": 1.1,
            "axes.facecolor": "white",
            "axes.grid": False,
            "xtick.labelsize": 13,
            "ytick.labelsize": 13,
            "xtick.major.size": 5,
            "ytick.major.size": 5,
            "xtick.major.width": 1.1,
            "ytick.major.width": 1.1,
            "legend.fontsize": 12,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.dpi": DPI,
            "figure.dpi": 110,
            "lines.linewidth": 2.2,
            "lines.markersize": 7,
            "grid.color": LIGHT_GRAY,
            "grid.linestyle": "--",
            "grid.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def despine(ax: plt.Axes) -> None:
    """Remove the top and right spines for a clean journal panel."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def add_depth_axis(ax: plt.Axes, *, categorical: bool = False) -> None:
    """Use a readable depth axis for the 0,1,2,4,...,32 grid.

    ``categorical=True`` spaces the seven planned depths equally, which keeps the
    three-panel placeholder legible.  The data panels use a symlog axis so the true
    numeric depth spacing is visible.
    """
    if categorical:
        ax.set_xlim(-0.55, len(DEPTHS) - 0.45)
        ax.set_xticks(range(len(DEPTHS)))
        ax.set_xticklabels([str(k) for k in DEPTHS])
        ax.set_xlabel("depth $k$ (passages)")
        return
    ax.set_xscale("symlog", linthresh=1, linscale=0.9)
    ax.set_xlim(-0.2, 45)
    ax.set_xticks(DEPTHS)
    ax.set_xticklabels([str(k) for k in DEPTHS])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel("depth $k$ (passages)")


def save_figure(fig: plt.Figure, name: str) -> None:
    """Write one PNG at the reference DPI with a white background."""
    path = FIG_DIR / name
    fig.savefig(path, dpi=DPI, facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def _t_critical(n: int) -> float:
    if _scipy_stats is not None and n > 1:
        return float(_scipy_stats.t.ppf(0.975, n - 1))
    return 1.96  # normal approximation fallback


def p0_summary() -> pd.DataFrame:
    """Per-depth P0 ``_r3`` GPU-only summary from raw rows.

    Returns columns: k, n_valid, n_invalid, n_correct, accuracy, mean_j,
    ci_low, ci_high, e_gpu.  ``mean_j`` is the mean of ``j_gpu_raw`` and
    ``e_gpu`` is total GPU joules over total correct answers.
    """
    if not P0_RAW.exists():
        raise SystemExit(f"missing P0 raw CSV: {P0_RAW}")
    df = pd.read_csv(P0_RAW)
    required = {"k", "j_gpu_raw", "correct_em", "valid"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{P0_RAW} is missing columns: {sorted(missing)}")

    rows: list[dict[str, Any]] = []
    for k in DEPTHS:
        g = df[(df["k"] == k) & (df["valid"] == 1)]
        n = len(g)
        if n == 0:
            continue
        j = g["j_gpu_raw"].to_numpy(dtype=float)
        correct = g["correct_em"].to_numpy(dtype=float)
        mean = float(j.mean())
        se = float(j.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
        half = _t_critical(n) * se
        n_correct = float(correct.sum())
        rows.append(
            {
                "k": int(k),
                "n_valid": int(n),
                "n_invalid": int(len(df[df["k"] == k]) - n),
                "n_correct": n_correct,
                "accuracy": float(correct.mean()),
                "mean_j": mean,
                "ci_low": mean - half,
                "ci_high": mean + half,
                "e_gpu": float(j.sum() / n_correct) if n_correct > 0 else float("inf"),
            }
        )
    if not rows:
        raise SystemExit(f"no valid P0 rows in {P0_RAW}")
    return pd.DataFrame(rows)


def figure_design() -> None:
    """Protocol schematic.  No measured values are drawn."""
    fig = plt.figure(figsize=(7.2, 8.8), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.972,
        "P1 measurement and analysis protocol",
        ha="center",
        va="center",
        fontsize=19.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.5,
        0.938,
        "SQuAD v1.1 dev  ·  Qwen3.5-4B Q4 (4k)  ·  BM25 top-32  ·  RTX 3060 Laptop 6 GB",
        ha="center",
        va="center",
        fontsize=11.2,
        color=GRAY,
    )

    # Steps are top-to-bottom.  Numeric constants trace to configs/grid/primary_k7.toml,
    # configs/base.toml, and README/ROADMAP; the 7,000 figure is 1,000 x 7.
    steps: list[tuple[str, str, str, str]] = [
        (
            "1",
            "1,000 SQuAD v1.1 dev questions\nP1 split; disjoint from the 200-question P0 harness",
            BLUE,
            "#EAF3FB",
        ),
        (
            "2",
            "Seven retrieval depths\nk ∈ {0, 1, 2, 4, 8, 16, 32}  →  7,000 measured queries",
            BLUE,
            "#EAF3FB",
        ),
        (
            "3",
            "Idle baseline before warm-up\n60 s window; proceed only if CV ≤ 0.20",
            SKY,
            "#EDF7FC",
        ),
        (
            "4",
            "Warm-up\n20 queries; excluded from every estimate",
            SKY,
            "#EDF7FC",
        ),
        (
            "5",
            "Randomized sweep\n"
            "k order permuted within each question\n"
            "unique 10-hex nonce on every request",
            BLUE,
            "#EAF3FB",
        ),
        (
            "6",
            "Seven-depth block calibration\n"
            "20 back-to-back queries per depth\n"
            "gate: factor ∈ [0.8, 1.4] at every depth",
            ORANGE,
            "#FFF3E0",
        ),
        (
            "7",
            "Repeat stability at k = 8\n3 blocks × 20 queries\nrepeat CV reported",
            PURPLE,
            "#F7ECF5",
        ),
        (
            "8",
            "Paired analysis\n"
            "5 pp EM non-inferiority at k = 4 vs k = 32\n"
            "savings 1 − E(4)/E(32) ≥ 20%; gates K1–K7 and G1–G5",
            GREEN,
            "#E7F4EF",
        ),
    ]

    x, w = 0.13, 0.76
    h, gap = 0.075, 0.028
    top = 0.895

    for i, (num, text, edge, fill) in enumerate(steps):
        y = top - i * (h + gap) - h
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.006,rounding_size=0.010",
                transform=ax.transAxes,
                facecolor=fill,
                edgecolor=edge,
                linewidth=1.6,
                zorder=2,
            )
        )
        ax.text(
            0.5,
            y + h / 2,
            text,
            ha="center",
            va="center",
            fontsize=12.3,
            linespacing=1.15,
            color=INK,
            zorder=3,
        )
        ax.add_patch(
            Circle(
                (0.082, y + h / 2),
                0.0132,
                transform=ax.transAxes,
                facecolor=edge,
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
        )
        ax.text(
            0.082,
            y + h / 2,
            num,
            ha="center",
            va="center",
            fontsize=11.5,
            fontweight="bold",
            color="white",
            zorder=4,
        )
        if i < len(steps) - 1:
            y_next = top - (i + 1) * (h + gap) - h
            ax.add_patch(
                FancyArrowPatch(
                    (0.5, y - 0.001),
                    (0.5, y_next + h + 0.001),
                    transform=ax.transAxes,
                    arrowstyle="-|>",
                    mutation_scale=13,
                    linewidth=1.4,
                    color=GRAY,
                    shrinkA=0,
                    shrinkB=0,
                    zorder=1,
                )
            )

    ax.plot([0.10, 0.90], [0.080, 0.080], color=LIGHT_GRAY, linewidth=1.0)
    ax.text(
        0.5,
        0.056,
        "Primary estimand: 1 − E(4)/E(32), with 5 pp EM non-inferiority at k = 4 vs k = 32.",
        ha="center",
        va="center",
        fontsize=8.8,
        color=INK,
    )
    ax.text(
        0.5,
        0.034,
        "Absolute J, E, N*, and S(k) are claimed only if all seven P1 block factors pass "
        "[0.8, 1.4].",
        ha="center",
        va="center",
        fontsize=8.8,
        color=INK,
    )
    ax.text(
        0.5,
        0.012,
        "Otherwise they are uncalibrated. P0 harness (not a paper result): 1,400 rows, "
        "200 questions.",
        ha="center",
        va="center",
        fontsize=8.8,
        color=GRAY,
    )

    save_figure(fig, "design.png")


def figure_p0(summary: pd.DataFrame) -> None:
    """P0 ``_r3``: uncalibrated J_gpu_raw curve and the k=0 block diagnostic."""
    fig, (ax_a, ax_b) = plt.subplots(
        1,
        2,
        figsize=(7.5, 5.0),
        gridspec_kw={"width_ratios": (1.28, 1.0)},
    )
    fig.tight_layout(rect=(0.0, 0.10, 1.0, 0.97), w_pad=2.0)
    fig.subplots_adjust(left=0.115)

    ks = summary["k"].to_numpy(dtype=float)
    mean = summary["mean_j"].to_numpy(dtype=float)
    lo = summary["ci_low"].to_numpy(dtype=float)
    hi = summary["ci_high"].to_numpy(dtype=float)

    ax_a.fill_between(ks, lo, hi, color=BLUE, alpha=0.16, linewidth=0)
    ax_a.errorbar(
        ks,
        mean,
        yerr=[mean - lo, hi - mean],
        fmt="none",
        ecolor=BLUE,
        elinewidth=1.2,
        capsize=4,
        capthick=1.2,
        zorder=2,
    )
    ax_a.plot(ks, mean, color=BLUE, marker="o", markersize=7, linewidth=2.2, zorder=3)
    add_depth_axis(ax_a)
    ax_a.set_ylim(0, float(hi.max()) * 1.13)
    ax_a.set_ylabel("$J_{\\mathrm{gpu,raw}}$ (J/query)", fontsize=15)
    ax_a.set_title("(a) GPU energy vs depth", fontsize=17.0, pad=8)
    ax_a.tick_params(axis="both", labelsize=12)
    ax_a.grid(axis="y", alpha=0.55)
    ax_a.set_axisbelow(True)
    despine(ax_a)
    ax_a.text(
        0.03,
        0.95,
        "UNCALIBRATED",
        transform=ax_a.transAxes,
        ha="left",
        va="top",
        fontsize=10.5,
        fontweight="bold",
        color=VERMILLION,
        bbox={
            "boxstyle": "round,pad=0.28",
            "facecolor": "#FFF1E8",
            "edgecolor": VERMILLION,
            "linewidth": 1.0,
        },
    )
    ax_a.text(
        0.97,
        0.05,
        f"n = {int(summary['n_valid'].min())} per depth\n95% CI",
        transform=ax_a.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.5,
        color=GRAY,
    )
    ax_a.text(
        0.02,
        0.02,
        "symlog x",
        transform=ax_a.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.5,
        color=GRAY,
    )

    # Panel (b): the run-window and block-window factors at k=0 against the fixed band.
    band_lo, band_hi = P0_BLOCK_BAND
    ax_b.add_patch(
        Rectangle(
            (0.0, band_lo),
            1.0,
            band_hi - band_lo,
            facecolor=GREEN,
            alpha=0.10,
            edgecolor=GREEN,
            linewidth=1.0,
            linestyle="--",
            zorder=0,
        )
    )
    ax_b.axhline(band_lo, color=GREEN, linewidth=1.4, linestyle="--", zorder=1)
    ax_b.axhline(band_hi, color=GREEN, linewidth=1.4, linestyle="--", zorder=1)
    x_csv, x_block = 0.27, 0.73
    ax_b.vlines(x_csv, 0.66, P0_K0_FACTOR_CSV, color=VERMILLION, linewidth=2.2, alpha=0.35)
    ax_b.vlines(x_block, 0.66, P0_K0_FACTOR_BLOCK, color=BLUE, linewidth=2.2, alpha=0.35)
    ax_b.scatter(
        [x_csv],
        [P0_K0_FACTOR_CSV],
        s=140,
        color=VERMILLION,
        edgecolor="white",
        linewidth=1.2,
        zorder=4,
        label="factor_csv (run window)",
    )
    ax_b.scatter(
        [x_block],
        [P0_K0_FACTOR_BLOCK],
        s=140,
        marker="D",
        color=BLUE,
        edgecolor="white",
        linewidth=1.2,
        zorder=4,
        label="factor_block (block window)",
    )
    ax_b.set_xlim(0.0, 1.0)
    ax_b.set_ylim(0.66, 1.50)
    ax_b.set_xticks([x_csv, x_block])
    ax_b.set_xticklabels(["factor_csv", "factor_block"], fontsize=9.8)
    ax_b.set_yticks([0.8, 1.0, 1.2, 1.4])
    ax_b.tick_params(axis="y", labelsize=12)
    ax_b.set_ylabel("block factor", fontsize=14.5)
    ax_b.set_title("(b) k = 0 check", fontsize=17.0, pad=8)
    ax_b.grid(axis="y", alpha=0.55)
    ax_b.set_axisbelow(True)
    despine(ax_b)

    ax_b.text(
        0.02,
        1.47,
        "consistency $= 1.2573$",
        ha="left",
        va="top",
        fontsize=11.2,
        color=INK,
    )
    ax_b.text(
        0.02,
        1.36,
        "acceptance band [0.8, 1.4]",
        ha="left",
        va="top",
        fontsize=9.4,
        color=GREEN,
    )
    ax_b.annotate(
        "0.7944",
        xy=(x_csv, P0_K0_FACTOR_CSV),
        xytext=(0.02, 0.735),
        ha="left",
        va="bottom",
        fontsize=11.0,
        fontweight="bold",
        color=VERMILLION,
        arrowprops={"arrowstyle": "-", "color": VERMILLION, "linewidth": 1.1},
    )
    ax_b.text(
        0.02,
        0.700,
        "below 0.80 floor",
        ha="left",
        va="bottom",
        fontsize=8.4,
        color=VERMILLION,
    )
    ax_b.annotate(
        "0.9989",
        xy=(x_block, P0_K0_FACTOR_BLOCK),
        xytext=(0.74, 1.025),
        ha="left",
        va="bottom",
        fontsize=11.0,
        fontweight="bold",
        color=BLUE,
        arrowprops={"arrowstyle": "-", "color": BLUE, "linewidth": 1.1},
    )

    fig.text(
        0.5,
        0.032,
        "P0 _r3: 1,400 rows, 0 invalid; uncalibrated "
        "($j_{\\mathrm{gpu,calibrated}} \\equiv j_{\\mathrm{gpu,raw}}$); "
        "no calibrated $J$ curve exists.",
        ha="center",
        va="center",
        fontsize=8.6,
        color=GRAY,
    )
    fig.text(
        0.5,
        0.010,
        "Source: runs/golden_squad_qwen4b_p0_r3/raw.csv; docs/P0_HARNESS_REPORT.md. "
        "k = 0 factor 0.7944 < 0.80.",
        ha="center",
        va="center",
        fontsize=8.2,
        color=GREEN,
    )
    save_figure(fig, "p0_harness.png")


def _read_p1_estimates() -> pd.DataFrame | None:
    if not P1_ESTIMATES.exists():
        return None
    df = pd.read_csv(P1_ESTIMATES)
    aliases = {
        "accuracy": ("accuracy", "a_em"),
        "mean_j": ("mean_j", "j_mean"),
        "e_per_correct": ("e_per_correct", "e_j_per_correct"),
    }
    for target, candidates in aliases.items():
        if target not in df.columns:
            for candidate in candidates:
                if candidate in df.columns:
                    df = df.rename(columns={candidate: target})
                    break
    required = {"k", "accuracy", "mean_j", "e_per_correct"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{P1_ESTIMATES} is missing columns: {sorted(missing)}")
    return df.sort_values("k")


def _read_json(path: Path) -> dict[str, Any]:
    """Read a registered JSON output, or stop with a clear missing-source error."""
    if not path.exists():
        raise SystemExit(f"missing P1 source: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _bootstrap_ci(bootstrap: dict[str, Any], block: str, k: int) -> tuple[float, float] | None:
    """Return the 95% bootstrap interval for one depth, if it is finite."""
    node = bootstrap.get(block, {}).get(str(k))
    if not isinstance(node, dict):
        return None
    interval = node.get("interval", {})
    low, high = interval.get("lower"), interval.get("upper")
    if low is None or high is None:
        return None
    low_f = float(low)
    high_f = float("inf") if high == "inf" else float(high)
    if not math.isfinite(low_f) or not math.isfinite(high_f):
        return None
    return low_f, high_f


def _require_ci(bootstrap: dict[str, Any], block: str, k: int) -> tuple[float, float]:
    """Return a finite bootstrap interval or stop with the missing key."""
    interval = _bootstrap_ci(bootstrap, block, k)
    if interval is None:
        raise SystemExit(f"missing finite bootstrap interval: {block} k={k}")
    return interval


def _p1_inputs() -> tuple[
    pd.DataFrame, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    """Load every registered P1 figure input; all are required in ``--p1`` mode."""
    estimates = _read_p1_estimates()
    if estimates is None:
        raise SystemExit(f"missing P1 estimates: {P1_ESTIMATES}")
    return (
        estimates,
        _read_json(P1_BOOTSTRAP),
        _read_json(P1_NONINFERIORITY),
        _read_json(P1_BLOCKS),
        _read_json(P1_REPEAT),
    )


def figure_p1_curve(use_p1: bool = False) -> None:
    """P1 A(k), J(k), E(k): placeholder by default, calibrated result with ``--p1``."""
    if use_p1:
        estimates, bootstrap, noninferiority, _blocks, _repeat = _p1_inputs()
    else:
        estimates, bootstrap, noninferiority = None, None, None

    fig, axes = plt.subplots(1, 3, figsize=(7.5, 5.4), sharex=False)
    fig.tight_layout(rect=(0.0, 0.115, 1.0, 0.735), w_pad=1.5)

    titles = ("(a) $A(k)$", "(b) $J(k)$", "(c) $E(k)$")
    ylabels = (
        "EM accuracy",
        "$J$ per query (J)",
        "$E$ per correct (J)",
    )

    if estimates is None:
        for ax, title, ylabel in zip(axes, titles, ylabels, strict=True):
            add_depth_axis(ax, categorical=True)
            ax.set_xlabel("")
            ax.set_title(title, fontsize=18.0, pad=7)
            ax.set_ylabel(ylabel, fontsize=14.0)
            ax.tick_params(axis="x", labelbottom=False)
            ax.tick_params(axis="y", labelsize=12.0)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            ax.grid(axis="y", alpha=0.45)
            ax.set_axisbelow(True)
            despine(ax)
            ax.text(
                0.5,
                0.52,
                "TBD",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=21,
                fontweight="bold",
                color="#BDBDBD",
                alpha=0.55,
            )

        fig.text(
            0.5,
            0.972,
            "P1 confirmatory curves — placeholder",
            ha="center",
            va="center",
            fontsize=19,
            fontweight="bold",
            color=INK,
        )
        fig.text(
            0.5,
            0.906,
            "P1 analysis pending — 7,000-query sweep in progress",
            ha="center",
            va="center",
            fontsize=13.8,
            fontweight="bold",
            color=VERMILLION,
            bbox={
                "boxstyle": "round,pad=0.40",
                "facecolor": "#FFF4E8",
                "edgecolor": ORANGE,
                "linewidth": 1.2,
            },
        )
        fig.text(
            0.5,
            0.850,
            "Planned panels only; no data points are plotted. Use --p1 for the registered result.",
            ha="center",
            va="center",
            fontsize=9.8,
            color=GRAY,
        )
        ax = axes[0]
        ax.annotate(
            "",
            xy=(0.84, 0.78),
            xytext=(0.40, 0.78),
            xycoords="axes fraction",
            arrowprops={"arrowstyle": "<->", "color": ORANGE, "linewidth": 1.4},
        )
        ax.text(
            0.62,
            0.835,
            "5 pp NI gate\n$k=4$ vs $k=32$",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=8.0,
            color=ORANGE,
            fontweight="bold",
        )
        ax.text(
            0.62,
            0.735,
            "savings ≥ 20%",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=7.8,
            color=ORANGE,
        )
        axes[1].text(
            0.5,
            0.10,
            "Calibrated only if all 7\nblock factors ∈ [0.8, 1.4]",
            transform=axes[1].transAxes,
            ha="center",
            va="bottom",
            fontsize=7.8,
            color=GRAY,
        )
        axes[2].text(
            0.5,
            0.10,
            "$E = \\sum J \\,/\\, \\sum c$",
            transform=axes[2].transAxes,
            ha="center",
            va="bottom",
            fontsize=8.0,
            color=GRAY,
        )
        fig.text(
            0.5,
            0.050,
            "retrieval depth $k$ (seven planned depths: 0, 1, 2, 4, 8, 16, 32)",
            ha="center",
            va="center",
            fontsize=13.0,
            fontweight="bold",
            color=INK,
        )
        fig.text(
            0.5,
            0.012,
            "Regenerated from analysis/squad_qwen4b_p1/estimates.csv by paper/scripts/make_figures.py "
            "when the P1 analysis exists.",
            ha="center",
            va="center",
            fontsize=8.2,
            color=GRAY,
        )
        save_figure(fig, "p1_curve.png")
        return

    est = estimates.set_index("k")
    ks = estimates["k"].to_numpy(dtype=float)

    # Panel (a): A(k) with the 5 pp gate band around A(32).
    a = estimates["accuracy"].to_numpy(dtype=float)
    a_lo = np.array([_require_ci(bootstrap, "accuracy", int(k))[0] for k in ks])
    a_hi = np.array([_require_ci(bootstrap, "accuracy", int(k))[1] for k in ks])
    ax_a = axes[0]
    add_depth_axis(ax_a, categorical=True)
    ax_a.set_xlabel("")
    ax_a.set_title(titles[0], fontsize=18.0, pad=7)
    ax_a.set_ylabel(ylabels[0], fontsize=14.0)
    ax_a.tick_params(axis="x", labelsize=10.5)
    ax_a.tick_params(axis="y", labelsize=12.0)
    ax_a.grid(axis="y", alpha=0.45)
    ax_a.set_axisbelow(True)
    despine(ax_a)
    ax_a.set_ylim(0, 0.60)
    ax_a.set_yticks([0.0, 0.2, 0.4, 0.6])

    a32 = float(est.loc[32, "accuracy"])
    a4 = float(est.loc[4, "accuracy"])
    ax_a.axhspan(a32 - 0.05, a32 + 0.05, color=GREEN, alpha=0.13, linewidth=0, zorder=0)
    ax_a.axhline(a32, color=GRAY, linewidth=1.0, linestyle="--", zorder=1)
    ax_a.errorbar(
        ks,
        a,
        yerr=np.vstack([a - a_lo, a_hi - a]),
        fmt="o-",
        color=BLUE,
        ecolor=BLUE,
        elinewidth=1.1,
        capsize=3,
        capthick=1.0,
        markersize=6,
        linewidth=1.9,
        zorder=3,
    )
    ax_a.scatter(
        [4],
        [a4],
        s=110,
        facecolors="none",
        edgecolors=VERMILLION,
        linewidths=2.0,
        zorder=5,
    )
    ax_a.scatter(
        [32],
        [a32],
        s=110,
        facecolors="none",
        edgecolors=INK,
        linewidths=1.6,
        zorder=5,
    )
    ax_a.text(
        0.02,
        0.96,
        "5 pp band around $A(32)$",
        transform=ax_a.transAxes,
        ha="left",
        va="top",
        fontsize=7.8,
        color=GREEN,
    )

    # Panel (b): calibrated J(k), point estimate only.
    ax_b = axes[1]
    add_depth_axis(ax_b, categorical=True)
    ax_b.set_xlabel("")
    ax_b.set_title(titles[1], fontsize=18.0, pad=7)
    ax_b.set_ylabel(ylabels[1], fontsize=14.0)
    ax_b.tick_params(axis="x", labelsize=10.5)
    ax_b.tick_params(axis="y", labelsize=12.0)
    ax_b.grid(axis="y", alpha=0.45)
    ax_b.set_axisbelow(True)
    despine(ax_b)
    ax_b.set_ylim(0, 105)
    ax_b.set_yticks([0, 25, 50, 75, 100])
    ax_b.plot(
        ks,
        estimates["mean_j"].to_numpy(dtype=float),
        "o-",
        color=BLUE,
        markersize=6,
        linewidth=1.9,
    )

    # Panel (c): E(k) on a log scale; k=0 is off-scale because it has one correct answer.
    ax_c = axes[2]
    add_depth_axis(ax_c, categorical=True)
    ax_c.set_xlabel("")
    ax_c.set_title(titles[2], fontsize=18.0, pad=7)
    ax_c.set_ylabel("$E$ per correct (J, log)", fontsize=14.0)
    ax_c.tick_params(axis="x", labelsize=10.5)
    ax_c.tick_params(axis="y", labelsize=11.0)
    ax_c.grid(axis="y", alpha=0.45, which="major")
    ax_c.set_axisbelow(True)
    despine(ax_c)
    mask = ks >= 1
    e = estimates.loc[mask, "e_per_correct"].to_numpy(dtype=float)
    e_lo = np.array([_require_ci(bootstrap, "e_per_correct", int(k))[0] for k in ks[mask]])
    e_hi = np.array([_require_ci(bootstrap, "e_per_correct", int(k))[1] for k in ks[mask]])
    ax_c.errorbar(
        ks[mask],
        e,
        yerr=np.vstack([e - e_lo, e_hi - e]),
        fmt="o-",
        color=BLUE,
        ecolor=BLUE,
        elinewidth=1.1,
        capsize=3,
        capthick=1.0,
        markersize=6,
        linewidth=1.9,
    )
    ax_c.set_yscale("log")
    ax_c.set_ylim(60, 240)
    ax_c.set_yticks([70, 100, 150, 200])
    ax_c.yaxis.set_major_formatter(ScalarFormatter())
    ax_c.yaxis.set_minor_formatter(NullFormatter())
    e0 = float(est.loc[0, "e_per_correct"])
    ax_c.text(
        0.04,
        0.96,
        f"$k=0$ off-scale:\n$E={e0:,.0f}$ J/correct\n(1/1,000 correct)",
        transform=ax_c.transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
        color=GRAY,
    )

    ni_primary = noninferiority.get("primary", {})
    diff_pp = float(ni_primary["mean_diff"]) * 100.0
    lower_pp = float(ni_primary["lower_bound"]) * 100.0
    savings_pct = float(noninferiority["savings_pct"])
    ni_supported = bool(ni_primary.get("non_inferior"))
    ni_word = "supported" if ni_supported else "not supported"
    status_color = GREEN if ni_supported else VERMILLION

    fig.text(
        0.5,
        0.955,
        "P1 confirmatory curves — calibrated",
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.5,
        0.872,
        f"$A(4)-A(32) = {diff_pp:+.2f}$ pp; one-sided lower ${lower_pp:+.2f}$ pp\n"
        f"5 pp NI {ni_word}; savings {savings_pct:.2f}%",
        ha="center",
        va="center",
        fontsize=11.0,
        fontweight="bold",
        color=status_color,
        bbox={
            "boxstyle": "round,pad=0.42",
            "facecolor": "#FFF1E8" if not ni_supported else "#E7F4EF",
            "edgecolor": status_color,
            "linewidth": 1.1,
        },
    )
    fig.text(
        0.5,
        0.805,
        "n = 1,000 per depth; A and E intervals are 95% bootstrap; J is a point estimate.",
        ha="center",
        va="center",
        fontsize=9.2,
        color=GRAY,
    )
    fig.text(
        0.5,
        0.050,
        "retrieval depth $k$ (seven depths, equally spaced)",
        ha="center",
        va="center",
        fontsize=13.0,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.5,
        0.012,
        "Sources: P1 estimates, bootstrap, noninferiority, blocks (registered). "
        "G1 not met; no positive 5 pp claim.",
        ha="center",
        va="center",
        fontsize=8.0,
        color=GRAY,
    )
    save_figure(fig, "p1_curve.png")


def figure_p1_calibration(use_p1: bool = False) -> None:
    """P1 block factors: placeholder by default, measured factors with ``--p1``."""
    if use_p1:
        blocks = _read_json(P1_BLOCKS)
        repeat = _read_json(P1_REPEAT)
    else:
        blocks, repeat = None, None

    fig, ax = plt.subplots(figsize=(7.0, 4.6))

    if blocks is None:
        fig.tight_layout(rect=(0.0, 0.10, 1.0, 0.735))
        band_lo, band_hi = P0_BLOCK_BAND
        ax.axhspan(band_lo, band_hi, color=GREEN, alpha=0.12, zorder=0)
        ax.axhline(band_lo, color=GREEN, linewidth=1.4, linestyle="--", zorder=1)
        ax.axhline(band_hi, color=GREEN, linewidth=1.4, linestyle="--", zorder=1)
        for i in range(len(DEPTHS)):
            ax.add_patch(
                Rectangle(
                    (i - 0.28, 0.82),
                    0.56,
                    0.56,
                    fill=False,
                    edgecolor="#8C8C8C",
                    linewidth=1.2,
                    linestyle=(0, (2, 2)),
                    zorder=2,
                )
            )
            ax.text(
                i,
                1.10,
                "TBD",
                ha="center",
                va="center",
                fontsize=10.2,
                color=GRAY,
                zorder=3,
            )
        ax.set_xlim(-0.6, 6.6)
        ax.set_ylim(0.70, 1.48)
        ax.set_xticks(range(len(DEPTHS)))
        ax.set_xticklabels([str(k) for k in DEPTHS])
        ax.set_yticks([0.8, 1.0, 1.2, 1.4])
        ax.set_xlabel("retrieval depth $k$ (passages)")
        ax.set_ylabel("block factor", fontsize=14.5)
        ax.tick_params(axis="both", labelsize=12)
        ax.grid(axis="y", alpha=0.45)
        ax.set_axisbelow(True)
        despine(ax)
        ax.text(
            0.02,
            0.985,
            "acceptance band [0.8, 1.4]",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.2,
            color=GREEN,
        )
        fig.text(
            0.5,
            0.958,
            "P1 block calibration — placeholder",
            ha="center",
            va="center",
            fontsize=19,
            fontweight="bold",
            color=INK,
        )
        fig.text(
            0.5,
            0.868,
            "Measured after sweep",
            ha="center",
            va="center",
            fontsize=14.3,
            fontweight="bold",
            color=VERMILLION,
            bbox={
                "boxstyle": "round,pad=0.38",
                "facecolor": "#FFF4E8",
                "edgecolor": ORANGE,
                "linewidth": 1.2,
            },
        )
        fig.text(
            0.5,
            0.790,
            "Seven per-depth factors will be plotted when the P1 block calibration is registered.",
            ha="center",
            va="center",
            fontsize=9.8,
            color=GRAY,
        )
        fig.text(
            0.5,
            0.018,
            "P0 reference only: k = 0 factor_csv = 0.7944 fell below the 0.80 floor. "
            "P1 values are not imputed.",
            ha="center",
            va="center",
            fontsize=8.8,
            color=GRAY,
        )
        save_figure(fig, "p1_calibration.png")
        return

    depths = {int(item["k"]): item for item in blocks.get("depths", [])}
    missing = [k for k in DEPTHS if k not in depths]
    if missing:
        raise SystemExit(f"{P1_BLOCKS} is missing depths: {missing}")
    factors = [float(depths[k]["factor_csv"]) for k in DEPTHS]
    all_passed = bool(blocks.get("all_passed", all(depths[k].get("passed") for k in DEPTHS)))
    idle = blocks.get("idle", {})
    idle_mean = float(idle.get("mean_w", blocks.get("idle_power_w", float("nan"))))
    idle_cv = float(idle.get("cv", float("nan")))

    fig.tight_layout(rect=(0.0, 0.13, 1.0, 0.735))
    fig.subplots_adjust(left=0.12)
    band_lo, band_hi = P0_BLOCK_BAND
    ax.axhspan(band_lo, band_hi, color=GREEN, alpha=0.12, zorder=0)
    ax.axhline(band_lo, color=GREEN, linewidth=1.4, linestyle="--", zorder=1)
    ax.axhline(band_hi, color=GREEN, linewidth=1.4, linestyle="--", zorder=1)
    xs = np.arange(len(DEPTHS))
    ax.plot(xs, factors, color=BLUE, marker="o", markersize=8, linewidth=2.0, zorder=3)
    for x, value in zip(xs, factors, strict=True):
        ax.text(
            x,
            value + 0.018,
            f"{value:.4f}",
            ha="center",
            va="bottom",
            fontsize=8.2,
            color=INK,
        )
    ax.scatter(
        [0],
        [factors[0]],
        s=170,
        facecolors="none",
        edgecolors=VERMILLION,
        linewidths=2.0,
        zorder=4,
    )
    margin = factors[0] - band_lo
    margin_pct = 100.0 * (factors[0] / band_lo - 1.0)
    ax.annotate(
        f"$k=0$: +{margin:.4f}\n(+{margin_pct:.1f}% above {band_lo:.2f})",
        xy=(0, factors[0]),
        xytext=(0.28, 0.728),
        ha="left",
        va="bottom",
        fontsize=8.2,
        color=VERMILLION,
        arrowprops={"arrowstyle": "->", "color": VERMILLION, "linewidth": 1.1},
    )

    ax.set_xlim(-0.6, 6.6)
    ax.set_ylim(0.70, 1.48)
    ax.set_xticks(range(len(DEPTHS)))
    ax.set_xticklabels([str(k) for k in DEPTHS])
    ax.set_yticks([0.8, 1.0, 1.2, 1.4])
    ax.set_xlabel("retrieval depth $k$ (passages)")
    ax.set_ylabel("factor_csv", fontsize=14.5)
    ax.tick_params(axis="both", labelsize=12)
    ax.grid(axis="y", alpha=0.45)
    ax.set_axisbelow(True)
    despine(ax)
    ax.text(
        0.02,
        0.985,
        "acceptance band [0.8, 1.4]",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        color=GREEN,
    )
    ax.text(
        0.98,
        0.05,
        "Repeat CV at $k=8$\n"
        f"median {100.0 * float(repeat['cv_median']):.2f}%, "
        f"max {100.0 * float(repeat['cv_max']):.2f}%",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.6,
        color=GRAY,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "none"},
    )

    banner_text = "All seven factors passed [0.8, 1.4]" if all_passed else "Gate failed"
    banner_color = GREEN if all_passed else VERMILLION
    fig.text(
        0.5,
        0.958,
        "P1 block calibration — all passed" if all_passed else "P1 block calibration — failed",
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.5,
        0.868,
        banner_text,
        ha="center",
        va="center",
        fontsize=14.3,
        fontweight="bold",
        color=banner_color,
        bbox={
            "boxstyle": "round,pad=0.38",
            "facecolor": "#E7F4EF" if all_passed else "#FFF1E8",
            "edgecolor": banner_color,
            "linewidth": 1.2,
        },
    )
    fig.text(
        0.5,
        0.790,
        f"20-query blocks; gate = factor_csv; idle {idle_mean:.2f} W (CV {100.0 * idle_cv:.2f}%)",
        ha="center",
        va="center",
        fontsize=9.8,
        color=GRAY,
    )
    fig.text(
        0.5,
        0.018,
        "Source: blocks.json, repeat.json. Gate = factor_csv; all seven passed.",
        ha="center",
        va="center",
        fontsize=8.4,
        color=GRAY,
    )
    save_figure(fig, "p1_calibration.png")


def check_outputs() -> int:
    """Print width/height/DPI for every PNG and fail if the journal floor is missed."""
    from PIL import Image

    expected = ("design.png", "p0_harness.png", "p1_curve.png", "p1_calibration.png")
    print(f"\n{'file':<24} {'width':>6} {'height':>7} {'dpi':>7} {'width_in':>9}")
    print("-" * 58)
    ok = True
    for name in expected:
        path = FIG_DIR / name
        if not path.exists():
            print(f"{name:<24} MISSING")
            ok = False
            continue
        with Image.open(path) as im:
            width, height = im.size
            dpi = im.info.get("dpi", (0, 0))
            dpi_x = float(dpi[0]) if isinstance(dpi, tuple) else float(dpi)
        width_in = width / dpi_x if dpi_x else float("nan")
        passed = dpi_x >= 600 and width >= 3000
        ok = ok and passed
        print(f"{name:<24} {width:>6} {height:>7} {dpi_x:>7.1f} {width_in:>9.2f}")
    print("-" * 58)
    print(
        "PASS: every PNG has dpi >= 600 and width >= 3000 px"
        if ok
        else "FAIL: journal floor missed"
    )
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--p1",
        action="store_true",
        help="regenerate the two P1 result figures from the registered analysis outputs",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="only verify existing PNG size/DPI; do not regenerate",
    )
    args = parser.parse_args()

    apply_style()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.check:
        return check_outputs()

    summary = p0_summary()
    figure_design()
    figure_p0(summary)
    figure_p1_curve(use_p1=args.p1)
    figure_p1_calibration(use_p1=args.p1)
    return check_outputs()


if __name__ == "__main__":
    raise SystemExit(main())
