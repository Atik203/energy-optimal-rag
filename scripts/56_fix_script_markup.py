"""Rewrite the Q&A section markup in the presentation script to a safe macro."""

from __future__ import annotations

import re
from pathlib import Path

p = Path("docs/PRESENTATION_SCRIPT.tex")
t = p.read_text(encoding="utf-8")

# 1) replace the macro definition with a self-contained, list-free version
old_macro = r"""\newcommand{\qa}[2]{%
  \item[\textbf{Q.}] \textbf{#1}\par
  \vspace{2pt}
  \hspace*{1.1em}\begin{minipage}[t]{0.93\linewidth}
  \color{ink}\small #2
  \end{minipage}
}"""
new_macro = r"""\newcommand{\qa}[2]{%
  \par\vspace{8pt}%
  \noindent\textbf{Q.}\enspace #1\par\vspace{3pt}%
  \noindent\hspace*{1.3em}\begin{minipage}[t]{0.90\linewidth}\color{ink}#2\end{minipage}\par
}"""
assert old_macro in t, "macro not found"
t = t.replace(old_macro, new_macro)

# 2) Member 1 block: \qa{question} followed by an answer paragraph
block1_old = r"""\begin{list}{}{\setlength{\leftmargin}{1.4em}\setlength{\itemsep}{10pt}}
\qa{Why these numbers: one thousand questions and seven depths?}
One thousand gives a usable estimate of accuracy near the plateau, and seven depths cover the useful range from no context to the retriever's limit. Seven depths also let us fit the energy curve with enough points.

\qa{Why only one dataset and one GPU?}
We chose depth of measurement over breadth, because the same questions had to be run on the same machine. That gives a clean comparison, but we state it as a limit, not as a general result.

\qa{Why this model, and why four-bit?}
A four-billion-parameter model at four-bit fits in six gigabytes of laptop memory, which is the hardware we had. It is a realistic deployment setting for a small team.

\qa{What does ``energy per correct answer'' actually mean?}
It answers the budget question: if I have to produce correct answers, how many joules does one correct answer cost. It is total energy divided by total correct answers.
\end{list}"""
block1_new = r"""\qa{Why these numbers: one thousand questions and seven depths?}{One thousand gives a usable estimate of accuracy near the plateau, and seven depths cover the useful range from no context to the retriever's limit. Seven depths also let us fit the energy curve with enough points.}

\qa{Why only one dataset and one GPU?}{We chose depth of measurement over breadth, because the same questions had to be run on the same machine. That gives a clean comparison, but we state it as a limit, not as a general result.}

\qa{Why this model, and why four-bit?}{A four-billion-parameter model at four-bit fits in six gigabytes of laptop memory, which is the hardware we had. It is a realistic deployment setting for a small team.}

\qa{What does ``energy per correct answer'' actually mean?}{It answers the budget question: if I have to produce correct answers, how many joules does one correct answer cost. It is total energy divided by total correct answers.}"""
assert block1_old in t, "member 1 Q&A block not found"
t = t.replace(block1_old, block1_new)

# 3) Members 2-5: \begin{qa}{q} ... \end{list}  ->  \qa{q}{...}
pattern = re.compile(r"\\begin\{qa\}\{(.*?)\}\s*(.*?)\n\\end\{list\}", re.S)


def repl(m: re.Match) -> str:
    q = m.group(1).strip()
    a = " ".join(m.group(2).split())
    return r"\qa{" + q + "}{" + a + "}"


t, n = pattern.subn(repl, t)
print("converted blocks:", n)

p.write_text(t, encoding="utf-8")
print("rewritten")
