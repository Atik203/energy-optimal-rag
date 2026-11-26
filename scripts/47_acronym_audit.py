"""Check acronyms are expanded near first use."""

from __future__ import annotations

import re
from pathlib import Path

t = Path("paper/main.tex").read_text(encoding="utf-8")
body = t[t.find(r"\begin{document}") :]

CHECKS = [
    ("NVML", "NVIDIA"),
    ("BM25", "matching"),
    ("AUC", "area under"),
    ("ICC", "intraclass"),
    ("DiD", "difference-in-differences"),
    ("TOST", "equivalence"),
    ("CV", "coefficient of variation"),
]

for ac, hint in CHECKS:
    m = re.search(rf"\b{ac}\b", body)
    if not m:
        print(f"{ac:6s} not used")
        continue
    window = body[max(0, m.start() - 220) : m.start() + 260]
    ok = hint.lower() in window.lower()
    print(f"{ac:6s} first@{m.start():6d}  expanded_nearby={ok}  | {body[m.start():m.start()+70]!r}")
