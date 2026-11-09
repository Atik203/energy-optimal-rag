#!/usr/bin/env python
"""00 — Prepare datasets (stub).

Downloads are intentionally not automated in v0.1.0: the operator must confirm
the upstream license and record checksums in ``data/manifest.json``. See
``docs/DATA_CARD.md`` and ``data/README.md``.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "00_prepare_data: not implemented in v0.1.0.\n"
        "Planned inputs: SQuAD v1.1 dev, HotpotQA distractor dev.\n"
        "Planned outputs: data/processed/*.parquet plus data/manifest.json checksums.\n"
        "See docs/IMPLEMENTATION_PLAN.md section 4 and docs/RUNBOOK.md step 2.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
