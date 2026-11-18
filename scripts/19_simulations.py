#!/usr/bin/env python
"""19 - CPU-only simulation studies for the estimator and the NI test.

Runs S1 (ratio estimator), S2 (non-inferiority test/power), and S3
(selection/certification) with explicit seeds. Writes
``analysis/simulations/s1.json``, ``s2.json``, ``s3.json`` and ``report.md``.
With ``--figures``, also writes the three 650 dpi paper figures.

These are simulations, not empirical results. The script never reads a run,
uses a GPU, or touches the network.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.stats.simulations import (  # noqa: E402
    DEFAULT_SEED,
    S1_ACCURACIES,
    S1_BOOTSTRAP_REPS,
    S1_BOOTSTRAP_RESAMPLES,
    S1_NOISES,
    S1_REPS,
    S1_SAMPLE_SIZES,
    S2_DIFFERENCES,
    S2_REPS,
    S2_SAMPLE_SIZES,
    S3_BOOTSTRAP_RESAMPLES,
    S3_GAPS,
    S3_REPS,
    S3_SAMPLE_SIZES,
    simulate_power_study,
    simulate_ratio_study,
    simulate_selection_study,
    write_simulation_outputs,
)

# Okabe-Ito palette, matching the paper figures.
DPI = 650
BLUE = "#0072B2"
SKY = "#56B4E9"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
GRAY = "#6E6E6E"
LIGHT_GRAY = "#D9D9D9"
INK = "#1A1A1A"

QUICK_CONFIG: dict[str, Any] = {
    "s1_accuracies": (0.3, 0.8),
    "s1_sample_sizes": (60, 120),
    "s1_noises": ("lognormal", "gamma"),
    "s1_reps": 20,
    "s2_sample_sizes": (60, 120),
    "s2_differences": (-0.05, 0.0),
    "s2_reps": 30,
    "s3_gaps": (0.05, 0.25),
    "s3_sample_sizes": (60, 120),
    "s3_reps": 15,
    "bootstrap_reps": 6,
    "bootstrap_resamples": 30,
    "engine_check_resamples": 10,
}


def _apply_style() -> None:
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "mathtext.fontset": "dejavusans",
            "mathtext.default": "regular",
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.labelweight": "bold",
            "axes.edgecolor": INK,
            "axes.linewidth": 1.1,
            "axes.facecolor": "white",
            "axes.grid": False,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "xtick.major.size": 5,
            "ytick.major.size": 5,
            "xtick.major.width": 1.1,
            "ytick.major.width": 1.1,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.dpi": DPI,
            "figure.dpi": 110,
            "lines.linewidth": 2.0,
            "lines.markersize": 6,
            "grid.color": LIGHT_GRAY,
            "grid.linestyle": "--",
            "grid.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _despine(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _cells(study: dict[str, Any]) -> list[dict[str, Any]]:
    return list(study["cells"])


def _by_n(cells: list[dict[str, Any]], key: str, accuracy: float, noise: str) -> tuple:
    selected = [cell for cell in cells if cell["accuracy"] == accuracy and cell["noise"] == noise]
    selected.sort(key=lambda cell: cell["n"])
    values = []
    for cell in selected:
        value: Any = cell
        for part in key.split("."):
            value = value[part]
        values.append(value)
    return [cell["n"] for cell in selected], values


def _set_n_axis(ax: Any, ns: list[int]) -> None:
    ax.set_xscale("log")
    ax.set_xticks(ns)
    ax.set_xticklabels([f"{value:,}" for value in ns])
    ax.minorticks_off()
    ax.set_xlim(min(ns) * 0.78, max(ns) * 1.28)


def _ratio_figure(study: dict[str, Any], out: Path) -> None:
    import matplotlib.pyplot as plt

    _apply_style()
    cells = _cells(study)
    accuracies = sorted({cell["accuracy"] for cell in cells})
    colors = [BLUE, ORANGE, GREEN, VERMILLION]
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 6.4), layout="constrained")
    ax = axes[0, 0]
    for color, accuracy in zip(colors, accuracies, strict=False):
        ns, values = _by_n(cells, "ratio_of_sums.relative_bias", accuracy, "lognormal")
        ratios = [100.0 * float(value) if value is not None else float("nan") for value in values]
        ax.plot(ns, ratios, marker="o", color=color, label=f"A={accuracy:.1f}")
    ax.axhline(0.0, color=GRAY, linewidth=1.0, linestyle=":")
    _set_n_axis(ax, ns)
    ax.set_xlabel("paired queries $n$")
    ax.set_ylabel("relative bias (%)")
    ax.set_title("(a) Ratio-of-sums bias", loc="left")
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=9)

    ax = axes[0, 1]
    for color, accuracy in zip(colors, accuracies, strict=False):
        ns, values = _by_n(cells, "ratio_of_sums.rmse", accuracy, "lognormal")
        ax.plot(
            ns,
            [float(value) for value in values],
            marker="o",
            color=color,
            label=f"A={accuracy:.1f}",
        )
    _set_n_axis(ax, ns)
    ax.set_xlabel("paired queries $n$")
    ax.set_ylabel("RMSE (J/correct)")
    ax.set_title("(b) Ratio-of-sums RMSE", loc="left")
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=9)

    methods = (
        ("delta", BLUE, "Delta"),
        ("percentile", ORANGE, "Percentile"),
        ("bca", GREEN, "BCa"),
    )
    for panel, accuracy, label in (
        (axes[1, 0], 0.5, "(c) Coverage, A=0.5"),
        (axes[1, 1], 0.1, "(d) Coverage, A=0.1"),
    ):
        selected = sorted(
            [
                cell
                for cell in cells
                if cell["accuracy"] == accuracy and cell["noise"] == "lognormal"
            ],
            key=lambda cell: cell["n"],
        )
        ns = [cell["n"] for cell in selected]
        for method, color, method_label in methods:
            coverage = [
                100.0 * float(cell["ratio_of_sums"]["coverage"][method])
                if cell["ratio_of_sums"]["coverage"][method] is not None
                else float("nan")
                for cell in selected
            ]
            panel.plot(ns, coverage, marker="o", color=color, label=method_label)
        panel.axhline(95.0, color=VERMILLION, linewidth=1.1, linestyle="--")
        _set_n_axis(panel, ns)
        panel.set_xlabel("paired queries $n$")
        panel.set_ylabel("95% CI coverage (%)")
        panel.set_title(label, loc="left")
        panel.set_ylim(88, 100.5)
        panel.grid(True, axis="y")
        _despine(panel)
    axes[1, 0].legend(frameon=False, fontsize=9)
    fig.suptitle("S1: ratio estimator (lognormal copula)", fontsize=16, fontweight="bold")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def _power_figure(study: dict[str, Any], out: Path) -> None:
    import matplotlib.pyplot as plt

    _apply_style()
    cells = _cells(study)
    differences = sorted({cell["true_difference_pp"] for cell in cells})
    colors = [BLUE, ORANGE, GREEN, VERMILLION, PURPLE]
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.8), layout="constrained")
    ax = axes[0]
    for color, difference in zip(colors, differences, strict=False):
        selected = sorted(
            [cell for cell in cells if cell["true_difference_pp"] == difference],
            key=lambda cell: cell["n"],
        )
        ns = [cell["n"] for cell in selected]
        z_values = [100.0 * float(cell["rejection"]["z"]) for cell in selected]
        score_values = [100.0 * float(cell["rejection"]["score"]) for cell in selected]
        ax.plot(
            ns,
            z_values,
            marker="o",
            color=color,
            linestyle="-",
            label=f"d={difference:+.0f} pp",
        )
        ax.plot(ns, score_values, marker="s", color=color, linestyle="--", alpha=0.8)
    ax.axhline(5.0, color=GRAY, linewidth=1.0, linestyle=":")
    _set_n_axis(ax, ns)
    ax.set_xlabel("paired queries $n$")
    ax.set_ylabel("rejection rate (%)")
    ax.set_title("(a) Power: solid z, dashed score", loc="left")
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=8, ncol=2)

    ax = axes[1]
    for color, difference in ((BLUE, -5.0), (ORANGE, 0.0)):
        selected = sorted(
            [cell for cell in cells if cell["true_difference_pp"] == difference],
            key=lambda cell: cell["n"],
        )
        ns = [cell["n"] for cell in selected]
        wald = [100.0 * float(cell["coverage"]["wald_two_sided"]) for cell in selected]
        score = [100.0 * float(cell["coverage"]["score_two_sided"]) for cell in selected]
        ax.plot(ns, wald, marker="o", color=color, label=f"Wald, d={difference:+.0f}")
        ax.plot(
            ns,
            score,
            marker="s",
            color=color,
            linestyle="--",
            label=f"Score, d={difference:+.0f}",
        )
    ax.axhline(95.0, color=VERMILLION, linewidth=1.1, linestyle="--")
    _set_n_axis(ax, ns)
    ax.set_xlabel("paired queries $n$")
    ax.set_ylabel("95% CI coverage (%)")
    ax.set_title("(b) Interval coverage", loc="left")
    ax.set_ylim(88, 100.5)
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=8)
    fig.suptitle("S2: paired non-inferiority at a 5 pp margin", fontsize=16, fontweight="bold")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def _selection_figure(study: dict[str, Any], out: Path) -> None:
    import matplotlib.pyplot as plt

    _apply_style()
    cells = _cells(study)
    gaps = sorted({cell["gap"] for cell in cells})
    colors = [BLUE, ORANGE, GREEN]
    all_ns = sorted({cell["n"] for cell in cells})
    target_gap = 0.10 if any(abs(gap - 0.10) < 1e-12 for gap in gaps) else gaps[len(gaps) // 2]
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 6.4), layout="constrained")
    ax = axes[0, 0]
    for color, gap in zip(colors, gaps, strict=False):
        selected = sorted(
            [cell for cell in cells if cell["gap"] == gap], key=lambda cell: cell["n"]
        )
        ax.plot(
            [cell["n"] for cell in selected],
            [100.0 * float(cell["selection_rate"]) for cell in selected],
            marker="o",
            color=color,
            label=f"gap={100.0 * gap:.0f}%",
        )
    _set_n_axis(ax, all_ns)
    ax.set_xlabel("queries $n$")
    ax.set_ylabel("P(select k=4) (%)")
    ax.set_title("(a) Selection accuracy", loc="left")
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=9)

    ax = axes[0, 1]
    for color, gap in zip(colors, gaps, strict=False):
        selected = sorted(
            [cell for cell in cells if cell["gap"] == gap], key=lambda cell: cell["n"]
        )
        ax.plot(
            [cell["n"] for cell in selected],
            [100.0 * float(cell["bootstrap"]["p_true_mean"]) for cell in selected],
            marker="o",
            color=color,
            label=f"gap={100.0 * gap:.0f}%",
        )
    ax.axhline(80.0, color=VERMILLION, linewidth=1.1, linestyle="--")
    _set_n_axis(ax, all_ns)
    ax.set_xlabel("queries $n$")
    ax.set_ylabel("mean bootstrap P(k*) (%)")
    ax.set_title("(b) P(k* optimal)", loc="left")
    ax.set_ylim(0, 101)
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=9)

    ax = axes[1, 0]
    for color, gap in zip(colors, gaps, strict=False):
        selected = sorted(
            [cell for cell in cells if cell["gap"] == gap], key=lambda cell: cell["n"]
        )
        ax.plot(
            [cell["n"] for cell in selected],
            [float(cell["winner_curse"]["mean_e_bias"]) for cell in selected],
            marker="o",
            color=color,
            label=f"gap={100.0 * gap:.0f}%",
        )
    ax.axhline(0.0, color=GRAY, linewidth=1.0, linestyle=":")
    _set_n_axis(ax, all_ns)
    ax.set_xlabel("queries $n$")
    ax.set_ylabel("E bias (J/correct)")
    ax.set_title("(c) Winner's curse", loc="left")
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=9)

    ax = axes[1, 1]
    selected = sorted(
        [cell for cell in cells if abs(cell["gap"] - target_gap) < 1e-12],
        key=lambda cell: cell["n"],
    )
    ns = [cell["n"] for cell in selected]
    ax.plot(
        ns,
        [100.0 * float(cell["n_star"]["relative_bias"]) for cell in selected],
        marker="o",
        color=BLUE,
        label="N* (accuracy-weighted)",
    )
    ax.plot(
        ns,
        [100.0 * float(cell["n_star"]["exact_relative_bias"]) for cell in selected],
        marker="s",
        color=ORANGE,
        linestyle="--",
        label="N* exact (per-query energy)",
    )
    ax.axhline(0.0, color=GRAY, linewidth=1.0, linestyle=":")
    _set_n_axis(ax, ns)
    ax.set_xlabel("queries $n$")
    ax.set_ylabel("relative bias (%)")
    ax.set_title(f"(d) Certification cost, gap={100.0 * target_gap:.0f}%", loc="left")
    ax.grid(True, axis="y")
    _despine(ax)
    ax.legend(frameon=False, fontsize=8)
    fig.suptitle("S3: depth selection and certification", fontsize=16, fontweight="bold")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def make_figures(
    ratio_study: dict[str, Any],
    power_study: dict[str, Any],
    selection_study: dict[str, Any],
    figure_dir: Path,
) -> list[Path]:
    """Write the three 650 dpi paper figures."""
    figure_dir = Path(figure_dir)
    written = []
    for name, function, study in (
        ("sim_ratio.png", _ratio_figure, ratio_study),
        ("sim_power.png", _power_figure, power_study),
        ("sim_selection.png", _selection_figure, selection_study),
    ):
        path = figure_dir / name
        function(study, path)
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="small grid for a smoke run")
    parser.add_argument("--reps", type=int, default=None, help="replicates for every study")
    parser.add_argument("--bootstrap-reps", type=int, default=None)
    parser.add_argument("--bootstrap-resamples", type=int, default=None)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=ROOT / "analysis" / "simulations")
    parser.add_argument("--figures", action="store_true", help="write the paper figures")
    parser.add_argument("--figure-dir", type=Path, default=ROOT / "paper" / "figures")
    args = parser.parse_args(argv)

    if args.quick:
        config = QUICK_CONFIG
        reps = args.reps if args.reps is not None else config["s1_reps"]
        s2_reps = args.reps if args.reps is not None else config["s2_reps"]
        s3_reps = args.reps if args.reps is not None else config["s3_reps"]
        bootstrap_reps = (
            args.bootstrap_reps if args.bootstrap_reps is not None else config["bootstrap_reps"]
        )
        bootstrap_resamples = (
            args.bootstrap_resamples
            if args.bootstrap_resamples is not None
            else config["bootstrap_resamples"]
        )
        s1_accuracies = config["s1_accuracies"]
        s1_sample_sizes = config["s1_sample_sizes"]
        s1_noises = config["s1_noises"]
        s2_sample_sizes = config["s2_sample_sizes"]
        s2_differences = config["s2_differences"]
        s3_gaps = config["s3_gaps"]
        s3_sample_sizes = config["s3_sample_sizes"]
        engine_check_resamples = config["engine_check_resamples"]
    else:
        reps = args.reps if args.reps is not None else S1_REPS
        s2_reps = args.reps if args.reps is not None else S2_REPS
        s3_reps = args.reps if args.reps is not None else S3_REPS
        bootstrap_reps = (
            args.bootstrap_reps if args.bootstrap_reps is not None else S1_BOOTSTRAP_REPS
        )
        bootstrap_resamples = (
            args.bootstrap_resamples
            if args.bootstrap_resamples is not None
            else S1_BOOTSTRAP_RESAMPLES
        )
        s1_accuracies = S1_ACCURACIES
        s1_sample_sizes = S1_SAMPLE_SIZES
        s1_noises = S1_NOISES
        s2_sample_sizes = S2_SAMPLE_SIZES
        s2_differences = S2_DIFFERENCES
        s3_gaps = S3_GAPS
        s3_sample_sizes = S3_SAMPLE_SIZES
        engine_check_resamples = 80

    print("S1: ratio estimator ...", flush=True)
    ratio_study = simulate_ratio_study(
        accuracies=s1_accuracies,
        sample_sizes=s1_sample_sizes,
        noises=s1_noises,
        reps=reps,
        bootstrap_reps=bootstrap_reps,
        bootstrap_resamples=bootstrap_resamples,
        seed=args.seed,
    )
    print("S2: non-inferiority power ...", flush=True)
    power_study = simulate_power_study(
        sample_sizes=s2_sample_sizes,
        differences=s2_differences,
        reps=s2_reps,
        seed=args.seed + 1,
    )
    print("S3: selection and certification ...", flush=True)
    selection_study = simulate_selection_study(
        gaps=s3_gaps,
        sample_sizes=s3_sample_sizes,
        reps=s3_reps,
        bootstrap_reps=bootstrap_reps,
        bootstrap_resamples=min(bootstrap_resamples, S3_BOOTSTRAP_RESAMPLES)
        if not args.quick
        else bootstrap_resamples,
        seed=args.seed + 2,
        engine_check_resamples=engine_check_resamples,
    )
    written = write_simulation_outputs(args.out, ratio_study, power_study, selection_study)
    for path in written:
        print(f"wrote {path}", flush=True)
    if args.figures:
        try:
            figures = make_figures(ratio_study, power_study, selection_study, args.figure_dir)
        except ImportError as error:
            print(f"figures skipped: {error}", file=sys.stderr)
        else:
            for path in figures:
                print(f"wrote {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
