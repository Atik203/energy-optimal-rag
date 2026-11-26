"""One-off patch: fix overlaps in margin, R/Q and token figures."""

from __future__ import annotations

from pathlib import Path

p = Path("scripts/48_make_deck_figures.py")
t = p.read_text(encoding="utf-8")

# ---- margin: re-lay the labels so nothing crosses the limit line ----
old_margin = '''    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    ax.axvline(-5, color=FOREST, linestyle="--", linewidth=2.0)
    ax.text(-4.95, 0.66, "5 pp limit", fontsize=11, color=FOREST, rotation=90, va="top")
    ax.axvline(0, color=GRIDC, linewidth=1.4)
    ax.plot([lo, 0.0 if lo > 0 else 0.0], [1, 1], color=AMBER, linewidth=3.2, solid_capstyle="round")
    ax.plot(lo, 1, "o", color=AMBER, markersize=9)
    ax.plot(point, 1, "o", color=INK, markersize=11)
    ax.text(point + 0.18, 1.16, f"measured: {point:.2f} pp", fontsize=11, fontweight="bold", color=INK)
    ax.text(lo - 0.15, 0.62, "95% lower bound", fontsize=10, color=AMBER, ha="left")
    ax.text(lo - 0.15, 0.46, f"{lo:.2f} pp  (1.17 pp past the limit)", fontsize=10.5, color=AMBER, ha="left")
    ax.set_xlim(-10, 3)
    ax.set_ylim(0.3, 1.5)'''
new_margin = '''    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    ax.axvline(-5, color=FOREST, linestyle="--", linewidth=2.0)
    ax.axvline(0, color=GRIDC, linewidth=1.4)
    ax.plot([lo, point], [1, 1], color=AMBER, linewidth=3.4, solid_capstyle="round")
    ax.plot(lo, 1, "o", color=AMBER, markersize=9)
    ax.plot(point, 1, "o", color=INK, markersize=11)
    ax.text(-5, 1.44, "the 5 pp limit", fontsize=11, color=FOREST, ha="center", fontweight="bold")
    ax.text(point + 0.2, 1.10, f"measured {point:.2f} pp", fontsize=11, fontweight="bold", color=INK)
    ax.text(lo - 0.25, 0.80, f"95% lower bound {lo:.2f} pp", fontsize=10.5, color=AMBER, ha="left")
    ax.text(-9.7, 0.56, "the bound sits 1.17 pp past the limit, so the claim was not established",
            fontsize=10.5, color=MUTED, ha="left")
    ax.annotate("", xy=(lo, 1.0), xytext=(lo, 0.86), arrowprops=dict(arrowstyle="-", color=AMBER, linewidth=1.2))
    ax.set_xlim(-10, 3)
    ax.set_ylim(0.45, 1.60)'''
assert old_margin in t, "margin block not found"
t = t.replace(old_margin, new_margin)

# ---- rq: short tick labels, wider ylim ----
old_rq = '''    ax.set_xticks(list(x))
    ax.set_xticklabels(list(arms), fontsize=10)'''
new_rq = '''    ax.set_xticks(list(x))
    ax.set_xticklabels(["Qwen3.5-4B", "Qwen2.5-1.5B", "Llama-3.2-3B", "HotpotQA"], fontsize=10.5)
    ax.set_ylim(min(dq) - 4, max(dr) + 4)'''
assert old_rq in t, "rq ticks not found"
t = t.replace(old_rq, new_rq)
t = t.replace(
    'ax.set_title("Recall always rises; precision moves both ways and decides the sign", fontsize=11, color=MUTED, loc="left", pad=10)',
    'ax.set_xlabel("depth change k=4 to k=32 (HotpotQA: k=4 to k=10)", fontsize=10)\n'
    '    ax.set_title("Recall always rises; precision moves both ways and decides the sign", fontsize=11, color=MUTED, loc="left", pad=10)',
)

# ---- token: move the note off the fit line ----
t = t.replace(
    '''    ax.text(0.03, 0.10, "Measured points from the padding experiment are shown as dashed lines",
            transform=ax.transAxes, fontsize=9.5, color=MUTED)''',
    '''    ax.text(0.99, 0.03, "dashed lines = measured energy from the padding experiment",
            transform=ax.transAxes, fontsize=9.5, color=MUTED, ha="right")''',
)

p.write_text(t, encoding="utf-8")
print("patched")
