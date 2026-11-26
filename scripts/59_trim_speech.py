"""Trim members 2, 4 and 5 to 150 words (1.5 minutes at 100 wpm)."""

from __future__ import annotations

from pathlib import Path

p = Path("docs/PRESENTATION_SCRIPT.tex")
t = p.read_text(encoding="utf-8")

PAIRS = [
    (
        "That removes question difficulty from the comparison, because a hard question stays hard at every depth.",
        "That removes question difficulty from the comparison.",
    ),
    ("when the machine is cool and steady", "when the machine is cool"),
    (
        "A smaller depth counts as good only if it does two things.",
        "A smaller depth counts as good only if it does both.",
    ),
    (
        "hashed them, and tagged them in the repository, so the rules could not move",
        "hashed them, and tagged them, so the rules could not move",
    ),
    (
        "Precision moves in both directions, and it decides the sign of the result.",
        "Precision moves both ways, and it decides the sign.",
    ),
    ("Then we asked why the effect exists.", "Then we asked why."),
    (
        "The last part is the physical cause, and the limits of what we can say.",
        "The last part is the cause and the limits.",
    ),
    (
        "We also padded four passages with neutral text until they reached the length of thirty-two.",
        "We also padded four passages to the length of thirty-two with neutral text.",
    ),
    ("the variation in energy, against", "the variation, against"),
]

for old, new in PAIRS:
    if old not in t:
        print("MISS:", old[:52])
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("trimmed")
