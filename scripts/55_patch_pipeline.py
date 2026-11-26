"""One-off patch: pipeline figure without internal title, wider sensor box."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

old = '''    ax.add_patch(Rectangle((64, 2.2), 15, 6.2, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.4))
    ax.text(71.5, 6.6, "NVML power sensor", ha="center", va="center", fontsize=10, fontweight="bold", color=FOREST)
    ax.text(71.5, 4.2, "samples every 100 ms", ha="center", va="center", fontsize=9, color=MUTED)
    ax.annotate("", xy=(71.5, 11.8), xytext=(71.5, 8.6), arrowprops=dict(arrowstyle="-|>", color=TEAL, linewidth=1.4))
    ax.text(50, 27.4, "Where the joules are spent: the reader, not the search", ha="center", fontsize=12.5, color=INK, fontweight="bold")'''

new = '''    ax.add_patch(Rectangle((60.5, 2.0), 22, 6.6, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.4))
    ax.text(71.5, 6.7, "NVML power sensor", ha="center", va="center", fontsize=10, fontweight="bold", color=FOREST)
    ax.text(71.5, 4.3, "samples every 100 ms", ha="center", va="center", fontsize=9, color=MUTED)
    ax.annotate("", xy=(71.5, 11.8), xytext=(71.5, 8.8), arrowprops=dict(arrowstyle="-|>", color=TEAL, linewidth=1.4))'''

if old not in t:
    raise SystemExit("pipeline block not found")
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("patched")
