"""Check speaking time per member at 100 words per minute."""

from __future__ import annotations

import re
from pathlib import Path

t = Path("docs/PRESENTATION_SCRIPT.tex").read_text(encoding="utf-8")

# take only the spoken sections, between \section{Member and the handover note
sections = re.split(r"\\section\{Member (\d)", t)
WPM = 100

print(f"{'member':8s} {'words':>6s} {'seconds':>8s} {'minutes':>8s}")
print("-" * 36)
total = 0
for i in range(1, len(sections), 2):
    num = sections[i]
    body = sections[i + 1]
    # cut at the handover line
    body = body.split("Handover")[0]
    body = body.split(r"\newpage")[0]
    body = body.split(r"\section")[0]
    # strip latex commands
    body = re.sub(r"\\slideref\{[^}]*\}", " ", body)
    body = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", body)
    body = re.sub(r"[{}$\\~]", " ", body)
    words = [w for w in body.split() if re.search(r"[A-Za-z0-9]", w)]
    n = len(words)
    total += n
    print(f"{num:8s} {n:6d} {n / WPM * 60:8.0f} {n / WPM:8.2f}")

print("-" * 36)
print(f"{'total':8s} {total:6d} {total / WPM * 60:8.0f} {total / WPM:8.2f}")
print(f"\nplus slide changes and pauses: about {(8.0 - total / WPM) * 60:.0f} s of the 8 minute budget")
