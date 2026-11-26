"""39 - Generate the qc-router eval frame deterministically (CPU only).

Extends the Phase 8 pool without re-randomizing: reloads the same 9,370-qid
pool (universe minus p0/p1 1,200), reshuffles with the same seed 20261115,
verifies the first 2,500 match the frozen qc_fresh/distractor/dense frames,
then takes the next 1,000 as qc_router_eval (sorted qids + sha256).

Writes data/splits/qc_frames.json (tracked source of truth). Run outputs
also merge the frame into the local data/processed/squad_splits.json, which
is what the loader reads. No GPU, no network, no reader.
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
EVAL_SIZE = 1000
EVAL_OFFSET = 2500


def _sha(items: list[str]) -> str:
    return hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()


def main() -> int:
    import pandas as pd

    questions = pd.read_parquet(ROOT / "data" / "processed" / "squad_questions.parquet")
    universe = [str(q) for q in questions["qid"]]
    assert len(universe) == 10570, f"expected 10570 dev qids, got {len(universe)}"

    splits = json.loads(
        (ROOT / "data" / "processed" / "squad_splits.json").read_text(encoding="utf-8")
    )["splits"]
    excluded = set(splits["p0_golden"]) | set(splits["p1_primary"])
    assert len(excluded) == 1200, f"expected 1200 unique excluded, got {len(excluded)}"
    pool = [q for q in universe if q not in excluded]
    assert len(pool) == 9370, f"expected 9370 fresh, got {len(pool)}"

    rng = random.Random(SEED)
    order = list(pool)
    rng.shuffle(order)

    tracked_path = ROOT / "data" / "splits" / "qc_frames.json"
    tracked = json.loads(tracked_path.read_text(encoding="utf-8"))
    frames = tracked["frames"]
    assert set(frames) == {"qc_fresh", "qc_distractor", "qc_dense"}, (
        f"unexpected frames {set(frames)}"
    )
    # Verify the frozen prefix reproduces exactly (same seed, same pool, plan order).
    expected = {
        "qc_fresh": (0, 1000),
        "qc_distractor": (1000, 500),
        "qc_dense": (1500, 1000),
    }
    for name, (off, size) in expected.items():
        got = sorted(order[off : off + size])
        assert got == frames[name]["qids"], f"{name} prefix mismatch — pool or seed drifted"
        assert _sha(got) == frames[name]["sha256"], f"{name} hash mismatch"

    eval_qids = sorted(order[EVAL_OFFSET : EVAL_OFFSET + EVAL_SIZE])
    assert len(eval_qids) == EVAL_SIZE
    assert not (set(eval_qids) & set().union(*[set(frames[n]["qids"]) for n in frames]))
    assert not (set(eval_qids) & excluded)

    frames["qc_router_eval"] = {"n": len(eval_qids), "sha256": _sha(eval_qids), "qids": eval_qids}
    tracked["frames"] = frames
    tracked_path.write_text(json.dumps(tracked, indent=2), encoding="utf-8")
    print(f"qc_router_eval: n={len(eval_qids)} sha={_sha(eval_qids)[:16]}...")
    print(f"wrote {tracked_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
