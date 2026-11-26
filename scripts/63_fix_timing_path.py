"""Point the timing checker at the consolidated Slides folder."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/57_speech_timing.py")
t = p.read_text(encoding="utf-8")
t = t.replace('Path("docs/PRESENTATION_SCRIPT.tex")', 'Path("Slides/Presentation_Script_and_QA.tex")')
p.write_text(t, encoding="utf-8")
print("patched path")
