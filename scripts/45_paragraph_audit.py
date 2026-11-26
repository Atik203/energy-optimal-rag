"""Audit paper prose paragraph lengths (skill: avoid 1-2 sentence stubs)."""

from __future__ import annotations

import re
from pathlib import Path

t = Path("paper/main.tex").read_text(encoding="utf-8")
b = t[t.find(r"\begin{document}") :]

# Split on blank lines; drop float/table/figure blocks and pure markup.
paras = []
cur = []
depth = 0
for line in b.splitlines():
    stripped = line.strip()
    if re.match(r"\\(begin|end)\{(table|figure|tabular|abstract|keywords|equation|align)", stripped):
        if stripped.startswith(r"\begin"):
            depth += 1
        else:
            depth = max(0, depth - 1)
        continue
    if depth:
        continue
    if not stripped:
        if cur:
            paras.append(" ".join(cur))
            cur = []
        continue
    if stripped.startswith(("\\section", "\\subsection", "\\item", "\\caption", "\\label")):
        if cur:
            paras.append(" ".join(cur))
            cur = []
        continue
    cur.append(stripped)
if cur:
    paras.append(" ".join(cur))

clean = []
for p in paras:
    txt = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", p)
    txt = re.sub(r"[$\\{}~]", " ", txt)
    words = [w for w in txt.split() if re.search(r"[A-Za-z]", w)]
    if len(words) > 3:
        clean.append((len(words), p[:70]))

print(f"prose paragraphs: {len(clean)}")
short = [x for x in clean if x[0] < 40]
print(f"under 40 words: {len(short)}")
for w, s in short:
    print(f"  {w:3d}  {s}")
