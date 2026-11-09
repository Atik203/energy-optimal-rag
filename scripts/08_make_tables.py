#!/usr/bin/env python
"""08 — Generate paper tables from registered analysis outputs (stub)."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "08_make_tables: not implemented in v0.1.0.\n"
        "Planned: every paper table is generated from analysis/<run_id>/ and mapped to a\n"
        "row in artifacts/claims_evidence.csv. No hand-edited numbers.\n"
        "See docs/IMPLEMENTATION_PLAN.md section 12.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
