"""Trim members 4 and 5 back to about 150 words after the fact corrections."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/Presentation_Script_and_QA.tex")
t = p.read_text(encoding="utf-8")

PAIRS = [
    (
        "That is the part we guard most carefully, because moving a threshold after seeing the numbers is the easiest mistake to make.",
        "That is the easiest mistake to make, so we guard it most.",
    ),
    ("Thank you. I will explain why the effect exists.", "Thank you. Why does accuracy change?"),
    (
        "Two more checks agree: swapping the retriever moves the result by only two points, and padding to the same length costs eighty-seven percent of the energy.",
        "Two checks agree: the retriever swap moves the result by two points, and padding costs eighty-seven percent of the energy.",
    ),
    (
        "The equation on the slide explains ninety-five point seven five percent of the variation, against eighty-nine point six five for depth.",
        "The equation explains ninety-five point seven five percent of the variation, against eighty-nine point six five for depth.",
    ),
    (
        "So: serving at k equals four instead of thirty-two saves about two thirds",
        "So: four passages instead of thirty-two saves about two thirds",
    ),
]

for old, new in PAIRS:
    if old not in t:
        print("MISS:", old[:56])
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("trimmed")
