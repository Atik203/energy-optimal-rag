"""Trim a few lines so the guide closes on page 3 without an orphaned heading."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

# shorten the cheat sheet by three lines
for line in (
    "pwd                 # where am I\n",
    "cp a.csv b.csv      # copy\n",
    "cat log.txt         # show a whole file\n",
):
    if line not in t:
        print("MISS:", line.strip())
    t = t.replace(line, "")

# merge two troubleshooting rows into one
old_rows = (
    "VS Code asks for a password twice & choose \\emph{Linux} as the remote platform, then reconnect \\\\\n"
    "\\cmd{No space left on device} & check \\cmd{df -h}, delete old checkpoints, download results and remove them \\\\\n"
)
new_rows = (
    "\\cmd{No space left on device} & check \\cmd{df -h}, delete old checkpoints, download results and remove them \\\\\n"
)
if old_rows not in t:
    print("MISS: troubleshooting rows")
t = t.replace(old_rows, new_rows)

p.write_text(t, encoding="utf-8")
print("trimmed")
