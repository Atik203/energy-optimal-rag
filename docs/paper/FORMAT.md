# FORMAT.md - manuscript format specification

> **Note (2026-11-22):** the supplement is now embedded in `paper/main.tex`.
> References to `supplement.tex` below are historical; the current source is the
> single `main.tex`.

This file records the format of the reference manuscript
`G:\HaluRISC\Journal_Paper\halurisc.tex` and turns it into a checklist for this project's
`main.tex` and `supplement.tex`. Where the reference and the installed `cas-sc` class differ,
the class wins.

## 1. Document class and engine

- Class: `\documentclass[a4paper,fleqn]{cas-sc}`. Elsevier CAS, single column, A4, display
  equations left-aligned (`fleqn`).
- Class source: `els-cas-templates` in TeX Live (TeX Live 2026 ships v2.4, dated 2024/05/04).
  `paper/` currently also holds local copies of `cas-sc.cls` and `cas-common.sty` (v2.3, dated
  2021/05/11); LaTeX resolves those first when a document is built in `paper/`.
  `supplement.tex` was verified against both versions and builds cleanly against both; the
  current supplement is 13 pages with the P1 tables. Keep one source before submission:
  either track the local copies deliberately or remove them and build against the installed
  class.
- Engine: `pdflatex` via `latexmk`; bibliography with BibTeX.
- Do not add `geometry`, `fontspec`, or margin packages. The class sets the page and loads its
  own fonts (`stix` for math, `charis` for text, `inconsolata` for monospace).

## 2. Preamble

The class already loads `fontenc` (T1), `amsmath`, `amsfonts`, `amssymb`, `booktabs`,
`makecell`, `multirow`, `array`, `colortbl`, `dcolumn`, `stfloats`, `graphicx`, `hyperref`
(color links), `xcolor`, `footmisc`, `wrapfig`, and `xspace`. The reference preamble adds:

| Package or setting | Purpose |
|---|---|
| `float` | `[H]` placement for a few tables and algorithms |
| `inputenc[utf8]` | UTF-8 source |
| `natbib[numbers]` | Numeric citations (bracketed numerals) |
| `tabularx` | Full-width text tables |
| `babel[english]` | Hyphenation and captions |
| `amsmath`, `amsfonts`, `amssymb`, `booktabs` | Math and rules (already loaded; repeated harmlessly) |
| `multirow`, `hyperref`, `subcaption` | Merged cells, links, subfigures |
| `algorithm`, `algpseudocode` | Numbered algorithms |
| `color`, `xcolor`, `orcidlink`, `lineno`, `silence` | Colour, ORCID badges, line numbers, warning filter |
| `\WarningFilter{hyperref}{Ignoring empty anchor}` | Suppresses a known class/hyperref notice |
| `\setlength{\emergencystretch}{2em}` | Avoids overfull lines in long captions |
| `\renewcommand{\arraystretch}{1.08}`, `\tabcolsep=5pt` | Roomier table cells |

Float placement in the reference: `topnumber=3`, `bottomnumber=2`, `totalnumber=5`,
`topfraction=0.95`, `bottomfraction=0.95`, `textfraction=0.05`, `floatpagefraction=0.7`;
`\textfloatsep` 10 pt, `\floatsep` 8 pt, `\intextsep` 8 pt (set at begin-document);
`\abovecaptionskip=6pt`, `\belowcaptionskip=2pt`. The values are set inside
`\AtBeginDocument` so the class defaults do not override them.

The reference also patches the class footer so it reads `<short authors>: Preprint` instead of
`Preprint submitted to Elsevier`. `supplement.tex` carries the same patch. Keep it unless the
venue requires the Elsevier wording.

## 3. Front matter

Order in the reference:

1. `\shorttitle{...}`, `\shortauthors{...}`.
2. `\title[mode=title]{...}`; the `mode=title` key is the CAS long-title switch.
3. Authors: `\author[1]{Name}[orcid=0000-...]`, optional `\cormark[1]`, `\ead{...}`,
   `\credit{...}`. The affiliation mark in brackets must match an `\affiliation[n]` entry.
4. `\affiliation[1]{organization={...}, city={...}, citysep={}, postcode={...},
   country={...}}`; `\cortext[cor1]{Corresponding author: ...}`.
5. `\begin{abstract} ... \end{abstract}`; one paragraph, no citations, no displayed math.
6. `\begin{keywords} ... \sep ... \end{keywords}`; 3–8 terms.
7. `\begingroup \hfuzz=120pt \maketitle \endgroup`, then `\hypersetup{pdfauthor=..., pdftitle=...}`,
   then `\linenumbers`.

The reference adds inline ORCID badges by redefining `\author` (its lines 81–188) and suppresses
the class's separate `\printorcid` footnote. That patch is optional: if it is copied, copy it
verbatim and keep `\printorcid` suppressed. If it is not copied, ORCID iDs appear only in the
footnote, and the footnote must not be left empty. `supplement.tex` suppresses `\printorcid`
and does not use the byline patch, so it prints no ORCID line.

Author placeholders must be resolved before submission. The supplement currently carries
`Affiliation to be confirmed`; the main manuscript must carry the full author list,
affiliations, corresponding author, and CRediT roles.

## 4. Section, float, and table style

- Sections: `\section{...}\label{sec:...}`, `\subsection{...}`; labels are lowercase and
  prefixed (`sec:`, `tab:`, `fig:`, `eq:`, `alg:`).
- Tables: `\begin{table}[pos=htbp]`, `\centering`, `\caption{...}` **above** the table,
  `\label{...}` immediately after the caption, `\begin{tabular}{...}`, `\toprule`,
  `\midrule`, `\bottomrule`. No vertical rules. Header row in bold. `\addlinespace` separates
  row groups. Missing values are `---`, not blank.
- Long text columns use `>{\raggedright\arraybackslash}p{...}` or `tabularx` with
  `>{\raggedright\arraybackslash}X`. Wide numeric tables use `\small` and
  `\setlength{\tabcolsep}{4pt}`.
- Table notes live inside the caption, marked `$^{\dagger}$`, `$^{\ast}$`, and explained there.
  Captions are one sentence where possible and state the sample size and seed when they vary.
- Figures: `\begin{figure}[pos=htbp]`, `\centering`,
  `\includegraphics[width=\linewidth]{...}`, `\caption{...}` **below** the figure, `\label{...}`
  after the caption. Subfigures use `subcaption` with `\subcaptionbox` or `subfigure`.
- The reference uses `[pos=htbp]` rather than `[htbp]` because CAS reads placement as a key.
  `[H]` is used only with the `float` package and only for tables/algorithms that must not move.
- Thousands separators inside math use `{,}` (`5{,}034`); ranges use `--`; subtraction in text
  uses `$-$`; units are separated by `~` (`6~GB`, `0.3~s`).

## 5. Figures: resolution and fonts

Measured from the reference figure files:

- Ten of the thirteen PNGs carry 650 dpi metadata, one carries 600 dpi, and the two architecture
  diagrams are 5,600 px wide with no DPI tag. All are placed at `\linewidth` or `0.98\linewidth`.
- Figures are raster PNG. Nothing in the reference requires PNG, so vector PDF is preferred for
  line art and plots; use PNG only for screenshots and diagrams.
- Rule for this project: vector PDF for plots, or PNG at ≥300 dpi at final print width. Text
  inside a figure must be ≥7 pt after scaling to `\linewidth`. No figure titles; the caption
  carries the title. Use a colourblind-safe palette and distinguish series by marker or dash as
  well as colour.
- `\graphicspath` in the reference lists four prefixes. This project uses one: `figures/`, with
  generated files written by `tools/paper/scripts/make_figures.py`. The root-level
  `scripts/09_make_figures.py` is an older v0.1.0 stub and is not the paper pipeline.

## 6. Mathematics

- `fleqn` is on; do not override it.
- Number display equations; add a label when the equation is referenced. Operators are
  `\mathrm` (`\mathrm{gpu}`); vectors are bold or plain per the paper's notation lock.
- One symbol, one meaning. In this project: `k` depth, `A(k)` accuracy, `J(k)` joules per query,
  `E(k)` joules per correct answer, `S(k)` context-side share, `S_r(k)` retrieval-only share,
  `N*` certification cost, `\Delta(k)` identity gap.
- Units are stated in the text or the column header, not inside every symbol.

## 7. Bibliography

- `natbib` with `numbers`; `\cite{...}` produces bracketed numerals.
- Style: `\bibliographystyle{elsarticle-num}`. The reference uses `\bibliography{ref}`; this
  project uses `\bibliography{refs}` for `refs.bib`.
- Reference spacing: `\setlength{\bibsep}{0pt}`, `\renewcommand{\bibfont}{\fontsize{8.5pt}{9pt}
  \selectfont}`, and `\sloppy` before the bibliography.
- Citation keys in the reference are short lowercase tokens (`selfcheck`, `guo`, `shap`).
  Recommended key form for this project: `firstauthorYYYYtopic`.
- No citation may appear in `supplement.tex`; references are inherited from the main
  manuscript. Do not add a second bibliography to the supplement.

## 8. Back matter

After the last section: `\printcredits` (requires `\credit{}` entries), then
`\section*{Declarations}` with an `itemize` of **Funding**, **Conflicts of Interest**,
**Data availability**, **Code availability**, and **Ethical approval**, then
`\section*{Acknowledgements}`, then the bibliography. The reference ends with `\end{document}`
after a small vertical space.

For this project the data-availability statement must match D-020 (raw runs local-only, no raw
SQuAD/HotpotQA text redistributed) and the code statement must point to
`https://github.com/Atik203/energy-optimal-rag` under MIT.

## 9. Checklist for `main.tex` and `supplement.tex`

| # | Requirement | How to check |
|---:|---|---|
| 1 | Class line is `\documentclass[a4paper,fleqn]{cas-sc}` | Inspect line 1 |
| 2 | No `geometry`, `fontspec`, or manual margin changes | `Select-String -Path *.tex -Pattern 'geometry\|fontspec\|hoffset\|voffset'` |
| 3 | `natbib[numbers]`, `booktabs`, `tabularx`, `babel[english]` present | Inspect preamble |
| 4 | `\shorttitle`, `\shortauthors`, `\title[mode=title]` set | Inspect front matter |
| 5 | Every `\author` mark has an `\affiliation`; corresponding author marked | Read the PDF page 1 |
| 6 | Abstract has no citations and no displayed math | `Select-String` inside the abstract |
| 7 | Keywords separated by `\sep`, 3–8 terms | Inspect front matter |
| 8 | `\maketitle` inside `\begingroup \hfuzz=120pt ... \endgroup` | Inspect front matter |
| 9 | Every `\ref` target exists; no `??` in the PDF | `Select-String out\main.log -Pattern 'undefined'` |
| 10 | Table captions above, figure captions below, labels after captions | Read the PDF |
| 11 | Booktabs rules only; no vertical rules | `Select-String -Path *.tex -Pattern 'hline'` |
| 12 | Wide tables fit the text block (no overfull box) | `Select-String out\main.log -Pattern 'Overfull'` |
| 13 | Figures are vector or ≥300 dpi at print width; text ≥7 pt | Inspect source files |
| 14 | Every number traces to `analysis/<run_id>/` or `artifacts/claims_evidence.csv` | Cross-check each table |
| 15 | No `TBD`, `[P1 RESULT PENDING]`, or `[VERIFY ...]` in a submitted draft | `pdftotext out\main.pdf - \| Select-String 'TBD\|PENDING\|VERIFY'` |
| 16 | Citations all resolve; numeric style | `Select-String out\main.log -Pattern 'Citation.*undefined'` |
| 17 | Supplement keeps S-numbering and has no bibliography | Inspect `\thesection` block; search for `\bibliography` |
| 18 | Build has 0 errors | `Select-String out\main.log -Pattern '^!'` |
| 19 | Build products under `out/`, `out-supplement/` are not committed | `git status --short` |
| 20 | Placeholders listed in the hand-off note before submission | Read the hand-off note |

## 10. Definition of a clean build

A build is clean when it reports 0 errors, 0 undefined references, 0 undefined citations, and no
overfull box wider than 5 pt. The `cas-sc` class emits `destination with the same identifier`
notices for table floats; they come from the class's float anchors and are cosmetic, not errors.
Any other warning is reviewed before the draft is circulated.

Commands, from `paper/`:

```powershell
latexmk -pdf -interaction=nonstopmode -outdir=out main.tex
Select-String -Path out\main.log -Pattern '^!|undefined|Overfull'
pdftotext -layout out\main.pdf - | Select-String 'TBD|PENDING|VERIFY'
```
