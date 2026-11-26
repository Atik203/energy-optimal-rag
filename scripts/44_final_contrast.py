"""Final contrast check for the shipping slide palette."""

from __future__ import annotations


def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(h: str) -> float:
    h = h.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio(a: str, b: str) -> float:
    x, y = lum(a), lum(b)
    hi, lo = max(x, y), min(x, y)
    return (hi + 0.05) / (lo + 0.05)


PAIRS = [
    ("title ink on white", "#14241B", "#FFFFFF"),
    ("takeaway muted on white", "#4A5A52", "#FFFFFF"),
    ("card number ink on white", "#14241B", "#FFFFFF"),
    ("card label forest on white", "#1F5134", "#FFFFFF"),
    ("card sub muted on white", "#4A5A52", "#FFFFFF"),
    ("eyebrow forest on white", "#1F5134", "#FFFFFF"),
    ("panel heading ink on mint", "#14241B", "#EEF5F1"),
    ("panel body muted on mint", "#4A5A52", "#EEF5F1"),
    ("strip text forest on mint", "#1F5134", "#EEF5F1"),
    ("table header white on dark", "#FFFFFF", "#123524"),
    ("table body ink on white", "#14241B", "#FFFFFF"),
    ("team rows white on dark", "#FFFFFF", "#123524"),
    ("team head lime on dark", "#C8F04F", "#123524"),
    ("closing label lime on dark", "#C8F04F", "#123524"),
    ("closing sub on dark", "#C6D6CC", "#123524"),
    ("divider on dark", "#2C4A3A", "#123524"),
]

print(f"{'pair':36s} {'ratio':>6s}  grade")
print("-" * 62)
worst = 99.0
for name, fg, bg in PAIRS:
    r = ratio(fg, bg)
    worst = min(worst, r)
    grade = "AAA" if r >= 7 else "AA" if r >= 4.5 else "AA-large" if r >= 3 else "FAIL"
    print(f"{name:36s} {r:6.2f}  {grade}")
print("-" * 62)
print(f"worst text pair: {worst:.2f}:1 (AA body needs 4.5)")
