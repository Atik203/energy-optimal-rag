"""Compress to three pages and drop the troubleshooting table."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

# --- tighter page and line spacing ---------------------------------------
t = t.replace("[margin=1.45cm,top=1.1cm,bottom=1.1cm]{geometry}",
              "[margin=1.4cm,top=0.9cm,bottom=0.9cm]{geometry}")
t = t.replace("\\linespread{1.04}", "\\linespread{1.0}")
t = t.replace("\\titlespacing*{\\section}{0pt}{9pt}{5pt}",
              "\\titlespacing*{\\section}{0pt}{7pt}{3pt}")
t = t.replace("\\vspace{-7pt}\\noindent", "\\vspace{-8pt}\\noindent")
t = t.replace("leftrule=3.5pt, left=10pt, right=10pt, top=4pt, bottom=4pt,",
              "leftrule=3.5pt, left=10pt, right=10pt, top=3pt, bottom=3pt,")
t = t.replace("before skip=4pt, after skip=4pt,", "before skip=3pt, after skip=3pt,")

# --- the numbered steps duplicate the comments in the code ----------------
old_steps = r"""This is the whole routine. Do it in this order.

\begin{enumerate}[leftmargin=1.3em,itemsep=1pt,topsep=1pt]
  \item On your laptop, send the code up.
  \item On the server, make an environment and install.
  \item Check the GPU is free, then queue the job.
  \item Watch it, then bring the results back.
\end{enumerate}

"""
if old_steps in t:
    t = t.replace(old_steps, "The whole routine, in order.\n\n")
else:
    print("MISS: step list")

# --- drop the whole troubleshooting table ---------------------------------
start = t.find("\\textbf{If something goes wrong.}")
if start == -1:
    raise SystemExit("troubleshooting block not found")
end = t.find("\\end{tabularx}", start)
if end == -1:
    raise SystemExit("tabularx end not found")
t = t[:start] + t[end + len("\\end{tabularx}") + 2 :]

p.write_text(t, encoding="utf-8")
print("compressed, troubleshooting removed")
