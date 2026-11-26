"""One-off patch: widen the window-vs-block panels and lift labels off the trace."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

pairs = [
    ("ax.set_ylim(0, 9)", "ax.set_ylim(0, 11)"),
    ("b - a, 9, facecolor=AMBER", "b - a, 7.6, facecolor=AMBER"),
    ('b - a, 9, facecolor="white"', 'b - a, 7.6, facecolor="white"'),
    ("3.1, 9, facecolor=TEAL", "3.1, 7.6, facecolor=TEAL"),
    ('ax.text(5.9, 7.4, "gaps are never measured"', 'ax.text(5.9, 9.9, "gaps are never measured"'),
    ('ax.annotate("", xy=(2.7, 6.4), xytext=(5.6, 7.1),', 'ax.annotate("", xy=(2.7, 6.4), xytext=(5.6, 9.3),'),
    ('ax.text(5.9, 7.4, "one integral covers the whole span"', 'ax.text(5.9, 9.9, "one integral covers the whole span"'),
    ('ax.annotate("", xy=(3.6, 6.4), xytext=(5.6, 7.1),', 'ax.annotate("", xy=(3.6, 6.4), xytext=(5.6, 9.3),'),
]
for old, new in pairs:
    if old in t:
        t = t.replace(old, new)
    else:
        print("not found:", old[:50])

p.write_text(t, encoding="utf-8")
print("patched")
