"""One-off patch: fix label collisions in the savings forest and drift plots."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

pairs = [
    # savings forest: lift the floor label above the axis text
    (
        'ax.text(21, 0.62, "20% floor", fontsize=10, color=FOREST)',
        'ax.text(20.8, len(labels) + 0.45, "20% floor", fontsize=10, color=FOREST, va="center")',
    ),
    ('    ax.set_xlim(10, 92)', '    ax.set_xlim(10, 92)\n    ax.set_ylim(0.4, len(labels) + 0.85)'),
    # drift: drop the in-figure title and move the reference label off the line
    (
        'ax.text(1.1, 1.008, "same energy as the batch design", fontsize=9.5, color=MUTED)',
        'ax.text(9.9, 1.004, "same energy as the batch design", fontsize=9.5, color=MUTED, ha="right", va="bottom")',
    ),
    (
        '    ax.set_title("Ten replays fall by about 15% as the GPU heats; the batch design does not move", fontsize=11, color=MUTED, loc="left", pad=10)\n',
        "    ax.set_ylim(min(ratios) - 0.035, max(ratios) + 0.055)\n",
    ),
]

for old, new in pairs:
    if old in t:
        t = t.replace(old, new)
    else:
        print("NOT FOUND:", old[:60])

p.write_text(t, encoding="utf-8")
print("patched")
