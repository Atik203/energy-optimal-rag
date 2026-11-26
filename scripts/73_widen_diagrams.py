"""Widen the sensor band and the rest gaps so labels do not collide."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/72_fix_diagrams.py")
t = p.read_text(encoding="utf-8")

t = t.replace("Rectangle((50.0, 31.0), 47.0, 8.0", "Rectangle((50.0, 31.0), 49.0, 8.0")
t = t.replace('ax.text(73.5, 35.0, "GPU power measured"', 'ax.text(74.5, 35.0, "GPU power measured"')
t = t.replace("n, gap = 5, 1.6", "n, gap = 5, 4.2")
t = t.replace('fontsize=9, color=MUTED)', 'fontsize=8, color=MUTED)')

p.write_text(t, encoding="utf-8")
print("patched")
