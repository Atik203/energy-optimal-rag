"""Strengthen the colour blocks in the GPU server guide."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

pairs = [
    (r"backgroundcolor=\color{amber!7}", r"backgroundcolor=\color{amber!16}"),
    (r"rulecolor=\color{amber!45}", r"rulecolor=\color{amber!80}"),
    (r"backgroundcolor=\color{forest!7}", r"backgroundcolor=\color{forest!16}"),
    (r"rulecolor=\color{forest!45}", r"rulecolor=\color{forest!80}"),
]

for old, new in pairs:
    if old not in t:
        print("MISS:", old)
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("tints raised")
