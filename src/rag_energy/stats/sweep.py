"""Sweep analysis: A(k), J(k), E(k), affine fit, and the P0 anchor check.

The estimator is a ratio of sums, not a mean of per-query ratios. Invalid rows
are excluded from the sums but reported at every depth. ``E = inf`` is retained
when a depth has no correct answers.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

P0_J_ANCHORS: dict[int, float] = {1: 17.98, 4: 25.10, 32: 89.55}
P0_FIT: dict[str, float] = {"a": 15.74, "b": 2.283}


@dataclass(frozen=True)
class DepthEstimate:
    k: int
    n_valid: int
    n_invalid: int
    n_correct: int
    accuracy: float
    mean_j: float
    e_per_correct: float
    mean_gpu_j: float
    mean_retrieval_j: float


@dataclass(frozen=True)
class AffineFit:
    a: float
    b: float
    r2: float
    n: int


def _is_one(value: Any) -> bool:
    return str(value).strip() in {"1", "1.0", "True", "true"}


def compute_estimates(rows: list[dict[str, Any]]) -> list[DepthEstimate]:
    """Compute per-depth estimates from raw rows."""
    if not rows:
        raise ValueError("no raw rows")
    depths = sorted({int(row["k"]) for row in rows})
    estimates: list[DepthEstimate] = []
    for depth in depths:
        valid_rows = [
            row for row in rows if int(row["k"]) == depth and str(row.get("valid", "1")) == "1"
        ]
        invalid = sum(
            1 for row in rows if int(row["k"]) == depth and str(row.get("valid", "1")) != "1"
        )
        n_valid = len(valid_rows)
        n_correct = sum(1 for row in valid_rows if _is_one(row.get("correct_em", 0)))
        sum_j = sum(float(row["j_total"]) for row in valid_rows)
        sum_gpu = sum(float(row["j_gpu_calibrated"]) for row in valid_rows)
        sum_retrieval = sum(float(row["j_retrieval_proxy"]) for row in valid_rows)
        estimates.append(
            DepthEstimate(
                k=depth,
                n_valid=n_valid,
                n_invalid=invalid,
                n_correct=n_correct,
                accuracy=(n_correct / n_valid) if n_valid else 0.0,
                mean_j=(sum_j / n_valid) if n_valid else 0.0,
                e_per_correct=(sum_j / n_correct) if n_correct else float("inf"),
                mean_gpu_j=(sum_gpu / n_valid) if n_valid else 0.0,
                mean_retrieval_j=(sum_retrieval / n_valid) if n_valid else 0.0,
            )
        )
    return estimates


def affine_fit(points: list[tuple[int, float]]) -> AffineFit:
    """Ordinary least squares fit of ``J(k) = a + b k``."""
    if len(points) < 2:
        raise ValueError("at least two points are required for an affine fit")
    xs = [float(k) for k, _ in points]
    ys = [float(value) for _, value in points]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("depth grid has no variation")
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    b = sxy / sxx
    a = mean_y - b * mean_x
    residuals = [y - (a + b * x) for x, y in zip(xs, ys, strict=True)]
    ss_res = sum(value**2 for value in residuals)
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return AffineFit(a=a, b=b, r2=r2, n=len(points))


def p0_check(
    estimates: list[DepthEstimate],
    fit: AffineFit,
    *,
    j_tolerance: float = 0.10,
    fit_tolerance: float = 0.10,
    min_r2: float = 0.95,
    calibrated: bool = True,
) -> dict[str, Any]:
    """Check the documented J anchors and affine fit; E/A are reported only."""
    by_k = {estimate.k: estimate for estimate in estimates}
    checks: list[dict[str, Any]] = []
    for depth, reference in P0_J_ANCHORS.items():
        estimate = by_k.get(depth)
        observed = estimate.mean_j if estimate is not None else None
        relative = (
            abs(observed - reference) / reference
            if observed is not None and reference != 0
            else None
        )
        checks.append(
            {
                "name": f"J({depth})",
                "observed": observed,
                "reference": reference,
                "relative_error": relative,
                "tolerance": j_tolerance,
                "passed": bool(relative is not None and relative <= j_tolerance),
            }
        )
    for name, observed, reference in (
        ("fit.a", fit.a, P0_FIT["a"]),
        ("fit.b", fit.b, P0_FIT["b"]),
    ):
        relative = abs(observed - reference) / reference
        checks.append(
            {
                "name": name,
                "observed": observed,
                "reference": reference,
                "relative_error": relative,
                "tolerance": fit_tolerance,
                "passed": bool(relative <= fit_tolerance),
            }
        )
    checks.append(
        {
            "name": "fit.r2",
            "observed": fit.r2,
            "reference": min_r2,
            "relative_error": None,
            "tolerance": None,
            "passed": bool(fit.r2 >= min_r2),
        }
    )
    return {
        "passed": all(item["passed"] for item in checks),
        "calibrated": calibrated,
        "adjudicable": calibrated,
        "note": (
            "Block-calibrated energy; the anchor check is adjudicable."
            if calibrated
            else "No block calibration was applied; the anchor check is confounded and "
            "is not adjudicable as a clean energy test."
        ),
        "checks": checks,
        "fit": asdict(fit),
        "e_anchors": {
            str(estimate.k): estimate.e_per_correct
            for estimate in estimates
            if estimate.k in P0_J_ANCHORS
        },
    }


def _write_estimates(path: Path, estimates: list[DepthEstimate]) -> None:
    fields = [
        "k",
        "n_valid",
        "n_invalid",
        "n_correct",
        "accuracy",
        "mean_j",
        "e_per_correct",
        "mean_gpu_j",
        "mean_retrieval_j",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for estimate in estimates:
            row = asdict(estimate)
            row["e_per_correct"] = (
                "inf" if math.isinf(estimate.e_per_correct) else estimate.e_per_correct
            )
            writer.writerow(row)


def write_analysis(raw_path: Path, out_dir: Path, run_id: str) -> Path:
    """Write estimates, the P0 check, and a markdown report for one sweep."""
    with raw_path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    estimates = compute_estimates(rows)
    fit = affine_fit([(estimate.k, estimate.mean_j) for estimate in estimates])
    calibrated = any(
        str(row.get("j_gpu_calibrated", "")) != str(row.get("j_gpu_raw", "")) for row in rows
    )
    check = p0_check(estimates, fit, calibrated=calibrated)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_estimates(out_dir / "estimates.csv", estimates)
    (out_dir / "p0_check.json").write_text(
        json.dumps(check, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    metadata: dict[str, Any] = {
        "run_id": run_id,
        "calibrated": calibrated,
        "config_sha256": None,
        "prereg_sha256": None,
        "git_commit": None,
        "seed": None,
    }
    manifest_path = raw_path.parent / "manifest.json"
    if manifest_path.is_file():
        run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata.update(
            {
                "config_sha256": run_manifest.get("config_sha256"),
                "prereg_sha256": run_manifest.get("prereg_sha256"),
                "git_commit": run_manifest.get("git_commit"),
                "seed": run_manifest.get("seed"),
            }
        )
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    lines = [
        f"# P0 sweep analysis - {run_id}",
        "",
        "| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for estimate in estimates:
        e_value = "inf" if math.isinf(estimate.e_per_correct) else f"{estimate.e_per_correct:.2f}"
        lines.append(
            f"| {estimate.k} | {estimate.n_valid} | {estimate.n_invalid} | "
            f"{estimate.accuracy:.4f} | {estimate.mean_j:.2f} | {e_value} |"
        )
    lines.extend(
        [
            "",
            f"Affine fit: `J(k) = {fit.a:.4f} + {fit.b:.4f} k`, R² = {fit.r2:.4f}.",
            f"Calibration: **{'applied' if calibrated else 'not applied'}**.",
            f"P0 anchor check: **{'PASS' if check['passed'] else 'FAIL'}**.",
        ]
    )
    if not calibrated:
        lines.append("The anchor check is not adjudicable as a clean energy test.")
    lines.append("")
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return out_dir
