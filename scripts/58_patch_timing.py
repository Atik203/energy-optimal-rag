"""Patch the timing checker to stop at the end of member 5's spoken block."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/57_speech_timing.py")
t = p.read_text(encoding="utf-8")

old = '    body = body.split("Handover")[0]'
new = (
    '    body = body.split("Handover")[0]\n'
    '    body = body.split(r"\\newpage")[0]\n'
    '    body = body.split(r"\\section")[0]'
)

if old not in t:
    raise SystemExit("anchor not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched")
