# Paper figures and tables

**Status:** 2026-11-22. The current paper uses six figures: `design.png`,
`p0_harness.png`, `measurement_validity.png`, `p1_curve.png`, `p1_frontier.png`,
and `sim_ratio.png`. The old `p1_calibration.png` was removed from the package because
the paper now reports the block factors in a table.

The P1 primary result is **negative**: the 5 pp non-inferiority test is **not supported**
(`A(4)-A(32) = -4.30` pp; one-sided lower bound `-6.17` pp; savings `58.17%`). The figure
states that explicitly. No positive 5 pp claim is made anywhere.

The scripts are the source of truth:

- `tools/paper/scripts/make_figures.py` → `paper/figures/*.png`
- `tools/paper/scripts/make_tables.py` → `tools/paper/tables/*.tex`

The supplement is now embedded in `paper/main.tex`; the old standalone
`supplement.tex` no longer exists. The figure package is limited to the six files
listed above.

---

## 1. Reference style, measured with PIL

The style target was read from `G:\HaluRISC\Journal_Paper\figures\**\*.png` with PIL
(`Image.open(...).size`, `.info["dpi"]`). Representative values:

| Reference file | Pixels | DPI | Width (in) |
|---|---:|---:|---:|
| `b3/transfer_score_distributions.png` | 4290 × 3055 | 650.0 | 6.60 |
| `b4/calibration_shift.png` | 4290 × 2047 | 650.0 | 6.60 |
| `b4/reliability_diagrams.png` | 4290 × 2047 | 650.0 | 6.60 |
| `revision/confusion_matrix.png` | 2666 × 2210 | 650.0 | 4.10 |
| `revision/h200_efficiency.png` | 4200 × 1650 | 600.0 | 7.00 |
| `revision/length_analysis.png` | 3921 × 1652 | 650.0 | 6.03 |
| `revision/m3_shap_summary.png` | 4160 × 2307 | 650.0 | 6.40 |
| `revision/operating_point_label_budget.png` | 4290 × 1950 | 650.0 | 6.60 |
| `revision/per_seed_stability.png` | 4009 × 1969 | 650.0 | 6.17 |
| `revision/roc_pr_curves.png` | 4030 × 3575 | 650.0 | 6.20 |
| `revision/shap_summary.png` | 3942 × 2110 | 650.0 | 6.06 |

The dominant reference format is **650 dpi, 6.0–6.6 in wide, 3,900–4,300 px**. One
650-dpi panel is 2,666 px wide, and one 600-dpi figure is 4,200 px wide. Two architecture
illustrations (`architecture-flow-large.png`, `system-architecture-large.png`) carry no DPI
metadata and were not used as chart references.

The project contract is stricter than the smallest reference:

- `savefig(dpi=650)` on every PNG.
- Single-column widths 6.5–7.5 in; no double-column figure has been produced yet.
- Every PNG ≥ 600 dpi and ≥ 3,000 px wide.
- White background, DejaVu Sans, bold axis labels, large titles, colorblind-friendly
  Okabe–Ito palette, no chartjunk.

### Palette

| Name | Hex | Use |
|---|---|---|
| Blue | `#0072B2` | primary data, protocol boxes |
| Sky | `#56B4E9` | baseline / warm-up boxes |
| Orange | `#E69F00` | calibration gate, pending banner |
| Green | `#009E73` | acceptance band, analysis box |
| Vermillion | `#D55E00` | failure / uncalibrated flag |
| Purple | `#CC79A7` | repeat-stability box |
| Grey | `#6E6E6E` | secondary text, arrows |
| Light grey | `#D9D9D9` | grid lines |
| Ink | `#1A1A1A` | text and spines |

---

## 2. Exact rcParams

`apply_style()` in `tools/paper/scripts/make_figures.py` is the source of truth. Current block:

```python
{
    "font.family": "DejaVu Sans",
    "font.size": 15,
    "mathtext.fontset": "dejavusans",
    "mathtext.default": "regular",
    "axes.titlesize": 18,
    "axes.titleweight": "bold",
    "axes.labelsize": 16,
    "axes.labelweight": "bold",
    "axes.edgecolor": "#1A1A1A",
    "axes.linewidth": 1.1,
    "axes.facecolor": "white",
    "axes.grid": False,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "xtick.major.size": 5,
    "ytick.major.size": 5,
    "xtick.major.width": 1.1,
    "ytick.major.width": 1.1,
    "legend.fontsize": 12,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 650,
    "figure.dpi": 110,
    "lines.linewidth": 2.2,
    "lines.markersize": 7,
    "grid.color": "#D9D9D9",
    "grid.linestyle": "--",
    "grid.linewidth": 0.7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}
```

Per-figure overrides:

- `p0_harness.png`: panel titles 17 pt, y labels 15/14.5 pt, ticks 12 pt.
- `p1_curve.png`: panel titles 18 pt, y labels 14 pt, x tick labels 10.5 pt. Panels use
  the seven depths equally spaced; panel (c) uses a log y axis.
- `p1_calibration.png`: title 19 pt, y label 14.5 pt, ticks 12 pt.
- `design.png`: title 19.5 pt, box text 12.3 pt, footnotes 8.8–10.2 pt. A dense
  eight-stage schematic cannot carry 14–16 pt body text at 7.2 in without overflow.

### Layout notes

- Data figures call `fig.tight_layout(rect=...)`; `rect` reserves space for the
  figure-level banner, shared x label, and provenance footer, which `tight_layout` does
  not see.
- `p0_harness.png` and the data-backed `p1_calibration.png` add
  `subplots_adjust(left=...)` after `tight_layout` to keep the rotated y label inside
  the canvas.
- `design.png` uses a full-canvas `add_axes((0, 0, 1, 1))` and manual box placement.
  Matplotlib 3.11 warns that this axes is not compatible with `tight_layout`; the
  manual layout is deterministic and is the only `tight_layout` exception.

---

## 3. Figure inventory

| File | `figsize` (in) | Pixels at 650 dpi | Status | Source |
|---|---|---|---:|---|
| `figures/design.png` | 7.2 × 8.8 | 4680 × 5720 | **Schematic** (no data) | `configs/grid/primary_k7.toml`, `configs/base.toml`, README/ROADMAP |
| `figures/p0_harness.png` | 7.5 × 5.0 | 4875 × 3250 | **P0 data-backed**, uncalibrated | `runs/golden_squad_qwen4b_p0_r3/raw.csv`; `docs/P0_HARNESS_REPORT.md` |
| `figures/p1_curve.png` | 7.5 × 5.4 | 4875 × 3510 | **P1 data-backed**, calibrated | `analysis/squad_qwen4b_p1/estimates.csv`, `bootstrap.json`, `noninferiority.json` |
| `figures/p1_calibration.png` | 7.0 × 4.6 | 4550 × 2990 | **P1 data-backed**, all pass | `runs/squad_qwen4b_p1/blocks.json`, `repeat.json` |

`main.tex` uses `figures/design.png`, `figures/p0_harness.png`, and
`figures/p1_curve.png`; `figures/p1_calibration.png` is available for the calibration
discussion.

### What each figure shows

**`design.png`** — eight-step P1 protocol: 1,000 SQuAD v1.1 dev questions → seven depths
`{0,1,2,4,8,16,32}` → 7,000 queries → idle baseline before warm-up → 20-query warm-up →
randomized sweep with a unique 10-hex nonce → seven-depth block calibration with the
`[0.8,1.4]` gate → `3 × 20` repeat at `k=8` → paired analysis with the 5 pp EM
non-inferiority test, `1 − E(4)/E(32) ≥ 20%` savings, and gates K1–K7/G1–G5.

**`p0_harness.png`** — (a) mean `j_gpu_raw` by depth with a 95% t interval over 200
questions per depth, explicitly labelled **UNCALIBRATED**; (b) the `k=0` block diagnostic:
`factor_csv = 0.7944` below the fixed `[0.8,1.4]` band, with `factor_block = 0.9989` and
`consistency = 1.2573`. No calibrated J curve is drawn because none exists.

**`p1_curve.png`** — calibrated P1 curves: (a) `A(k)` with the 5 pp gate band around
`A(32)`, (b) `J(k)` in J/query, (c) `E(k)` in J/correct on a log axis. Panel (a) marks
`k=4` and `k=32`; the figure-level annotation reports the primary result exactly:
`A(4)-A(32) = -4.30 pp`, one-sided lower `-6.17 pp`, 5 pp NI **not supported**, savings
`58.17%`.

**`p1_calibration.png`** — the seven `factor_csv` values against `[0.8,1.4]`; all pass.
The `k=0` point is annotated as marginal (`+0.0089`, `+1.1%` above the 0.80 floor), and
the repeat CV at `k=8` is shown (`median 2.81%`, `max 18.44%`).

---

## 4. P1 values and annotations used

All values are read from the registered P1 outputs; none is hand-typed into the script.

| Quantity | Value | Source |
|---|---:|---|
| Questions / rows | 1,000 per depth / 7,000 total | `estimates.csv`, `metadata.json` |
| Invalid rows | 0 | `metadata.json` |
| `A(4)` | 0.450 | `estimates.csv` |
| `A(32)` | 0.493 | `estimates.csv` |
| `A(4)-A(32)` | **-4.30 pp** | `noninferiority.json` (`mean_diff = -0.043`) |
| One-sided 95% lower bound | **-6.17 pp** | `noninferiority.json` (`lower_bound = -0.061702…`) |
| One-sided 95% upper bound | -2.43 pp | `noninferiority.json` |
| 5 pp NI verdict | **not supported** | `noninferiority.json` (`non_inferior: false`) |
| One-sided p | 0.2691 | `noninferiority.json` |
| Savings `1-E(4)/E(32)` | **58.17%** | `bootstrap.json`, `noninferiority.json` |
| Savings 95% bootstrap CI | [56.02, 60.14]% | `bootstrap.json` |
| Bootstrap `P(k*=4)` | 0.7244 | `bootstrap.json` |
| `factor_csv` by depth | 0.808899, 1.250626, 1.240312, 1.311107, 1.290241, 1.214256, 1.058708 | `blocks.json` |
| `k=0` margin over 0.80 | +0.008899 (**+1.1%**) | `blocks.json` |
| Repeat CV at `k=8` | median **2.81%**, max **18.44%** | `repeat.json` |
| Idle baseline | 15.79 W, CV 1.23% | `blocks.json` |

The 5 pp band in panel (a) spans `A(32) ± 5 pp = [0.443, 0.543]`. The point estimate
`A(4)=0.450` lies inside that band, but the **paired** one-sided lower bound (`-6.17 pp`)
is outside the 5 pp margin, so the gate is not met. The figure shows both facts; do not
read the shaded band alone as a pass.

Panel (c) omits `k=0` from the log-scale curve: `k=0` has 1/1,000 correct answers, so
`E(0)=14,585` J/correct and its bootstrap upper bound is infinite. The panel states this
in place.

### Gate context (not plotted, but relevant)

`G1` and `G2` fail; `K3` (`P(k*=4)=0.7244 < 0.8`) and `K5` (95% depth span 4, depths
`{4,8}`) fail. `K1`, `K2`, `K4`, `K7`, and `G3` pass. `K6`, `G4`, and `G5` are P2/P3
analyses and are not evaluated here. The paper may report a calibrated negative result;
it may not claim a positive 5 pp certification or a stable static `k*`.

---

## 5. Data provenance and the first-run P0 trap

`analysis/golden_squad_qwen4b_p0/estimates.csv` exists, but it belongs to the **first P0
run**, not the clean `_r3` rerun. It is not used by `p0_harness.png` or `p0_harness.tex`.
The difference is material: the first-run analysis reports `k=0` mean `J = 7.77 J`, while
`runs/golden_squad_qwen4b_p0_r3/raw.csv` gives `17.43 J`; at `k=32` the values are `76.15`
versus `84.94 J`. The figure and table recompute every value from the `_r3` raw CSV.

P0 constants in the scripts, each with a source comment:

| Constant | Value | Source |
|---|---:|---|
| `k=0` `factor_csv` | 0.7944 | `docs/P0_HARNESS_REPORT.md` §6 |
| `k=0` `factor_block` | 0.9989 | `docs/P0_HARNESS_REPORT.md` §6 |
| `k=0` `consistency` | 1.2573 | `docs/P0_HARNESS_REPORT.md` §6 |
| Acceptance band | `[0.8, 1.4]` | `docs/P0_HARNESS_REPORT.md` §3.1 |
| Idle mean / CV / n | 15.573 W / 1.12% / 551 | `runs/golden_squad_qwen4b_p0_r3/manifest.json` |

P0 is a harness check, not a paper result. The run is registered `invalid`; the J values
are uncalibrated because `j_gpu_calibrated ≡ j_gpu_raw`. Do not describe the P0 curve as a
calibrated energy result.

---

## 6. Commands

From `E:\PROJECT\energy-optimal-rag`:

```powershell
conda activate energy-optimal-rag

# Placeholder path: design + P0 + P1 placeholders
python tools/paper/scripts/make_figures.py

# Data-backed P1 result figures (current files)
python tools/paper/scripts/make_figures.py --p1

# Verify only
python tools/paper/scripts/make_figures.py --check

# Tables are separate from this figure task
python tools/paper/scripts/make_tables.py
```

`--p1` requires these registered sources and fails with a clear error if any is missing:

- `analysis/squad_qwen4b_p1/estimates.csv`
- `analysis/squad_qwen4b_p1/bootstrap.json`
- `analysis/squad_qwen4b_p1/noninferiority.json`
- `runs/squad_qwen4b_p1/blocks.json`
- `runs/squad_qwen4b_p1/repeat.json`

`--check` uses PIL and prints width, height, DPI, and width in inches. It exits non-zero
if any PNG is below 600 dpi or 3,000 px wide. Current output:

```text
file                      width  height     dpi  width_in
----------------------------------------------------------
design.png                 4680    5720   650.0      7.20
p0_harness.png             4875    3250   650.0      7.50
p1_curve.png               4875    3510   650.0      7.50
p1_calibration.png         4550    2990   650.0      7.00
----------------------------------------------------------
PASS: every PNG has dpi >= 600 and width >= 3000 px
```

Equivalent one-liner:

```powershell
python -c "from PIL import Image; import glob, os; [print(os.path.basename(f), Image.open(f).size, Image.open(f).info.get('dpi')) for f in sorted(glob.glob('paper/figures/*.png'))]"
```

Style/lint check:

```powershell
python -m ruff format tools/paper/scripts/make_figures.py tools/paper/scripts/make_tables.py
python -m ruff check tools/paper/scripts/make_figures.py tools/paper/scripts/make_tables.py
```

---

## 7. Missing sources and open items

| Expected source | Status on 2026-11-15 | Consequence |
|---|---|---|
| `runs/golden_squad_qwen4b_p0_r3/raw.csv` | present, 1,400 rows | P0 figure/table data |
| `runs/golden_squad_qwen4b_p0_r3/manifest.json` | present | idle mean/CV/n |
| `analysis/golden_squad_qwen4b_p0_r3/` | **missing** | no calibrated P0 analysis exists; P0 remains uncalibrated |
| `analysis/golden_squad_qwen4b_p0/estimates.csv` | present, first run only | **not used**; does not describe `_r3` |
| `analysis/squad_qwen4b_p1/estimates.csv` | present | P1 curves |
| `analysis/squad_qwen4b_p1/bootstrap.json` | present | A/E intervals, savings interval, `P(k*)` |
| `analysis/squad_qwen4b_p1/noninferiority.json` | present | primary NI verdict and bounds |
| `runs/squad_qwen4b_p1/blocks.json` | present | seven block factors |
| `runs/squad_qwen4b_p1/repeat.json` | present | repeat CV |
| `tools/paper/tables/p1_estimates.tex` | template/TBD in this figure task | run `make_tables.py` separately to fill it |
| `paper/main.tex`, `paper/supplement.tex` | present, **not modified** | their P1 text still needs reconciliation |

`paper/main.tex` currently describes P1 as pending in its P1 subsection; that text is
outside this task's write scope. The figures are ready for a data-backed rewrite of that
section.

---

## 8. Claim boundary

- P1 is calibrated: all seven `factor_csv` values pass `[0.8, 1.4]`.
- P1's 5 pp non-inferiority gate is **not met**: `A(4)-A(32) = -4.30 pp`, one-sided lower
  `-6.17 pp`, savings `58.17%`. This is a negative primary result, not a certification.
- `P(k*=4)=0.7244` is below the 0.8 stability threshold; `K3` and `K5` fail. Do not claim a
  stable static `k*`.
- P0 remains an uncalibrated harness failure and is not a paper result.
- No universal `k*`, no “2 pp optimal” claim, and no positive 5 pp claim are supported by
  these files.
