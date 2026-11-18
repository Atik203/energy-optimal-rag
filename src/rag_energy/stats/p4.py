"""P4 theory validation across registered arms.

Descriptive only: identity gaps, coverage-model fit, monotonicity checks,
margin/scoring sensitivity, and certification-cost curves. No gate is
re-adjudicated and no new confirmatory claim is created.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from rag_energy.stats.models import coverage_fit
from rag_energy.stats.p1 import (
    affine_lack_of_fit,
    certification_cost,
    identity_gap,
    load_rows,
    margin_sensitivity,
    scoring_sensitivity,
    summarize,
)

MARGINS = (0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, float):
        if value == float("inf"):
            return "Infinity"
        if value == float("-inf"):
            return "-Infinity"
    return value


def _arm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = summarize(rows, correct_key="em")
    by_k = {summary.k: summary for summary in summaries}
    depths = sorted(by_k)
    fit = affine_lack_of_fit([(summary.k, summary.mean_j) for summary in summaries])
    a0, p, coverage_r2 = coverage_fit(
        [float(depth) for depth in depths],
        [by_k[depth].accuracy for depth in depths],
    )
    monotone = all(
        by_k[depths[index]].accuracy <= by_k[depths[index + 1]].accuracy
        for index in range(len(depths) - 1)
    )
    identity = [
        identity_gap(summaries, a=float(fit["a"]), b=float(fit["b"]), depth=depth)
        for depth in depths
    ]
    reference = max(depths)
    margins = margin_sensitivity(summaries, margins=MARGINS, reference_depth=reference)
    scoring = scoring_sensitivity(rows, margins=MARGINS, reference_depth=reference)
    certification: dict[int, Any] = {}
    for row in margins:
        selected = row.get("selected_depth")
        if selected is None or selected == reference or selected in certification:
            continue
        certification[int(selected)] = certification_cost(
            summaries,
            selected_depth=int(selected),
            reference_depth=reference,
        )
    return {
        "n_rows": len(rows),
        "n_depths": len(depths),
        "depths": depths,
        "accuracy": {depth: by_k[depth].accuracy for depth in depths},
        "e_per_correct": {
            depth: by_k[depth].e_per_correct for depth in depths
        },
        "affine": fit,
        "coverage": {"a0": a0, "p": p, "r_squared": coverage_r2},
        "monotone": monotone,
        "identity": identity,
        "margin": margins,
        "scoring": scoring,
        "certification": certification,
    }


def write_p4_analysis(raw_paths: dict[str, Path], out_dir: Path) -> Path:
    """Write P4 summaries for each named arm and return the output directory."""
    if not raw_paths:
        raise ValueError("at least one arm is required")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    arms: dict[str, Any] = {}
    identity_rows: list[dict[str, Any]] = []
    margin_rows: list[dict[str, Any]] = []
    scoring_rows: list[dict[str, Any]] = []
    for arm, raw_path in raw_paths.items():
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"{arm}: missing raw CSV {path}")
        summary = _arm_summary(load_rows(path))
        arms[arm] = summary
        for row in summary["identity"]:
            identity_rows.append({"arm": arm, **row})
        for row in summary["margin"]:
            margin_rows.append({"arm": arm, **row})
        for scoring_rule, rows in summary["scoring"].items():
            for row in rows:
                scoring_rows.append({"arm": arm, "scoring": scoring_rule, **row})

    payload = {
        "arms": arms,
        "margins": list(MARGINS),
        "note": "P4 is descriptive; no gate is re-adjudicated.",
    }
    (out_dir / "p4.json").write_text(
        json.dumps(payload, indent=2, default=_to_jsonable), encoding="utf-8"
    )

    def write_csv(name: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
        with (out_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    write_csv(
        "identity.csv",
        identity_rows,
        ["arm", "depth", "gap", "epsilon_j", "epsilon_a", "method", "step"],
    )
    write_csv(
        "margin.csv",
        margin_rows,
        ["arm", "margin_pp", "selected_depth", "accuracy", "e_per_correct", "savings_pct"],
    )
    write_csv(
        "scoring.csv",
        scoring_rows,
        ["arm", "scoring", "margin_pp", "selected_depth", "accuracy", "savings_pct"],
    )

    lines = ["# P4 theory validation", ""]
    for arm, summary in arms.items():
        coverage = summary["coverage"]
        lines.extend(
            [
                f"## {arm}",
                "",
                f"- Rows: {summary['n_rows']}; depths: {summary['depths']}.",
                f"- Accuracy monotone: {summary['monotone']}.",
                f"- Affine fit: `J = {summary['affine']['a']:.4f} + "
                f"{summary['affine']['b']:.4f} k`, R2 = {summary['affine']['r2']:.4f}, "
                f"lack-of-fit p = {summary['affine']['lack_of_fit_p']:.4f}.",
                f"- Coverage fit: a0 = {coverage['a0']:.2f}, p = {coverage['p']:.3f}, "
                f"R2 = {coverage['r_squared']:.4f}.",
                "- Identity gaps: "
                + ", ".join(
                    f"k={row['depth']}: {row['gap']:.3f} ({row['method']})"
                    for row in summary["identity"]
                )
                + ".",
                "",
            ]
        )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_dir
