"""Sync the placeholder constants in the private-build script."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/84_build_private_guide.py")
t = p.read_text(encoding="utf-8")

pairs = [
    ('PLACEHOLDER_INTERNAL = "10.100.110.110"', 'PLACEHOLDER_INTERNAL = "10.0.0.50"'),
    ('PLACEHOLDER_GLOBAL = "100.100.52.109"', 'PLACEHOLDER_GLOBAL = "203.0.113.10"'),
]
for old, new in pairs:
    if old not in t:
        print("MISS:", old)
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("synced")
