#!/usr/bin/env python
"""20 - Exploratory inference layer for the P1 paired design.

Reads a registered raw sweep and writes ``analysis/inference/p1.json`` with the
restricted-MLE score test, the exact sensitivity, the TOST results at +/-5 and
+/-2 pp, realized power and required n at the observed discordance, BCa
intervals, the joint question bootstrap and the design MDE.

The preregistered 5 pp verdict is copied through unchanged. Every new number in
this payload is exploratory or sensitivity analysis and cannot promote that
verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.stats.inference import build_inference_payload  # noqa: E402
from rag_energy.stats.p1 import DEFAULT_SEED, _write_json, load_rows  # noqa: E402

REGISTERED_ANALYSIS = Path("analysis") / "squad_qwen4b_p1" / "noninferiority.json"
PREREG_FILES = ("prereg/PREREGISTRATION.md", "prereg/analysis_plan.md")


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def build_provenance(root: Path, raw_path: Path) -> dict[str, Any]:
    """Record the hashes the analysis plan requires alongside a result."""
    return {
        "raw_csv_sha256": _sha256(raw_path),
        "prereg_sha256": {name: _sha256(root / name) for name in PREREG_FILES},
        "git_commit": _git_commit(root),
    }


def _report(payload: dict[str, Any]) -> str:
    design = payload["design"]
    score = payload["score_test"]
    primary = payload["preregistered_primary"]
    exact = payload["exact_sensitivity"]
    lines = [
        f"# Exploratory inference layer - {payload['run_id']}",
        "",
        "All numbers below are **exploratory or sensitivity** analysis. The "
        "preregistered 5 pp verdict is unchanged.",
        "",
        "## Primary (confirmatory, unchanged)",
        "",
        f"- Paired n = {design['n_pairs']}; b = {design['b']}, c = {design['c']}; "
        f"discordance = {design['discordance']:.4f}.",
        f"- Mean difference A(4) - A(32) = {100 * design['mean_diff']:.2f} pp; "
        f"one-sided lower bound {100 * primary['lower_bound']:.2f} pp.",
        f"- Preregistered Wald z = {primary['z']:.4f}, p = {primary['p_value']:.4f}; "
        f"verdict: **{primary['verdict']}**.",
        "",
        "## Score and exact sensitivity",
        "",
        "| Test | z | p (one-sided) | Non-inferior |",
        "|---|---:|---:|---|",
        f"| Wald (preregistered) | {primary['z']:.4f} | {primary['p_value']:.4f} | "
        f"{primary['non_inferior']} |",
        f"| Restricted-MLE score | {score['z']:.4f} | {score['p_value']:.4f} | "
        f"{score['non_inferior']} |",
        f"| Exact unconditional | - | {exact['exact_unconditional_p']:.4f} | "
        f"{exact['exact_unconditional_p'] <= 0.05} |",
        f"| Exact conditional | - | {exact['exact_conditional_p']:.4f} | "
        f"{exact['exact_conditional_p'] <= 0.05} |",
        "",
        "## TOST",
        "",
        "| Margin | p | Equivalence |",
        "|---:|---:|---|",
    ]
    for label, key in (("+/-5 pp", "five_pp"), ("+/-2 pp", "two_pp")):
        block = payload["tost"][key]
        lines.append(f"| {label} | {block['p_tost']:.4f} | {block['equivalent']} |")
    lines.extend(
        [
            "",
            "## Power at the observed discordance",
            "",
            "| True d (pp) | Realized power | n at 50% | n at 80% |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in payload["realized_power"]:
        lines.append(
            f"| {row['true_diff_pp']:.1f} | {row['realized_power']:.4f} | "
            f"{row['required_n_50pct']} | {row['required_n_80pct']} |"
        )
    lines.extend(
        [
            "",
            f"MDE at 80% power: a true loss of {payload['mde']['mde_loss_pp']:.2f} pp is the "
            f"largest this design can still certify.",
            "",
            "## BCa intervals",
            "",
            f"- Mean difference: {100 * payload['bca']['mean_difference']['lower']:.2f} to "
            f"{100 * payload['bca']['mean_difference']['upper']:.2f} pp.",
            f"- Savings: {100 * payload['bca']['savings']['lower']:.2f} to "
            f"{100 * payload['bca']['savings']['upper']:.2f}%.",
            "",
            "## Joint bootstrap",
            "",
            f"- P(NI and savings >= 20%) = {payload['joint_bootstrap']['p_joint']:.4f} over "
            f"{payload['joint_bootstrap']['resamples']} resamples.",
            f"- P(NI) = {payload['joint_bootstrap']['p_non_inferior']:.4f}; "
            f"P(savings >= 20%) = {payload['joint_bootstrap']['p_savings_floor']:.4f}.",
            f"- Cluster bootstrap: {payload['cluster_bootstrap']['status']} "
            f"({payload['cluster_bootstrap'].get('reason', 'computed')}).",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exploratory inference layer for P1.")
    parser.add_argument("--run-id", default="squad_qwen4b_p1")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    parser.add_argument("--resamples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--margin-pp", type=float, default=5.0)
    args = parser.parse_args()

    root = Path(args.root)
    raw_path = root / "runs" / args.run_id / "raw.csv"
    if not raw_path.is_file():
        print(f"missing raw sweep: {raw_path}", file=sys.stderr)
        return 1
    out_dir = Path(args.out) if args.out else root / "analysis" / "inference"

    registered_path = root / REGISTERED_ANALYSIS
    registered = (
        json.loads(registered_path.read_text(encoding="utf-8"))
        if registered_path.is_file()
        else None
    )

    rows = load_rows(raw_path)
    payload = build_inference_payload(
        rows,
        run_id=args.run_id,
        margin=args.margin_pp / 100.0,
        resamples=args.resamples,
        seed=args.seed,
        registered=registered,
    )
    payload["provenance"] = build_provenance(root, raw_path)
    payload["software"] = {"python": sys.version.split()[0], "seed": args.seed}

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "p1.json", payload)
    (out_dir / "report.md").write_text(_report(payload), encoding="utf-8", newline="\n")

    consistency = payload.get("consistency_with_registered_analysis") or {}
    print(f"Inference layer: {out_dir / 'p1.json'}")
    print(f"score z = {payload['score_test']['z']:.4f}, p = {payload['score_test']['p_value']:.4f}")
    print(f"joint P(NI and savings >= 20%) = {payload['joint_bootstrap']['p_joint']:.4f}")
    print(f"matches registered analysis: {consistency.get('consistent')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
