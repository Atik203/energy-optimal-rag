"""Drop the reader list from the pipeline figure; the slide table now carries it."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/65_redraw_pipeline.py")
t = p.read_text(encoding="utf-8")

start = t.find('    # readers')
end = t.find('    fig.savefig(')
if start == -1 or end == -1:
    raise SystemExit("anchors not found")

replacement = (
    '    ax.text(1.5, 8.8, "one question at seven depths, all on one GPU", fontsize=9.5, color=MUTED)\n\n'
)

t = t[:start] + replacement + t[end:]
p.write_text(t, encoding="utf-8")
print("removed reader list")
