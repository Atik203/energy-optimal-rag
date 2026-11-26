"""Member 5: cover all three probes on slide 10, shorten slide 11 to match."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/Presentation_Script_and_QA.tex")
t = p.read_text(encoding="utf-8")

old = r"""\slideref{slide 10} Thank you. I will explain why the effect exists.

Recall always rises with depth. Precision moves both ways, and it decides the sign. When we hold the correct passage first, adding distractors actually helps. So the loss comes from the correct passage being pushed down the list, not from length alone.

\slideref{slide 11} And energy follows text length. The equation on the slide explains ninety-five point seven five percent of the variation, against eighty-nine point six five for depth. Each extra prefill token costs about twenty-five millijoules. We checked this by padding four passages to the length of thirty-two, and the cost rose to seventy-five point nine joules."""

new = r"""\slideref{slide 10} Thank you. I will explain why the effect exists.

Recall always rises with depth. Precision moves both ways, and it decides the sign. When we hold the correct passage first, adding distractors actually helps. So the loss comes from the correct passage being pushed down the list. Two more checks agree: swapping the retriever moves the result by only two points, and padding to the same length costs eighty-seven percent of the energy.

\slideref{slide 11} Energy follows text length, not passage count. The equation on the slide explains ninety-five point seven five percent of the variation, against eighty-nine point six five for depth. Each extra prefill token costs about twenty-five millijoules."""

if old not in t:
    raise SystemExit("member 5 block not found")
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("member 5 updated")
