"""Merge the last three sections into one short closing section."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/GPU_Server_Guide.tex")
t = p.read_text(encoding="utf-8")

marker = "\\Needspace{12\\baselineskip}"
i = t.find(marker)
if i == -1:
    raise SystemExit("marker not found")

tail = r"""\section{Final notes: rules, fixes, handy commands}

\begin{warnbox}
\begin{itemize}[leftmargin=1.1em,itemsep=0pt,topsep=0pt]
  \item Avoid installing unnecessary software packages.
  \item Back up all necessary data every day.
  \item Do not share your user credentials with anyone.
  \item The server is monitored at all times by UIU CITS.
\end{itemize}
\end{warnbox}

\textbf{If something goes wrong.}

\begin{tabularx}{\linewidth}{@{}>{\ttfamily\small}lX@{}}
\toprule
\rowcolor{rose!10} Message & What to do \\
\midrule
ssh not recognised & the Windows SSH client is missing; install OpenSSH Client (section 2) \\
Permission denied & wrong account name, or your key is not on the server; ask the administrator \\
Connection timed out & you are outside the campus network; use \cmd{uiu-gpu-outside} or \cmd{-p 110} \\
\cmd{uiu-gpu} unknown & the \cmd{config} file is missing, called \cmd{config.txt}, or in the wrong folder (section 3) \\
No space left & check \cmd{df -h}, delete old checkpoints, download results and remove them \\
CUDA out of memory & another job holds the GPU, or the batch is too large; check \cmd{nvidia-smi} \\
\bottomrule
\end{tabularx}

\textbf{Commands you will need on the server.}

\begin{srvblock}
ls -lh              # list files with sizes
cd ~/work           # change folder
mkdir results       # make a folder
mv old new          # rename or move
rm old.csv          # delete a file (no undo)
less log.txt        # scroll a file, q to quit
tail -f log.txt     # watch a file grow, Ctrl+C to stop
nano notes.txt      # editor: Ctrl+O save, Ctrl+X exit
\end{srvblock}

\begin{tipbox}
\textbf{Before you log off:} check for jobs you forgot with \cmd{ts}, download anything worth
keeping, and free space with \cmd{df -h} if you are near the 200 GB limit.
\end{tipbox}

\end{document}
"""

t = t[:i] + tail
p.write_text(t, encoding="utf-8")
print("merged closing section")
