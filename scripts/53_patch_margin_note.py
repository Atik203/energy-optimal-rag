"""One-off patch: split the margin note into three short lines."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

old = '''    ax.text(-9.7, 0.62, "the lower bound sits 1.17 pp past the limit,",
            fontsize=10.5, color=MUTED, ha="left")
    ax.text(-9.7, 0.50, "so the claim was not established",
            fontsize=10.5, color=MUTED, ha="left")'''

new = '''    ax.text(-9.7, 0.66, "the lower bound sits 1.17 pp", fontsize=10.5, color=MUTED, ha="left")
    ax.text(-9.7, 0.55, "past the limit, so the claim", fontsize=10.5, color=MUTED, ha="left")
    ax.text(-9.7, 0.44, "was not established", fontsize=10.5, color=MUTED, ha="left")'''

if old not in t:
    raise SystemExit("margin note block not found")

t = t.replace(old, new).replace("ax.set_ylim(0.45, 1.60)", "ax.set_ylim(0.38, 1.60)")
p.write_text(t, encoding="utf-8")
print("patched")
