"""Point the figure generators at the consolidated Slides folder."""

from __future__ import annotations

from pathlib import Path

for name in ("scripts/48_make_deck_figures.py", "scripts/48b_render_deck_equations.py"):
    p = Path(name)
    t = p.read_text(encoding="utf-8")
    before = t
    t = t.replace('"ppt_slides" / "figures"', '"Slides" / "figures"')
    t = t.replace('"ppt_slides", "figures"', '"Slides", "figures"')
    if t == before:
        print(f"{name}: no path change needed or path not found")
    p.write_text(t, encoding="utf-8")
    print(f"{name}: patched")
