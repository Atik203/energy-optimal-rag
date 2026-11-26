"""Keep short lead-in lines with their code blocks."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

pairs = [
    ("Test it:\n", "\\needspace{5\\baselineskip}\nTest it:\n"),
    ("Typical session:\n", "\\needspace{6\\baselineskip}\nTypical session:\n"),
]
for old, new in pairs:
    if old not in t:
        print("MISS:", old.strip())
    t = t.replace(old, new, 1)

if "\\usepackage{needspace}" not in t:
    t = t.replace("\\usepackage[hidelinks]{hyperref}", "\\usepackage{needspace}\n\\usepackage[hidelinks]{hyperref}")

p.write_text(t, encoding="utf-8")
print("pinned")
