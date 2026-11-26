"""One-off patch: keep the margin figure labels clear of the limit line."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

pairs = [
    (
        'ax.text(-5, 1.44, "the 5 pp limit", fontsize=11, color=FOREST, ha="center", fontweight="bold")',
        'ax.text(-5.25, 1.44, "the 5 pp limit", fontsize=11, color=FOREST, ha="right", fontweight="bold")',
    ),
    (
        '''    ax.text(-9.7, 0.56, "the bound sits 1.17 pp past the limit, so the claim was not established",
            fontsize=10.5, color=MUTED, ha="left")''',
        '''    ax.text(-9.7, 0.62, "the lower bound sits 1.17 pp past the limit,",
            fontsize=10.5, color=MUTED, ha="left")
    ax.text(-9.7, 0.50, "so the claim was not established",
            fontsize=10.5, color=MUTED, ha="left")''',
    ),
    (
        '''    ax.text(lo - 0.25, 0.80, f"95% lower bound {lo:.2f} pp", fontsize=10.5, color=AMBER, ha="left")''',
        '''    ax.text(lo - 0.25, 0.86, f"95% lower bound {lo:.2f} pp", fontsize=10.5, color=AMBER, ha="right")''',
    ),
]

for old, new in pairs:
    if old in t:
        t = t.replace(old, new)
    else:
        print("NOT FOUND:", old[:60])

p.write_text(t, encoding="utf-8")
print("patched")
