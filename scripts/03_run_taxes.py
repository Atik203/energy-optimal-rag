#!/usr/bin/env python
"""03 — Run energy-tax conditions (stub)."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "03_run_taxes: not implemented in v0.1.0.\n"
        "Planned: calibrate a fixed tax (raises a) and a per-passage tax (raises b)\n"
        "to 10-30% of the pilot baselines a=15.74 J and b=2.283 J/passage, then test\n"
        "the sign of the k* movement. See configs/taxes/ and docs/PROTOCOL.md section 6.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
