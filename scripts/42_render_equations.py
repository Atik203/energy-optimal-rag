"""Render display equations with real LaTeX (matplotlib usetex) to transparent PNGs."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = Path(r"C:\Users\atiku\AppData\Local\Temp\opencode\ppt\eq")
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "text.usetex": True,
        "font.family": "serif",
        "font.size": 24,
        "text.latex.preamble": r"\usepackage{amsmath}\usepackage{xcolor}",
    }
)

EQUATIONS = {
    "eq_estimand": r"$E(k) = \dfrac{\sum_q J_{qk}}{\sum_q C_{qk}}$",
    "eq_token": r"$J = 13.88 + 0.02549\,T_{\mathrm{pre}} + 1.135\,T_{\mathrm{dec}}$",
    "eq_did": r"$\Delta = [A_d(4) - A_d(32)] - [A_b(4) - A_b(32)]$",
}


def main() -> int:
    for name, tex in EQUATIONS.items():
        fig = plt.figure(figsize=(8, 2))
        fig.patch.set_alpha(0.0)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.text(0.5, 0.5, tex, ha="center", va="center", color="#14241B")
        path = OUT / f"{name}.png"
        fig.savefig(path, dpi=300, transparent=True, bbox_inches="tight", pad_inches=0.05)
        plt.close(fig)
        print(f"wrote {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
