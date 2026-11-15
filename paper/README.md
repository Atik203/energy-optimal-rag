# Paper

**Status (2026-11-15): P0 FAIL · P1 COMPLETE, primary result NOT SUPPORTED · no replication or
adaptive result.**
The supplement builds (13 pages) and reports the P1 confirmatory result. The main manuscript is
in progress.

| Phase | State | Detail |
|---|---|---|
| P0 harness | **FAIL** | Clean `_r3` sweep: 1,400/1,400 valid rows, 0 invalid, idle CV 1.12%; block `k=0` factor 0.7944 below the fixed 0.8 floor. No blocks, repeat CV, or calibrated analysis. |
| P1 powered run | **COMPLETE, negative** | 7,000/7,000 valid rows, 0 invalid; all seven block factors pass (0.8089–1.3111). Primary 5 pp non-inferiority **NOT SUPPORTED**: `A(4) − A(32) = −4.30` pp, one-sided 95% lower bound `−6.17` pp, `p = 0.2691`; savings 58.17% [56.02, 60.14]. H1 and H4 supported; H3 not supported. |

## File map

| Path | Role | State |
|---|---|---|
| `supplement.tex` | Methods and reproducibility supplement, sections S1–S7 | Builds; P1 results included |
| `main.tex` | Manuscript (decision-theory + causal-measurement paper) | In progress (paper agent) |
| `refs.bib` | Bibliography for `main.tex` | In progress |
| `figures/` | `design.png`, `p0_harness.png`, P1 curve and calibration figures | Generated |
| `tables/` | P0 and P1 table fragments (`\input`) | Generated |
| `scripts/make_figures.py`, `scripts/make_tables.py` | Paper figure and table generators | Present |
| `FORMAT.md` | Format specification shared by `main.tex` and `supplement.tex` | Current |
| `writing-support/PROJECT_BRIEF.md` | Evidence map, terminology lock, open questions | Current |
| `writing-support/VOICE_PROFILE.md` | Voice calibration and authorship rung | Current |
| `out/`, `out-supplement/` | `latexmk` build directories | Local; do not commit |

## Build

Run from `paper/`. Requires TeX Live with `els-cas-templates` (`cas-sc.cls`) and
`elsarticle-num.bst`.

```powershell
latexmk -pdf -interaction=nonstopmode -outdir=out-supplement supplement.tex
latexmk -pdf -interaction=nonstopmode -outdir=out main.tex
latexmk -C -outdir=out-supplement supplement.tex   # clean
```

The supplement builds to 13 pages with 0 errors, no undefined references, and no overfull boxes.
The `cas-sc` class emits duplicate-float-destination notices for tables; they are cosmetic. Do
not commit build products.

## Tables and figures

Every table and figure must come from a registered run. The paper generators read the raw runs
and the P1 analysis output and emit `\input` fragments or PNGs:

```powershell
python paper/scripts/make_tables.py
python paper/scripts/make_figures.py
python paper/scripts/make_figures.py --check
```

Run them from the repository root. The older root-level `scripts/08_make_tables.py` and
`scripts/09_make_figures.py` are v0.1.0 stubs that exit with status 2; they are not the paper
pipeline. Do not hand-edit a generated `.tex` fragment or a figure.

## Evidence map

| Paper object | Evidence | State |
|---|---|---|
| P0 failure detail (S5) | `docs/P0_HARNESS_REPORT.md`, `analysis/p0_calibration_diagnostic/` | Final |
| P0 registry/ledger rows | `runs/registry.csv`, `artifacts/ledger.csv` | Tracked; `_r3` is `invalid` |
| Pilot values (S3 pilot column) | `docs/PILOT_EVIDENCE.md`, `artifacts/claims_evidence.csv` | Transcribed prior evidence (D-011) |
| Frozen thresholds and hashes | `prereg/PREREGISTRATION.md`, `prereg/analysis_plan.md`, `prereg/FREEZE.md`, `configs/analysis/prereg.toml` | Frozen |
| P1 primary and descriptive results | `analysis/squad_qwen4b_p1/`, `docs/P1_RESULTS.md` | Complete; claims C-025–C-029 |
| P1 raw rows, blocks, repeat | `runs/squad_qwen4b_p1/` | Local-only (D-020); 7,000 rows |
| Claim index | `artifacts/claims_evidence.csv` | C-025–C-029 |
| Artifact checksums | `artifacts/ledger.csv` | A-0010–A-0018 |

## Claim boundary

The paper does **not** claim 5 pp non-inferiority, "certified" savings, a 2 pp optimum, a
universal `k*`, or an adaptive-policy gain. The primary result is a documented negative at 5 pp;
the 58.17% savings is a calibrated descriptive ratio of sums that does not support the policy
claim because the accuracy side fails. H3 fails, so the identity is reported as a local
diagnostic, not as proof of optimality. The Llama 3.2 3B reader and the 16k context-budget probe
are exploratory/diagnostic and do not enter H7 or G5. H200 results are accuracy-only and never
pooled with RTX 3060 energy. The wall-meter cross-check is waived (D-016). The `k=0` P1 factor
(0.8089) passed but is only 1.1% above the fixed floor; it is reported as measured and the range
was not widened. Raw P0/P1 data are local-only (D-020), so the reproducibility package is
incomplete until an external backup exists.
