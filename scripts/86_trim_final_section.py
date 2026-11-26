"""Drop the Linux cheat-sheet section and un-number the closing notes."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

# 1) stale cross-references after the nvidia-smi section was removed
t = t.replace("(section 4) to work with files", "(section 5) to work with files")
t = t.replace("(section 6) so the shared GPU stays free", "(section 7) so the shared GPU stays free")

# 2) replace the numbered final section with an unnumbered closing block, no Linux cheat sheet
start = t.find("\\section{Final notes}")
end = t.find("\\end{document}")
if start == -1 or end == -1:
    raise SystemExit("final section not found")

closing = r"""\begin{tipbox}
\textbf{Rules.} No unnecessary software \textperiodcentered\ back up your data daily \textperiodcentered\
never share your credentials \textperiodcentered\ the server is monitored by UIU CITS.
\end{tipbox}

\textbf{If something goes wrong.}

\begin{tabularx}{\linewidth}{@{}>{\ttfamily\small}lX@{}}
\toprule
\rowcolor{rose!10} Message & What to do \\
\midrule
ssh not recognised & install OpenSSH Client (section 2) \\
Permission denied & wrong account name, or your key is missing; ask the administrator \\
Connection timed out & outside campus; use \cmd{uiu-gpu-outside} \\
\cmd{uiu-gpu} unknown & \cmd{config} missing, named \cmd{config.txt}, or in the wrong folder \\
No space left & \cmd{df -h}, delete checkpoints, download results \\
CUDA out of memory & another job holds the GPU, or the batch is too large \\
\bottomrule
\end{tabularx}

\begin{tipbox}
\textbf{Before you log off:} stop forgotten jobs (\cmd{ts}), check that nothing of yours is
still running (\cmd{nvidia-smi}), and download your results.
\end{tipbox}

"""

t = t[:start] + closing + t[end:]
p.write_text(t, encoding="utf-8")
print("closing block rewritten")
