# Paper

**Status (2026-11-19):** the manuscript includes P0–P4, the formal theory appendix,
the inference sensitivity layer, the simulation evidence, and the supplementary
material in one document. Page limit is not a constraint for the current draft.

## File map

| Path | Role |
|---|---|
| `main.tex` | Manuscript and supplementary material; the single source document |
| `theory_appendix.tex` | Formal assumptions, Lemma 1, Propositions 1–3, corollaries, proofs |
| `supplement_body.tex` | Supplementary sections S1–S10, included by `main.tex` with S numbering |
| `refs.bib` | Bibliography |
| `figures/` | 650-DPI figures generated from registered runs |
| `tables/` | Generated LaTeX table fragments |
| `scripts/` | Figure and table generators |
| `writing-support/` | Project brief and voice profile (not part of the PDF) |
| `out/main.pdf` | The only build product; open this file |

## Build

Run from `paper/` with TeX Live:

```powershell
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

The current build is 54 pages with no undefined references or multiply-defined
labels. Build products other than `out/main.pdf` are not committed.

## Reproducibility

Every table and figure comes from a registered run or an analysis output. The
generators are:

```powershell
python paper/scripts/make_tables.py
python paper/scripts/make_figures.py --p1
python paper/scripts/make_frontier_figure.py
python paper/scripts/make_measurement_figure.py
```

The paper archive is at DOI `10.5281/zenodo.24352803`. Raw question/context text
is not redistributed; sanitized per-query tables are in `artifacts/release/`.
