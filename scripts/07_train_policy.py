#!/usr/bin/env python
"""07 — Train and evaluate the query-conditional depth policy (stub)."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "07_train_policy: not implemented in v0.1.0.\n"
        "Planned: features from BM25 top score, score gap, entropy, question type and\n"
        "length; 600/200/200 train/validation/test; matched-accuracy evaluation against\n"
        "the best static k; report the fraction of the oracle gap captured.\n"
        "No test-set tuning. See ROADMAP.md P3 and stats/policy.py.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
