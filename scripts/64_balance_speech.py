"""Balance members 4 and 5 to about 150 words each."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/Presentation_Script_and_QA.tex")
t = p.read_text(encoding="utf-8")

PAIRS = [
    # Member 4 gains one sentence
    (
        "Five tests fired and one finished. No threshold was moved afterwards.",
        "Five tests fired and one finished. No threshold was moved afterwards. "
        "That is the part we guard most carefully, because moving a threshold after seeing the numbers is the easiest mistake to make.",
    ),
    # Member 5 sheds a few words
    (
        "Recall always rises with depth, because more passages make the correct one easier to find.",
        "Recall always rises with depth.",
    ),
    (
        "Precision moves both ways, and it decides the sign of the result.",
        "Precision moves both ways, and it decides the sign.",
    ),
    (
        "So, in one line: serving at k equals four instead of thirty-two",
        "So: serving at k equals four instead of thirty-two",
    ),
]

for old, new in PAIRS:
    if old not in t:
        print("MISS:", old[:60])
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("balanced")
