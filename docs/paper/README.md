# Paper support notes

**Status (2026-11-22):** the manuscript is a single `paper/main.tex` that contains
the main paper, Appendix A (formal theory), and Supplementary Material S1-S12.
Page limit is not a constraint for the current draft.

## Upload package

The Overleaf package is the `paper/` folder:

| Path | Role |
|---|---|
| `main.tex` | Manuscript, Appendix A, and Supplementary Material; the single `.tex` source |
| `refs.bib` | Bibliography |
| `cas-sc.cls`, `cas-common.sty` | CAS class files |
| `figures/` | six 650-DPI figures used by `main.tex` |
| `out/main.pdf` | the only build product |

`main.tex` is the root file. No other `.tex` file is required.

## Build

Run from `paper/` with TeX Live:

```powershell
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

The current build has no undefined references or multiply-defined labels. Build
products other than `out/main.pdf` are not committed.

## Reproducibility

Every table and figure comes from a registered run or an analysis output. The
generators now live outside the upload package:

```powershell
python tools/paper/scripts/make_tables.py
python tools/paper/scripts/make_figures.py --p1
python tools/paper/scripts/make_frontier_figure.py
python tools/paper/scripts/make_measurement_figure.py
```

Generated table fragments are written to `tools/paper/tables/`; figures are
written to `paper/figures/`. The paper archive is at DOI
`10.5281/zenodo.24352803`. Raw question/context text is not redistributed;
sanitized per-query tables are in `artifacts/release/`.

## Historical notes

`FIGURES.md` and `FORMAT.md` describe the original two-file build. The
supplement is now embedded in `main.tex`; references to `supplement.tex` in those
notes are historical.
