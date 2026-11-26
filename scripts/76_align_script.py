"""Align the speaker script with the corrected slide facts."""

from __future__ import annotations

from pathlib import Path

p = Path("Slides/Presentation_Script_and_QA.tex")
t = p.read_text(encoding="utf-8")

PAIRS = [
    (
        "Per-question readings captured only eighty-one point seven percent of the measured time, "
        "and at k equals four they came out twenty-two percent low. The error depends on the depth, "
        "so no single correction can repair it. That is why we moved to batches.",
        "The per-question readings recovered only eighty-one point seven percent of the replay energy. "
        "At k equals four the window reads thirty-six point two five joules per query against the "
        "block's twenty-eight point three three, so it overstates by about twenty-eight percent. "
        "The bias shrinks with depth, so no single correction can repair it.",
    ),
    (
        "It must save at least twenty percent of the energy, and it must lose at most five accuracy points.",
        "It must save at least twenty percent of the energy, and the ninety-five percent lower bound "
        "on its accuracy loss must be no worse than five points.",
    ),
    (
        "That is inside the limit. But the lower bound of our confidence interval was minus six point "
        "one seven, which is outside it. So the saving condition was met, and the accuracy condition was not.",
        "The estimate is inside the limit. But the rule is about the lower bound, and the bound is "
        "minus six point one seven, which is outside it. So the saving condition was met, and the "
        "accuracy condition was not.",
    ),
    (
        "Precision moves both ways, and it decides the sign.",
        "Precision swings from minus thirteen to plus eight points across the groups, and it decides "
        "whether net accuracy rises or falls.",
    ),
    (
        "so the direction is solid even though the exact number is uncertain.",
        "so the direction is solid even though the point estimate is not, and our checks on it did not all agree.",
    ),
]

for old, new in PAIRS:
    if old not in t:
        print("MISS:", old[:60])
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("script aligned")
