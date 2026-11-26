"""Tests for the qc-router eval frame (Task 2, CPU only)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_router_frame_disjoint():
    path = ROOT / "data" / "splits" / "qc_frames.json"
    assert path.is_file(), "qc_frames.json missing"
    frames = json.loads(path.read_text(encoding="utf-8"))["frames"]
    assert "qc_router_eval" in frames, "qc_router_eval not yet generated"
    assert frames["qc_router_eval"]["n"] == 1000
    qids = frames["qc_router_eval"]["qids"]
    assert len(qids) == 1000 and len(set(qids)) == 1000
    assert qids == sorted(qids)
    import hashlib

    assert (
        hashlib.sha256("\n".join(qids).encode()).hexdigest() == frames["qc_router_eval"]["sha256"]
    )
    others = set()
    for name in ("qc_fresh", "qc_distractor", "qc_dense"):
        others |= set(frames[name]["qids"])
    assert not (set(qids) & others), "eval frame overlaps existing qc frames"
