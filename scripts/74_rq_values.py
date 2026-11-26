"""Print the registered R/Q deltas per arm so the slide figure can use them."""

from __future__ import annotations

import json
from pathlib import Path

d = json.loads(Path("analysis/recall_precision.json").read_text(encoding="utf-8"))

for arm, v in d.items():
    if not isinstance(v, dict) or "recall" not in v:
        continue
    depths = [str(k) for k in v["depths"]]
    hi = "32" if "32" in v["recall"] else depths[-1]
    lo = "4"
    dr = 100 * (v["recall"][hi] - v["recall"][lo])
    dq = 100 * (v["precision"][hi] - v["precision"][lo])
    da = 100 * (v["accuracy"][hi] - v["accuracy"][lo])
    print(f"{arm:22s} {lo}->{hi:>2s}   dR={dr:+5.1f}   dQ={dq:+5.1f}   dA={da:+5.1f}")
