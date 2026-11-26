"""WCAG contrast audit for the slide palette (projector legibility)."""

from __future__ import annotations


def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio(fg: str, bg: str) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


# Candidate palette pairs actually used (or proposed) in the deck.
PAIRS = [
    ("body ink on white", "#1B2414", "#FFFFFF"),
    ("body ink on paper", "#1B2414", "#F6F2E6"),
    ("card title olive on white", "#6E760F", "#FFFFFF"),
    ("card title olive on paper", "#6E760F", "#F6F2E6"),
    ("eyebrow deep green on white", "#2B4014", "#FFFFFF"),
    ("eyebrow deep green on paper", "#2B4014", "#F6F2E6"),
    ("footer deep green on white", "#2B4014", "#FFFFFF"),
    ("sub muted on white", "#424A3E", "#FFFFFF"),
    ("sub muted on paper", "#424A3E", "#F6F2E6"),
    ("team rows white on dark green", "#FFFFFF", "#123524"),
    ("team head lime on dark green", "#C8F04F", "#123524"),
    ("table body on lime header", "#1B2414", "#C8F04F"),
    ("white on lime (bad)", "#FFFFFF", "#C8F04F"),
    ("PROPOSED card title forest", "#1F5134", "#FFFFFF"),
    ("PROPOSED eyebrow forest", "#1F5134", "#FFFFFF"),
    ("PROPOSED teal accent", "#0F766E", "#FFFFFF"),
    ("PROPOSED amber accent", "#8A4B00", "#FFFFFF"),
    ("PROPOSED rose accent", "#9F1239", "#FFFFFF"),
]

print(f"{'pair':44s} {'ratio':>7s}  {'AA body':>8s} {'AA large':>9s}  verdict")
print("-" * 92)
for name, fg, bg in PAIRS:
    r = ratio(fg, bg)
    aa_body = r >= 4.5
    aa_large = r >= 3.0
    if r >= 7:
        v = "AAA - excellent on projector"
    elif r >= 4.5:
        v = "AA - good"
    elif r >= 3.0:
        v = "AA large only - thin"
    else:
        v = "FAIL - illegible in daylight"
    print(f"{name:44s} {r:7.2f}  {str(aa_body):>8s} {str(aa_large):>9s}  {v}")
