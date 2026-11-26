"""One-off patch: block-timeline annotation and sweep caption clarity."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

old = '''    ax.annotate("", xy=(44, 21.6), xytext=(16, 21.6), arrowprops=dict(arrowstyle="<|-|>", color=AMBER, linewidth=1.5))
    ax.text(30, 23.2, "one integrated energy window per batch", ha="center", fontsize=10.5, color=AMBER, fontweight="bold")
    ax.text(50, 4.2, "Idle power is read from the tail of the rest period, so the GPU is already cool and steady", ha="center", fontsize=10, color=MUTED)
    ax.text(2, 24.6, "Randomized order, one depth per batch, fixed rest between batches", fontsize=11.5, color=INK, fontweight="bold")'''

new = '''    ax.annotate("", xy=(4, 18.6), xytext=(16, 18.6), arrowprops=dict(arrowstyle="<|-|>", color=AMBER, linewidth=1.6))
    ax.text(10, 19.4, "one energy window per batch", ha="center", fontsize=10.5, color=AMBER, fontweight="bold")
    ax.text(50, 4.2, "Idle power is read from the tail of the rest period, so the GPU is already cool and steady", ha="center", fontsize=10, color=MUTED)
    ax.text(50, 24.4, "Randomized order, one depth per batch, fixed rest between batches",
            ha="center", fontsize=11.5, color=INK, fontweight="bold")'''

if old not in t:
    raise SystemExit("timeline block not found")
t = t.replace(old, new)

t = t.replace(
    'ax.set_title("Each row is one question. Shading = order it was run.", fontsize=11.5, color=MUTED, pad=10, loc="left")',
    'ax.set_title("Each row is one question. The number is the run order (1 = first).", fontsize=11.5, color=MUTED, pad=10, loc="left")',
)
t = t.replace(
    'ax.set_title("Each row is one question. Shading = order it was run.", fontsize=11.5, color=MUTED, pad=10, loc="left")',
    'ax.set_title("Each row is one question. The number is the run order (1 = first).", fontsize=11.5, color=MUTED, pad=10, loc="left")',
)

p.write_text(t, encoding="utf-8")
print("patched")
