"""Fix overfull/underfull lines and strengthen the colour scheme."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

# ---- colour: lime accent, teal number chips, stronger tints --------------
t = t.replace("\\definecolor{teal}{HTML}{0F766E}",
              "\\definecolor{teal}{HTML}{0F766E}\n\\definecolor{lime}{HTML}{C8F04F}")

t = t.replace(
    "\\newtcolorbox{titleband}{colback=forest, colframe=forest, boxrule=0pt, arc=4pt,\n"
    "  left=12pt, right=12pt, top=9pt, bottom=9pt, halign=center}",
    "\\newtcolorbox{titleband}{colback=forest, colframe=forest, boxrule=0pt, arc=4pt,\n"
    "  left=12pt, right=12pt, top=9pt, bottom=9pt, halign=center,\n"
    "  borderline south={3pt}{0pt}{lime}}",
)

# section numbers become teal chips with white digits
t = t.replace(
    "\\titleformat{\\section}\n"
    "  {\\large\\bfseries\\color{forest}}{\\textcolor{teal}{\\thesection}}{0.5em}{}",
    "\\titleformat{\\section}\n"
    "  {\\large\\bfseries\\color{forest}}\n"
    "  {\\colorbox{teal}{\\textcolor{white}{\\,\\thesection\\,}}}{0.6em}{}",
)

# slightly stronger table and chip tints so they survive printing
t = t.replace("\\rowcolor{forest!10}", "\\rowcolor{forest!16}")
t = t.replace("\\rowcolor{rose!10}", "\\rowcolor{rose!16}")
t = t.replace("\\colorbox{amber!20}", "\\colorbox{amber!26}")
t = t.replace("\\colorbox{forest!20}", "\\colorbox{forest!26}")
t = t.replace("{\\color{forest!30}\\rule", "{\\color{teal!55}\\rule")

# ---- fix the overfull line: show the example as a block ------------------
old = (
    "Without the short name, add the port with a capital \\cmd{-P}:\n"
    "\\texttt{\\small scp -P 110 file username@203.0.113.10:\\textasciitilde/work/}.\n"
    "Manual: \\url{https://man.openbsd.org/scp}\n"
)
new = (
    "Without the short name, add the port with a capital \\cmd{-P}:\n\n"
    "\\begin{winblock}\n"
    "scp -P 110 .\\train.py username@203.0.113.10:~/work/\n"
    "\\end{winblock}\n\n"
    "Manual: \\url{https://man.openbsd.org/scp}\n"
)
if old not in t:
    print("MISS: scp manual line")
t = t.replace(old, new)

# ---- fix the underfull box: URLs set ragged right ------------------------
old_more = (
    "\\begin{tipbox}\n"
    "More: \\url{https://justanhduc.github.io/2021/02/03/Task-Spooler.html} and\n"
    "\\url{https://github.com/justanhduc/task-spooler}\n"
    "\\end{tipbox}"
)
new_more = (
    "\\begin{tipbox}\n"
    "\\raggedright More: \\url{https://justanhduc.github.io/2021/02/03/Task-Spooler.html} and\n"
    "\\url{https://github.com/justanhduc/task-spooler}\\par\n"
    "\\end{tipbox}"
)
if old_more not in t:
    print("MISS: more tipbox")
t = t.replace(old_more, new_more)

p.write_text(t, encoding="utf-8")
print("colours and spacing patched")
