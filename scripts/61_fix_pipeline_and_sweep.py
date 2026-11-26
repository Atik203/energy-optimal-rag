"""Patch: keep the NVML label inside its box, and enlarge the sweep figure."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

old_pipe = '''    ax.add_patch(Rectangle((60.5, 2.0), 22, 6.6, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.4))
    ax.text(71.5, 6.7, "NVML power sensor", ha="center", va="center", fontsize=10, fontweight="bold", color=FOREST)
    ax.text(71.5, 4.3, "samples every 100 ms", ha="center", va="center", fontsize=9, color=MUTED)'''

new_pipe = '''    ax.add_patch(Rectangle((54.0, 1.8), 35, 7.4, facecolor="#EEF5F1", edgecolor=TEAL, linewidth=1.4))
    ax.text(71.5, 7.4, "NVML power sensor", ha="center", va="center", fontsize=9.5, fontweight="bold", color=FOREST)
    ax.text(71.5, 4.6, "one reading every 100 ms", ha="center", va="center", fontsize=8.5, color=MUTED)'''

if old_pipe not in t:
    raise SystemExit("pipeline block not found")
t = t.replace(old_pipe, new_pipe)

# sweep figure: a little more vertical room so labels breathe
t = t.replace("fig, ax = plt.subplots(figsize=(7.4, 4.6))", "fig, ax = plt.subplots(figsize=(7.8, 4.9))")

p.write_text(t, encoding="utf-8")
print("patched")
