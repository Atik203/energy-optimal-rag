"""48b - Render the deck equations with real LaTeX (transparent PNG).

Uses the same pdflatex path as the manuscript so the symbols match.
Output: ppt_slides/figures/eq_*.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "ppt_slides" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "text.usetex": True,
        "font.family": "serif",
        "font.size": 26,
        "text.latex.preamble": r"\usepackage{amsmath}",
    }
)

INK = "#14241B"

EQUATIONS = {
    "eq_estimand": (r"$E(k) \;=\; \dfrac{\sum_{q} J_{qk}}{\sum_{q} C_{qk}}$", (7.2, 2.2)),
    "eq_savings": (r"$\mathrm{Sav}(k) \;=\; 1 - \dfrac{E(k)}{E(32)}$", (7.2, 1.9)),
    "eq_token": (r"$J \;=\; 13.88 \;+\; 0.02549\,T_{\mathrm{pre}} \;+\; 1.135\,T_{\mathrm{dec}}$", (8.6, 1.9)),
    "eq_rq": (r"$A(k) \;=\; R(k)\cdot Q(k)$", (5.4, 1.8)),
    "eq_identity": (r"$\Delta(k) \;=\; \varepsilon_{J}(k) \;-\; \varepsilon_{A}(k)$", (6.6, 1.9)),
}


def main() -> int:
    for name, (tex, size) in EQUATIONS.items():
        fig = plt.figure(figsize=size)
        fig.patch.set_alpha(0.0)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.text(0.5, 0.5, tex, ha="center", va="center", color=INK)
        path = OUT / f"{name}.png"
        fig.savefig(path, dpi=300, transparent=True, bbox_inches="tight", pad_inches=0.04)
        plt.close(fig)
        print(f"  {name}.png  {path.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
