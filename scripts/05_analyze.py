#!/usr/bin/env python
"""05 — Analyze a completed run (stub)."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "05_analyze: not implemented in v0.1.0.\n"
        "Planned: E(k), A(k), S(k) with question-level bootstrap (10,000 resamples),\n"
        "5pp non-inferiority primary, 2pp estimation-only secondary, identity gap,\n"
        "bootstrap P(k* optimal), and N*. Outputs go to analysis/<run_id>/.\n"
        "See prereg/analysis_plan.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
