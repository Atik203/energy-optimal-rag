#!/usr/bin/env python
"""06 — Power and MDE table for the 5 pp non-inferiority test.

The pilot's MDE was roughly 4-5 pp at n=200. This script shows why n=1,000 is
the primary sample size and why 2 pp is estimation-only.

Assumptions are explicit and can be overridden on the command line. They are
planning assumptions, not measured values.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.stats.power import (  # noqa: E402
    minimum_detectable_effect,
    noninferiority_power,
    paired_difference_se,
)


def build_table(
    ns: list[int],
    differences: list[float],
    margin: float,
    discordant_rate: float,
    alpha: float,
) -> str:
    sd = paired_difference_se(discordant_rate, 1)  # SD of one paired difference
    lines = [
        f"# Power table: one-sided {margin:.0%} non-inferiority, alpha={alpha}",
        f"# Assumed discordant rate = {discordant_rate:.3f}; SD(diff) = {sd:.4f}",
        "",
        "| n | MDE (80% power) | " + " | ".join(f"diff {d:+.0%}" for d in differences) + " |",
        "|---:|---:|" + "---:|" * len(differences),
    ]
    for n in ns:
        mde = minimum_detectable_effect(n, sd, alpha=alpha, power=0.80)
        cells = [f"{noninferiority_power(n, d, margin, sd, alpha):.3f}" for d in differences]
        lines.append(f"| {n} | {mde:.3%} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--margin", type=float, default=0.05)
    parser.add_argument(
        "--discordant-rate",
        type=float,
        default=0.08,
        help="Planning discordant-pair rate (pre-registered), not a measured value.",
    )
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--ns", type=int, nargs="+", default=[200, 300, 500, 750, 1000, 1500, 2000])
    parser.add_argument(
        "--diffs",
        type=float,
        nargs="+",
        default=[0.0, 0.01, 0.02, 0.03],
    )
    args = parser.parse_args()
    print(build_table(args.ns, args.diffs, args.margin, args.discordant_rate, args.alpha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
