"""Update Member 1's speech for the new slide 3 (three readers + their curves)."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/Presentation_Script_and_QA.tex")
t = p.read_text(encoding="utf-8")

old = r"""\slideref{slide 2} Most systems choose the number of retrieved passages by habit. We treat that number as a decision. We ask one question: can we use fewer passages, spend less energy, and still keep the same accuracy?

The number we follow is energy per correct answer. We take all the joules used at one depth and divide them by all the correct answers at that depth. We do not average per-question ratios, because at low depth most questions are wrong, and the ratio becomes meaningless.

\slideref{slide 3} To answer this we used one thousand SQuAD questions, seven depths from zero to thirty-two, a four-bit Qwen model, BM25 retrieval, and one laptop GPU. Every question was run at every depth, which gave us seven thousand measured answers."""

new = r"""\slideref{slide 2} Most systems choose the number of retrieved passages by habit. We treat that number as a decision.

The number we follow is energy per correct answer: all the joules used at one depth, divided by all the correct answers at that depth. We never average per-question ratios, because at low depth most questions are wrong, and the ratio becomes meaningless.

\slideref{slide 3} We used one thousand SQuAD questions, seven depths, BM25 retrieval, and one laptop GPU. That gave seven thousand measured answers.

We also tested two smaller readers on the same questions. The chart shows why the reader matters. Our main model keeps improving up to thirty-two passages. Llama peaks at four and then falls. The 1.5B model stays flat. So there is no single best depth."""

if old not in t:
    raise SystemExit("member 1 block not found")
t = t.replace(old, new)

# add one likely question about the three readers
anchor = r"""\qa{What does ``energy per correct answer'' actually mean?}"""
addition = (
    r"""\qa{Why test three different readers?}{Because the shape of the accuracy curve is a property of the reader, not of retrieval. """
    r"""The main model keeps improving, Llama peaks early, and the smallest model is flat. One reader alone would have hidden that.}"""
    "\n\n" + anchor
)
if anchor in t:
    t = t.replace(anchor, addition, 1)
else:
    print("anchor for new question not found")

p.write_text(t, encoding="utf-8")
print("speech updated")
