"""Re-map the speaker script to two main slides per member (12 = thank you)."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/Presentation_Script_and_QA.tex")
t = p.read_text(encoding="utf-8")

old_m4 = r"""\section{Member 4 \textnormal{\small --- slides 8 to 10, decision and cause}}

\slideref{slide 8} Thank you. I will explain the decision rule and the tests.

A smaller depth counts as good only if it does both. It must save at least twenty percent of the energy, and it must lose at most five accuracy points.

At k equals four, the accuracy loss was four point three points. That is inside the limit. But the lower bound of our confidence interval was minus six point one seven, which is outside it. So the saving condition was met, and the accuracy condition was not. We report that honestly.

\slideref{slide 9} Before the runs, we wrote three plans, hashed them, and tagged them, so the rules could not move after we saw the numbers. Five tests fired, and one finished.

\slideref{slide 10} Then we asked why. Recall always rises with depth. Precision moves both ways, and it decides the sign. When we hold the correct passage first, adding distractors actually helps.

\vspace{6pt}
{\small\color{muted}\textbf{Handover:} ``Thank you. My teammate will finish with the cause and the limits.''}"""

new_m4 = r"""\section{Member 4 \textnormal{\small --- slides 8 and 9, decision and fixed rules}}

\slideref{slide 8} Thank you. I will explain the decision rule.

A smaller depth counts as good only if it does both. It must save at least twenty percent of the energy, and it must lose at most five accuracy points.

At k equals four, the accuracy loss was four point three points. That is inside the limit. But the lower bound of our confidence interval was minus six point one seven, which is outside it. So the saving condition was met, and the accuracy condition was not. We report that honestly.

\slideref{slide 9} Before the runs, we wrote three plans, hashed them, and tagged them, so the rules could not move after we saw the numbers. Five tests fired and one finished. No threshold was moved afterwards.

\vspace{6pt}
{\small\color{muted}\textbf{Handover:} ``Thank you. My teammate will finish with the cause and the close.''}"""

old_m5 = r"""\section{Member 5 \textnormal{\small --- slides 11 to 13, cause and close}}

\slideref{slide 11} Thank you. The last part is the cause and the limits.

Energy follows text length, not the number of passages. The equation on the slide explains ninety-five point seven five percent of the variation, against eighty-nine point six five for the depth model. Each extra prefill token costs about twenty-five millijoules.

We also padded four passages to the length of thirty-two with neutral text. The cost rose to seventy-five point nine joules, close to the eighty-seven point two joules of thirty-two real passages.

\slideref{slide 12} So what can we claim? Serving at k equals four instead of thirty-two saves about two thirds of the GPU energy per correct answer, and every method we tried puts the saving above half.

What we cannot claim is a five-point accuracy guarantee, a single best depth, or an adaptive router gain. We tested the router twice and found nothing.

\slideref{slide 13} Thank you. We are happy to take your questions."""

new_m5 = r"""\section{Member 5 \textnormal{\small --- slides 10 and 11, cause and cost, then close}}

\slideref{slide 10} Thank you. I will explain why the effect exists.

Recall always rises with depth, because more passages make the correct one easier to find. Precision moves both ways, and it decides the sign of the result. When we hold the correct passage first, adding distractors actually helps. So the loss comes from the correct passage being pushed down the list, not from length alone.

\slideref{slide 11} And energy follows text length. The equation on the slide explains ninety-five point seven five percent of the variation, against eighty-nine point six five for depth. Each extra prefill token costs about twenty-five millijoules. We checked this by padding four passages to the length of thirty-two, and the cost rose to seventy-five point nine joules.

\slideref{slide 12} So, in one line: serving at k equals four instead of thirty-two saves about two thirds of the GPU energy per correct answer. We do not claim a five-point guarantee, a single best depth, or a router gain. Thank you. We are happy to take questions."""

for old, new in ((old_m4, new_m4), (old_m5, new_m5)):
    if old not in t:
        raise SystemExit("block not found: " + old[:60])
    t = t.replace(old, new)

# speaker table rows
t = t.replace("Member 4 & 8--10 & The decision rule, fixed rules, the cause & 1.5 min \\\\",
              "Member 4 & 8--9 & The decision rule, fixed rules & 1.5 min \\\\")
t = t.replace("Member 5 & 11--13 & Text length, findings and limits, close & 1.5 min \\\\",
              "Member 5 & 10--12 & The cause, text length, close & 1.5 min \\\\")

# cue cards
t = t.replace(r"\subsection*{Member 4 \textnormal{\small (slides 8--10)}}",
              r"\subsection*{Member 4 \textnormal{\small (slides 8--9)}}")
t = t.replace(r"\subsection*{Member 5 \textnormal{\small (slides 11--13)}}",
              r"\subsection*{Member 5 \textnormal{\small (slides 10--12)}}")

p.write_text(t, encoding="utf-8")
print("script re-mapped")
