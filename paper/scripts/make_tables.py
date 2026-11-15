#!/usr/bin/env python
"""Build the paper's LaTeX tables from registered run files.

Outputs (``paper/tables``):

* ``p0_harness.tex``   -- P0 ``_r3`` per-depth uncalibrated GPU energy + k=0 diagnostic
* ``p1_estimates.tex`` -- P1 per-depth estimates, or a TBD template while P1 is pending

Rules:

* No number is hand-typed.  P0 values are recomputed from
  ``runs/golden_squad_qwen4b_p0_r3/raw.csv``; the three k=0 block constants are
  documented constants from ``docs/P0_HARNESS_REPORT.md`` because the run produced no
  ``blocks.json``.  P1 values are read from ``analysis/squad_qwen4b_p1/estimates.csv``
  only when that file exists.
* The P1 table never promotes a descriptive difference into a non-inferiority result.
  The registered analysis supplies the test; this table reports descriptive estimates.

Run from the repository root::

    python paper/scripts/make_tables.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "paper" / "tables"
P0_RAW = ROOT / "runs" / "golden_squad_qwen4b_p0_r3" / "raw.csv"
P0_MANIFEST = ROOT / "runs" / "golden_squad_qwen4b_p0_r3" / "manifest.json"
P1_ESTIMATES = ROOT / "analysis" / "squad_qwen4b_p1" / "estimates.csv"

DEPTHS = (0, 1, 2, 4, 8, 16, 32)

# Measured P0 k=0 block diagnostic.  These are not fitted or rounded from a plot.
# Source: docs/P0_HARNESS_REPORT.md Sec. 6 (verbatim); no blocks.json exists for _r3.
P0_K0_FACTOR_CSV = 0.7944
P0_K0_FACTOR_BLOCK = 0.9989
P0_K0_CONSISTENCY = 1.2573
P0_BLOCK_BAND = (0.8, 1.4)  # fixed pre-registered band, report Sec. 3.1

# Fallback idle values, used only if manifest.json is unreadable.
# Source: docs/P0_HARNESS_REPORT.md Sec. 6 and runs/golden_squad_qwen4b_p0_r3/manifest.json.
P0_IDLE_MEAN_W = 15.572577
P0_IDLE_CV = 0.011198
P0_IDLE_N = 551

# Two-sided 95% t critical value for the 200-question P0 blocks.
# Source: scipy.stats.t.ppf(0.975, 199) = 1.97196; the P0 grid fixes n = 200 per depth.
P0_T_CRIT_95_DF199 = 1.9720


def _fmt(value: Any, digits: int) -> str:
    """Format a finite number; return TBD for missing and -- for undefined."""
    if value is None:
        return "TBD"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "TBD"
    if math.isnan(number):
        return "TBD"
    if math.isinf(number):
        return "--"
    return f"{number:.{digits}f}"


def _read_p0() -> pd.DataFrame:
    if not P0_RAW.exists():
        raise SystemExit(f"missing P0 raw CSV: {P0_RAW}")
    df = pd.read_csv(P0_RAW)
    required = {"k", "j_gpu_raw", "correct_em", "valid"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{P0_RAW} is missing columns: {sorted(missing)}")
    return df


def _p0_idle() -> tuple[float, float, int]:
    if P0_MANIFEST.exists():
        data = json.loads(P0_MANIFEST.read_text(encoding="utf-8"))
        idle = data.get("idle", {})
        try:
            return (
                float(idle["mean_w"]),
                float(idle["cv"]),
                int(idle.get("n", P0_IDLE_N)),
            )
        except (KeyError, TypeError, ValueError):
            pass
    return P0_IDLE_MEAN_W, P0_IDLE_CV, P0_IDLE_N


def _p0_rows() -> list[dict[str, float]]:
    df = _read_p0()
    rows: list[dict[str, float]] = []
    for k in DEPTHS:
        g = df[(df["k"] == k) & (df["valid"] == 1)]
        if g.empty:
            continue
        j = g["j_gpu_raw"].to_numpy(dtype=float)
        correct = g["correct_em"].to_numpy(dtype=float)
        n_correct = float(correct.sum())
        mean_j = float(j.mean())
        n = len(g)
        se = float(j.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
        t_crit = P0_T_CRIT_95_DF199 if n == 200 else 1.96
        rows.append(
            {
                "k": float(k),
                "n_valid": float(len(g)),
                "n_invalid": float(len(df[df["k"] == k]) - len(g)),
                "accuracy": float(correct.mean()),
                "mean_j": mean_j,
                "ci_low": mean_j - t_crit * se,
                "ci_high": mean_j + t_crit * se,
                "e_gpu": float(j.sum() / n_correct) if n_correct > 0 else float("inf"),
            }
        )
    if not rows:
        raise SystemExit(f"no valid P0 rows in {P0_RAW}")
    return rows


def write_p0_table() -> Path:
    """Write ``p0_harness.tex`` from the _r3 raw rows and documented constants."""
    rows = _p0_rows()
    idle_mean, idle_cv, idle_n = _p0_idle()

    lines: list[str] = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{P0 harness energy by retrieval depth for run "
        r"\texttt{golden\_squad\_qwen4b\_p0\_r3}. Values are recomputed from "
        r"\texttt{raw.csv}; $J_{\mathrm{gpu,raw}}$ is per-query GPU energy before block "
        r"calibration. The run is uncalibrated and is not a paper result.}",
        r"\label{tab:p0_harness}",
        r"\small",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{rrrrrrr}",
        r"\toprule",
        r"$k$ & $n_{\mathrm{valid}}$ & $n_{\mathrm{invalid}}$ & $A(k)$ & "
        r"$\bar{J}_{\mathrm{gpu,raw}}$ (J) & 95\% CI (J) & "
        r"$E_{\mathrm{gpu,raw}}$ (J/correct) \\",
        r"\midrule",
    ]
    for row in rows:
        ci = f"[{_fmt(row['ci_low'], 2)}, {_fmt(row['ci_high'], 2)}]"
        lines.append(
            f"{int(row['k'])} & {int(row['n_valid'])} & {int(row['n_invalid'])} & "
            f"{_fmt(row['accuracy'], 3)} & {_fmt(row['mean_j'], 2)} & {ci} & "
            f"{_fmt(row['e_gpu'], 1)} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\par\vspace{2pt}",
            r"\begin{flushleft}",
            r"\footnotesize",
            r"Block calibration at $k=0$: "
            rf"$\mathrm{{factor}}_{{\mathrm{{csv}}}}={P0_K0_FACTOR_CSV:.4f}$ "
            rf"(outside $[{P0_BLOCK_BAND[0]:.1f},{P0_BLOCK_BAND[1]:.1f}]$; FAIL), "
            rf"$\mathrm{{factor}}_{{\mathrm{{block}}}}={P0_K0_FACTOR_BLOCK:.4f}$, "
            rf"consistency $={P0_K0_CONSISTENCY:.4f}$. "
            rf"Idle baseline $={idle_mean:.3f}$ W, CV $={idle_cv * 100:.2f}\%$, "
            rf"$n={idle_n}$. Because calibration failed, "
            r"$j_{\mathrm{gpu,calibrated}}\equiv j_{\mathrm{gpu,raw}}$; no calibrated "
            r"$J$ curve exists. $E$ is total GPU joules over total correct answers; "
            r"$k=0$ has zero correct answers. Sources: "
            r"\texttt{runs/golden\_squad\_qwen4b\_p0\_r3/raw.csv}, "
            r"\texttt{runs/golden\_squad\_qwen4b\_p0\_r3/manifest.json}, "
            r"\texttt{docs/P0\_HARNESS\_REPORT.md}.",
            r"\end{flushleft}",
            r"\end{table}",
            "",
        ]
    )
    path = TABLE_DIR / "p0_harness.tex"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")
    return path


def _read_p1_estimates() -> pd.DataFrame | None:
    if not P1_ESTIMATES.exists():
        return None
    df = pd.read_csv(P1_ESTIMATES)
    aliases = {
        "accuracy": ("accuracy", "a_em"),
        "mean_j": ("mean_j", "j_mean"),
        "e_per_correct": ("e_per_correct", "e_j_per_correct"),
        "n_valid": ("n_valid", "n"),
        "n_invalid": ("n_invalid",),
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


def _p1_row_map(df: pd.DataFrame) -> dict[int, pd.Series]:
    return {int(row["k"]): row for _, row in df.iterrows()}


def write_p1_table() -> Path:
    """Write ``p1_estimates.tex``; TBD template until the P1 estimates exist."""
    df = _read_p1_estimates()
    lines: list[str] = [
        r"\begin{table}[t]",
        r"\centering",
    ]

    if df is None:
        lines.extend(
            [
                r"\caption{P1 confirmatory estimates by retrieval depth. TEMPLATE: the P1 "
                r"analysis has not been produced, so every estimate cell is TBD. This table "
                r"is rewritten automatically when "
                r"\texttt{analysis/squad\_qwen4b\_p1/estimates.csv} exists.}",
                r"\label{tab:p1_estimates}",
                r"\small",
                r"\setlength{\tabcolsep}{4pt}",
                r"\begin{tabular}{rrrrrr}",
                r"\toprule",
                r"$k$ & $n_{\mathrm{valid}}$ & $n_{\mathrm{invalid}}$ & $A(k)$ & "
                r"$J(k)$ (J) & $E(k)$ (J/correct) \\",
                r"\midrule",
            ]
        )
        for k in DEPTHS:
            lines.append(f"{k} & TBD & TBD & TBD & TBD & TBD \\\\")
        lines.extend(
            [
                r"\bottomrule",
                r"\end{tabular}",
                r"\par\vspace{2pt}",
                r"\begin{flushleft}",
                r"\footnotesize",
                r"Primary contrast: 5 pp EM non-inferiority at $k=4$ vs $k=32$, with "
                r"savings $1-E(4)/E(32)$: TBD. No P1 result is claimed until the "
                r"registered analysis exists.",
                r"\end{flushleft}",
                r"\end{table}",
                "",
            ]
        )
    else:
        by_k = _p1_row_map(df)
        lines.extend(
            [
                r"\caption{P1 confirmatory estimates by retrieval depth. Values are read "
                r"verbatim from \texttt{analysis/squad\_qwen4b\_p1/estimates.csv}; "
                r"$J(k)$ and $E(k)$ are uncalibrated whenever any block factor fails.}",
                r"\label{tab:p1_estimates}",
                r"\small",
                r"\setlength{\tabcolsep}{4pt}",
                r"\begin{tabular}{rrrrrr}",
                r"\toprule",
                r"$k$ & $n_{\mathrm{valid}}$ & $n_{\mathrm{invalid}}$ & $A(k)$ & "
                r"$J(k)$ (J) & $E(k)$ (J/correct) \\",
                r"\midrule",
            ]
        )
        for k in DEPTHS:
            row = by_k.get(k)
            if row is None:
                lines.append(f"{k} & TBD & TBD & TBD & TBD & TBD \\\\")
                continue
            n_valid = row.get("n_valid") if "n_valid" in row.index else None
            n_invalid = row.get("n_invalid") if "n_invalid" in row.index else None
            lines.append(
                f"{k} & {_fmt(n_valid, 0)} & {_fmt(n_invalid, 0)} & "
                f"{_fmt(row.get('accuracy'), 3)} & {_fmt(row.get('mean_j'), 2)} & "
                f"{_fmt(row.get('e_per_correct'), 1)} \\\\"
            )
        lines.extend(
            [
                r"\bottomrule",
                r"\end{tabular}",
                r"\par\vspace{2pt}",
                r"\begin{flushleft}",
                r"\footnotesize",
            ]
        )
        contrast = _p1_contrast_text(by_k)
        lines.append(contrast)
        lines.extend(
            [
                r"The one-sided 5 pp non-inferiority test and its interval are reported "
                r"by the registered P1 analysis; this table is descriptive.",
                r"\end{flushleft}",
                r"\end{table}",
                "",
            ]
        )

    path = TABLE_DIR / "p1_estimates.tex"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")
    return path


def _p1_contrast_text(by_k: dict[int, pd.Series]) -> str:
    """Return a descriptive k=4 vs k=32 contrast, never a non-inferiority verdict."""
    if 4 not in by_k or 32 not in by_k:
        return r"Primary contrast: $A(4)-A(32)$ and $1-E(4)/E(32)$: TBD."
    a4 = float(by_k[4]["accuracy"])
    a32 = float(by_k[32]["accuracy"])
    e4 = float(by_k[4]["e_per_correct"])
    e32 = float(by_k[32]["e_per_correct"])
    if not all(math.isfinite(x) for x in (a4, a32, e4, e32)) or e32 == 0:
        return r"Primary contrast: $A(4)-A(32)$ and $1-E(4)/E(32)$: TBD."
    delta_pp = (a4 - a32) * 100.0
    savings_pct = (1.0 - e4 / e32) * 100.0
    return (
        r"Descriptive contrast (not the NI test): "
        rf"$A(4)-A(32)={delta_pp:+.1f}$ pp; "
        rf"$1-E(4)/E(32)={savings_pct:.1f}\%$."
    )


def main() -> int:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    write_p0_table()
    write_p1_table()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
