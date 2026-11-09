#!/usr/bin/env python
"""02 — Run a depth sweep (stub)."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "02_run_sweep: not implemented in v0.1.0.\n"
        "Usage after P0: python scripts/02_run_sweep.py --config configs/runs/squad_qwen4b.toml\n"
        "The runner must randomize k within question, add a unique nonce to every request,\n"
        "and write runs/<run_id>/raw.csv. See docs/PROTOCOL.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
