"""Fix the tilde inside \\cmd{}, keep the Task Spooler heading with its block, tidy a tip."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

# 1) `~` is a non-breaking space inside \cmd{...}; use \textasciitilde so paths render correctly
count = t.count(r"\cmd{~")
t = t.replace(r"\cmd{~", r"\cmd{\textasciitilde")
print(f"tilde paths fixed: {count}")

# 2) keep the Task Spooler heading and its first block together
old = r"\section{Jobs: Task Spooler}"
new = "\\needspace{12\\baselineskip}\n" + old
if old not in t:
    raise SystemExit("Task Spooler section not found")
t = t.replace(old, new, 1)

# 3) tidy the closing tip
old_tip = (
    "\\textbf{Before you log off:} stop forgotten jobs (\\cmd{ts}), activate nothing else is running\n"
    "(\\cmd{nvidia-smi}), and download your results."
)
new_tip = (
    "\\textbf{Before you log off:} stop forgotten jobs (\\cmd{ts}), check that nothing of yours is\n"
    "still running (\\cmd{nvidia-smi}), and download your results."
)
if old_tip in t:
    t = t.replace(old_tip, new_tip)
else:
    print("MISS: closing tip")

p.write_text(t, encoding="utf-8")
print("patched")
