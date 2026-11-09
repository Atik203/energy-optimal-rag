#!/usr/bin/env python
"""04 — Run block energy calibration (stub)."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "04_run_blocks: not implemented in v0.1.0.\n"
        "Planned: 20 back-to-back queries per depth, idle-subtracted block total,\n"
        "scale factors written to runs/<run_id>/blocks.json. The pilot factors were\n"
        "1.041-1.188. See docs/MEASUREMENT.md section 4.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
