"""32 - Generate the three Phase 8 fresh qid frames deterministically (CPU only).

Pool = all SQuAD dev qids minus the p0/p1 union (1,200 unique excluded; P3 is a
hashed subset of P1). Deterministic shuffle with seed 20261115, then slice in
plan order: fresh 1000, distractor 500, dense 1000 - mutually disjoint.

Writes data/splits/qc_frames.json (qid lists + per-frame SHA-256; the tracked source
of truth). Run outputs also merge the frames into the local
data/processed/squad_splits.json, which is what the loader reads. Regenerating with
the same seed must reproduce identical hashes; the frozen prereg records them.
No GPU, no network, no reader.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SEED = 20261115
SIZES = (("qc_fresh", 1000), ("qc_distractor", 500), ("qc_dense", 1000))


def _sha(items: list[str]) -> str:
    return hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    import pandas as pd

    questions = pd.read_parquet(ROOT / "data" / "processed" / "squad_questions.parquet")
    universe = [str(q) for q in questions["qid"]]
    assert len(universe) == 10570, f"expected 10570 dev qids, got {len(universe)}"

    splits = json.loads((ROOT / "data" / "processed" / "squad_splits.json").read_text(encoding="utf-8"))[
        "splits"
    ]
    excluded = set(splits["p0_golden"]) | set(splits["p1_primary"])
    assert len(excluded) == 1200, f"expected 1200 unique excluded, got {len(excluded)}"
    pool = [q for q in universe if q not in excluded]
    assert len(pool) == 9370, f"expected 9370 fresh, got {len(pool)}"

    rng = random.Random(SEED)
    order = list(pool)
    rng.shuffle(order)

    frames: dict[str, list[str]] = {}
    offset = 0
    for name, size in SIZES:
        frames[name] = sorted(order[offset : offset + size])
        offset += size
    assert sum(len(v) for v in frames.values()) == 2500
    assert len(set().union(*map(set, frames.values()))) == 2500
    assert not (set().union(*map(set, frames.values())) & excluded)

    payload = {
        "schema_version": 1,
        "seed": SEED,
        "universe": 10570,
        "excluded_unique": 1200,
        "pool": 9370,
        "frames": {
            name: {"n": len(qids), "sha256": _sha(qids), "qids": qids}
            for name, qids in frames.items()
        },
    }
    out = ROOT / "data" / "processed" / "qc_frames.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for name, qids in frames.items():
        print(f"{name}: n={len(qids)} sha={_sha(qids)[:16]}...")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
