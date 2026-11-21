# Paper Voice and Structure Update — Implementation Plan

**Plan date:** 2026-11-22
**Author of the task:** project author
**Executor:** OpenCode agent with `academic-writer-humanizer` and
`subagent-driven-development`
**Manuscript:** `paper/main.tex`
**Status:** implemented on branch `paper/voice-restructure`; final review pending

## 1. Goal

Update the manuscript so that it follows the supervisor-locked G0–G15 writing
guide and the calibrated author voice profile, without changing any number,
claim, equation, citation, label, or gate verdict. Then reduce `paper/` to the
files Overleaf actually needs.

The update is an editorial and structural pass, not a new analysis. No result is
recomputed, no gate is re-adjudicated, and no claim is strengthened.

## 2. Binding constraints

These override every style preference.

1. **Claim boundary.** P0 remains FAIL. The 5 pp P1 result remains NOT
   SUPPORTED. `0.7944` is not rounded or re-thresholded. No universal `k*`, no
   adaptive-policy claim, no 16k/H200 energy claim.
2. **Numbers.** Every number must trace to a registered run or analysis output.
   Do not change, round, or invent a value. Do not add a result.
3. **Equations and symbols.** Preserve every equation, symbol, unit, subscript,
   superscript, and equation label. Do not silently correct mathematics.
4. **Citations.** Preserve every `\cite` key. Do not add a reference that is not
   in `refs.bib`.
5. **Labels and references.** Preserve every `\label`, `\ref`, and `\eqref`
   target. Renumbering is automatic through LaTeX; do not hand-edit numbers.
6. **Format.** CAS single-column, numeric citations, 650 DPI figures, 600+ DPI
   rule satisfied. Page limit is not a constraint.
7. **Voice.** Use the high-confidence calibrated profile in
   `C:\Users\atiku\.config\opencode\skills\academic-writer-humanizer\writing-support\VOICE_PROFILE.md`:
   mean sentence length about 20 words, sentence-length standard deviation about
   10.8, substantive paragraphs of 120–250+ words, no 3–6-line stubs, no
   `Furthermore`/`Moreover`/`In conclusion`, formal lowercase `where ...`
   definitions after display equations, and a one-paragraph conclusion.
8. **Integrity.** This is rung B/C work: the agent edits and drafts from project
   evidence; the author must verify every number and citation before submission.
   AI-use disclosure may be required by the institution.

## 3. Baseline audit (current draft)

Measured on `paper/main.tex` at commit `887a28c`:

| Check | Current | Target |
|---|---|---|
| Main numbered sections | 8 | 6 |
| Results subsections | 9, plus 4 subsubsections | 4 |
| Discussion subsections | 3, separate top-level section | folded into Results 5.4 |
| Introduction paragraphs | 6 | 4 |
| Abstract length | about 500 words | about 300 words |
| Conclusion | 4 paragraphs, about 750 words | 1 paragraph, 120–160 words |
| Substantive paragraphs (median) | 106.5 words | 150–250+ words |
| Paragraphs under 80 words | 38 | fewer, and none that are 3–6-line stubs |
| Captions over 35 words | 8 | 0 |
| Figures | 9 PNGs, 6 used | 6 used |
| `.tex` inputs | `theory_appendix.tex`, `supplement_body.tex` | none; both inlined |
| Markdown files in `paper/` | `README.md`, `FIGURES.md`, `FORMAT.md` | none |
| Extra folders in `paper/` | `scripts/`, `tables/`, `writing-support/` | moved outside `paper/` |

Other findings:

- Citation and label checks are clean: 41 cited keys, 41 bib entries, no missing
  or uncited keys, no duplicate labels, no missing references.
- All figures are 650 DPI.
- The prose is already specific and evidence-grounded. The main problems are
  section sprawl, micro-paragraphs, overlong captions, and a small number of
  repetitive sentence openers. Do not flatten the author's clear wording.
- `paper/writing-support/VOICE_PROFILE.md` is stale (confidence low, no
  samples). Use the calibrated high-confidence profile from the skill instead.

## 4. Target structure

Exactly six main numbered sections, then unnumbered back matter, then Appendix A
and Supplementary Material S1–S10.

1. **Introduction** — four paragraphs:
   1. current state and concrete problem;
   2. prior work and gap (5–6 study groups, each with a limitation);
   3. objective and proposed approach;
   4. scope, headline results, contributions, claim boundary.
2. **Related Work and Conventional Method** — three subsections:
   1. Related Work (the five current strands, condensed to three paragraphs);
   2. Baseline Method (merge current Preliminaries + Baseline Method;
      notation, ratio estimand, affine model, constrained optimum, identity,
      certification cost);
   3. Baseline Families (keep the family list, but merge the eight bold
      micro-paragraphs into three substantive paragraphs).
3. **Proposed Method** — three subsections:
   1. Working Principle;
   2. Measurement Protocol (current Measurement, renamed);
   3. Estimators, Gates, and Inference (merge current Estimators and Gates; keep
      Algorithm 1 and the gate table).
4. **Experiments** — four subsections:
   1. Setup and Dataset (merge current Experimental Setup + Dataset);
   2. Procedure and Baselines (merge current Baselines and Procedure);
   3. Evaluation Metrics (keep all equations);
   4. Statistical Analysis (keep all equations and tests).
5. **Results and Discussion** — four subsections:
   1. Descriptive Results and Measurement Validity (pilot, P0, validity, P1
      descriptive curve);
   2. Confirmatory and Replication Results (P1 primary, identity/selection,
      gates, certification, sensitivity, P2);
   3. Theory, Mechanism, and Simulations (P4, recall × precision, simulations);
   4. Discussion, Threats, and Limitations (current Discussion, Threats,
      Limitations, Evidence Status).
6. **Conclusion** — exactly one paragraph, 120–160 words.

Back matter: Author contributions (existing `\printcredits`), Declarations,
Acknowledgements, References. Appendix A theory. Supplementary Material S1–S10.

## 5. File target

Final `paper/`:

```
paper/
  main.tex              # single source: manuscript + Appendix A + supplement S1-S10
  refs.bib
  cas-sc.cls
  cas-common.sty
  figures/              # only the six figures referenced by main.tex
  out/main.pdf          # only build product
```

Move, do not delete, the support material:

- `paper/scripts/` → `tools/paper/scripts/` (update `ROOT` to `parents[3]`,
  table output to `tools/paper/tables/`, figure output stays `paper/figures/`).
- `paper/tables/` → `tools/paper/tables/`.
- `paper/writing-support/` → `docs/paper/writing-support/`.
- `paper/README.md`, `paper/FIGURES.md`, `paper/FORMAT.md` →
  `docs/paper/` (build notes only; not part of the Overleaf upload).
- Remove unused figures: `p1_calibration.png`, `sim_power.png`,
  `sim_selection.png`.
- Remove `paper/scripts/__pycache__/`.
- Update references in `README.md`, `docs/RUNBOOK.md`, and the moved docs.

## 6. Tasks

Each task is one implementer dispatch, followed by one task review. Tasks that
edit `paper/main.tex` run sequentially; never dispatch two implementers on the
same file at once.

### Task 0 — Setup and ledger

- Create branch `paper/voice-restructure` from `main`.
- Create `.superpowers/sdd/2026-11-22-paper-voice-restructure/progress.md` with
  the plan identity line.
- Add `.superpowers/` to `.git/info/exclude` (local only, not committed).
- Record `BASE = git rev-parse HEAD`.
- Save a baseline paragraph/caption/citation report in the workspace.

**Acceptance:** clean branch, ledger exists, baseline report exists.

### Task 1 — Structural consolidation and file inlining

**Files:** `paper/main.tex`, `paper/theory_appendix.tex`,
`paper/supplement_body.tex`.

1. Inline `theory_appendix.tex` and `supplement_body.tex` at their current
   `\input` locations. Remove the `\input` lines. Delete the two files after a
   successful compile.
2. Remove the `\section{Related Work}` heading. Promote the five related-work
   paragraphs into `\subsection{Related Work}` under Section 2, and retitle
   Section 2 to `Related Work and Conventional Method`.
3. Remove `\subsection{Preliminaries}` and fold its text into the opening of
   `\subsection{Baseline Method}`.
4. Merge `\subsection{Gates}` into `\subsection{Estimators and Inference}` and
   rename it `Estimators, Gates, and Inference`.
5. Merge `\subsection{Experimental Setup}` and `\subsection{Dataset}` into
   `\subsection{Setup and Dataset}`.
6. Merge `\subsection{Baselines and Procedure}` remains one subsection; keep
   `\subsection{Evaluation Metrics}` and `\subsection{Statistical Analysis}`.
7. Remove `\section{Discussion and Limitations}` and promote its three
   subsections to `\subsection{Discussion, Threats, and Limitations}` under
   Section 5. Retitle Section 5 `Results and Discussion`.
8. Replace the nine Results subsections and four subsubsections with the four
   target subsections. Keep every paragraph and float; only move headings.
9. Keep `\section{Conclusion}` as Section 6 for now; Task 5 rewrites it.
10. Compile. No undefined references, no duplicate labels, no missing figures.

**Acceptance:** exactly six main `\section` commands before `\appendix`; no
`\input` of a `.tex` file; compile clean; all numbers and citations intact.

### Task 2 — Front matter, Introduction, and Related Work

**Files:** `paper/main.tex` only.

1. Rewrite the abstract to about 300 words in the G2 order: context, gap,
   objective, approach, justification, outcome. Keep the exact primary numbers
   and the negative verdict. Do not add a claim.
2. Rewrite the Introduction to exactly four paragraphs, each 200–260 words:
   - P1 current state with 3–4 citations;
   - P2 prior work and gap with 5–6 study groups, each with a concrete
     limitation;
   - P3 objective and approach (SQuAD, 1,000 questions, 7 depths, Qwen3.5-4B,
     BM25, NVML, prereg, NI test);
   - P4 scope, headline results, five contributions, claim boundary.
3. Condense Related Work from five paragraphs to three substantive paragraphs:
   depth as a design constant + adaptive retrieval; context length/distractors +
   inference energy/measurement; preregistration/NI/selection + selective
   prediction. Keep every citation.
4. Remove repeated sentences between the Introduction and Related Work. The
   Introduction states the gap; Related Work explains the technical lineage.
5. Use the calibrated voice: vary sentence length, avoid `Furthermore` and
   `Moreover`, keep first-person plural for author actions, past tense for
   procedures.

**Acceptance:** abstract ≤ 350 words; Introduction exactly 4 paragraphs; no
citation lost; all abstract numbers match Results.

### Task 3 — Methods sections (2–4)

**Files:** `paper/main.tex` only.

1. Section 2: merge the eight bold baseline-family micro-paragraphs into three
   substantive paragraphs (static baselines; hindsight and matched oracles;
   deployable policy and external comparators). Keep all equations.
2. Section 3: turn the five bold measurement paragraphs into three substantive
   paragraphs (energy decomposition and sensor; block calibration and cache
   control; thermal state, CPU proxy, repeatability, wall meter). Keep every
   equation and Algorithm 1.
3. Section 4: merge Setup + Dataset into two substantial paragraphs; merge
   Baselines + Procedure into two; keep Evaluation Metrics and Statistical
   Analysis equations intact.
4. Add lowercase `where ...` definitions after display equations that currently
   define variables only in an adjacent sentence. Do not change the mathematics.
5. Replace vague quantifiers only where an exact value exists. Do not invent.
6. Keep all table and figure references.

**Acceptance:** Sections 2–4 have 3, 3, and 4 subsections respectively; no
micro-paragraph under 60 words except table/figure lead-ins that are merged;
all equations and citations intact.

### Task 4 — Results 5.1–5.2

**Files:** `paper/main.tex` only.

1. In 5.1, merge the pilot's five paragraphs into three (energy curve;
   accuracy/identity; decision rules/bounds). Merge the P0 paragraphs into
   three. Merge the measurement-validity paragraphs into two. Merge the P1
   descriptive curve into two.
2. In 5.2, merge the P1 primary paragraphs into three (decision and interval;
   inference sensitivity; savings and interpretation). Merge
   identity/selection into one, gates into one, certification into one, and
   sensitivity into one. Merge P2 into two.
3. Remove the `\subsubsection` headings. Use bold run-in labels only when they
   help navigation inside a substantive paragraph.
4. Shorten every caption in this range to ≤35 words; move the explanation into
   the body text.
5. Keep all numbers, table references, and figure references.

**Acceptance:** 5.1 and 5.2 together have no paragraph under 80 words (except a
one-sentence table lead-in, which must be merged into the next paragraph);
captions ≤35 words; all numbers intact.

### Task 5 — Results 5.3–5.4 and Conclusion

**Files:** `paper/main.tex` only.

1. In 5.3, merge P4 into two paragraphs, recall × precision into two, and
   simulations into two. Shorten the simulation figure/table captions.
2. In 5.4, merge the six Discussion bold paragraphs into three substantive
   paragraphs (what the evidence shows; why the selection is unstable; what it
   means for practice and adaptivity). Merge Threats into one lead paragraph
   plus the table. Merge Limitations into three paragraphs (measurement;
   design/scope; statistical/identity/status). Merge Evidence Status into one
   paragraph plus the claim table.
3. Rewrite the Conclusion as exactly one paragraph of 120–160 words. It must
   state the problem, the approach, the headline result with scope, the
   boundary condition, and one future direction. No new result, no citation,
   no bullet list.
4. Shorten all remaining captions over 35 words.
5. Remove generic summary closers and repeated "The ..." openers where the
   referent is clear.

**Acceptance:** 5.3 and 5.4 have no micro-paragraphs; Conclusion is one
paragraph, 120–160 words; all numbers and citations intact.

### Task 6 — Appendix and supplement style pass

**Files:** `paper/main.tex` only (the inlined appendix/supplement).

1. Remove the standalone-supplement preamble comments that no longer apply.
2. Keep S numbering and Appendix A numbering.
3. Merge paragraphs under 60 words in the supplement where they are prose, not
   table notes.
4. Ensure every display equation has a lowercase `where ...` definition.
5. Keep the supplement's 10 sections; do not restructure them into the six main
   sections.
6. Check that all `\ref` targets resolve after inlining.

**Acceptance:** compile clean; no duplicate labels; appendix and supplement
still start on new pages with correct numbering.

### Task 7 — Cleanup and final verification

**Files:** `paper/` tree, `tools/paper/`, `docs/paper/`, root docs.

1. Move support folders and markdowns as specified in section 5.
2. Update script paths and doc references.
3. Remove unused figures and `__pycache__`.
4. Build `paper/out/main.pdf`.
5. Run:
   - `pdflatex` + `bibtex` + `pdflatex` ×2;
   - citation/label/duplicate-label check;
   - paragraph/caption/abstract/conclusion statistics;
   - DPI check;
   - `pytest -q` and `python -m rag_energy.cli validate`;
   - a spot check of 10 headline numbers against `artifacts/claims_evidence.csv`.
6. Confirm `paper/` contains only the target files.

**Acceptance:** clean compile, no undefined refs, no duplicate labels, 6 main
sections, 4 Results subsections, abstract ≤350 words, conclusion 120–160 words,
captions ≤35 words, figures 650 DPI, tests pass, `paper/` clean.

## 7. Review gates

Each implementer report is followed by one task review with two verdicts:

- **Spec compliance:** target structure, paragraph counts, caption limits, and
  preserved numbers/citations/equations.
- **Quality:** voice match, logical flow, no new claims, no lost qualifications.

The reviewer gets the task brief, the implementer report, and a diff file. The
reviewer does not rewrite. Findings enter a fix loop; controller does not fix
findings inline.

## 8. Definition of done

- `paper/main.tex` is the only `.tex` source.
- Six main sections, four Results subsections, one-paragraph conclusion.
- Abstract and Introduction follow G2/G4.
- No caption over 35 words.
- No paragraph that is a 3–6-line stub in the main body.
- Every number, citation, equation, label, and gate verdict preserved.
- `paper/` contains only `main.tex`, `refs.bib`, `cas-sc.cls`,
  `cas-common.sty`, `figures/` (six used files), `out/main.pdf`.
- Compile clean and tests pass.
