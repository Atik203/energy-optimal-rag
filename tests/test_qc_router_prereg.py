"""Tests for the qc-router prereg draft (Task 1, CPU only)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_router_prereg_schema():
    text = (ROOT / "prereg" / "qc_router_prereg.md").read_text(encoding="utf-8")
    assert "H-route" in text
    assert "qc_router_eval" in text
    assert "allow_abstention=False" in text
    assert "prereg-qc-router-v1" in text
    # max-reuse roles pinned
    assert "p1_primary" in text
    assert "qc_fresh" in text
    # fixed-cost rule guards the 7.21% artifact
    assert "fixed" in text.lower()
    assert "Per-query windows" in text or "per-query windows" in text
