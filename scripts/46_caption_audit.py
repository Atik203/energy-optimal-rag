"""Audit caption lengths (skill: concise 1-2 line captions)."""

from __future__ import annotations

import re
from pathlib import Path

t = Path("paper/main.tex").read_text(encoding="utf-8")
for m in re.finditer(r"\\caption\{", t):
    start = m.end() - 1
    depth = 0
    i = start
    while i < len(t):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    cap = t[start + 1 : i]
    print(f"{len(cap):4d} chars ~{len(cap) / 110:.1f} lines | {cap[:60]}")
