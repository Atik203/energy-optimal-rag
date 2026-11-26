"""Insert a clean page break before the GPU-aware subsection."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

old = r"\subsection*{GPU-aware builds}"
new = "\\newpage\n" + old

if old not in t:
    raise SystemExit("anchor not found")
if "\\newpage\n" + old in t:
    raise SystemExit("break already present")

t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("break inserted")
