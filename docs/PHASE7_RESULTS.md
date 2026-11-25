# Phase 7 - block estimator: first run

**Run:** `squad_qwen4b_p7_blocks` · 2026-11-25 · prereg `ce7233d0` (`prereg-measurement-v1`)
**Design:** 7 depths x 5 randomized blocks x 20 questions, 120 s cooldown, 2 discarded queries.
**Idle:** 14.23 W, CV 0.009.
**Scripts:** `scripts/22_run_blocks_design.py`, `scripts/23_phase7_analysis.py`.

## Result

| k | A(k) | J/query | E (J/correct) | blocks | CV |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.000 | 7.11 | - | 5 | 0.072 |
| 1 | 0.350 | 17.62 | 50.35 | 5 | 0.036 |
| 2 | 0.550 | 18.87 | 34.31 | 5 | 0.023 |
| 4 | 0.650 | 24.84 | 38.21 | 5 | 0.024 |
| 8 | 0.650 | 35.57 | 54.73 | 5 | 0.027 |
| 16 | 0.530 | 56.58 | 106.76 | 5 | 0.019 |
| 32 | 0.590 | 92.76 | 157.23 | 5 | 0.018 |

Savings at `k=4` vs `k=32`: **75.70% [73.92, 77.33]**.
Affine on `k >= 1`: `J = 14.52 + 2.523k`, slope 95% CI `[2.329, 2.717]`.

## Gate status

| Hypothesis | Criterion | Result |
|---|---|---|
| H-M2 (block CV <= 20% at `k >= 4`) | 2.4%, 2.7%, 1.9%, 1.8% | **pass** |
| H-M3 (affine, positive slope, `k >= 1`) | slope CI excludes zero | **pass** |
| H-M1 (block agrees with sweep within 3 pp) | 75.70 vs 58.17 = **17.5 pp** | **fail** |

G7 therefore fails on convergence, exactly as the frozen decision rule anticipated. Per that
rule, both estimators are reported and absolute `J` is demoted to a range.

## Diagnosis: the failure is the denominator, not the energy

The energy measurement is clean: monotone in depth, block CV 1.8-3.6% at `k >= 4`, and a
positive affine slope. Two separate causes explain the 17.5 pp gap.

**1. The accuracy denominator is a 20-question subsample.** With 20 questions the accuracy
standard error is about 11 pp, and the observed curve is non-monotone:

- `A(4) = A(8) = 0.65`, `A(16) = 0.53`, `A(32) = 0.59`.

The full P1 sample gives 0.450, 0.467, 0.481, 0.493. The 20 questions are easier and noisier, so
`E(4)` is understated and the saving is overstated. The energy numerator is unaffected.

**2. The block estimator genuinely disagrees with the window estimator at short depths.**

| Quantity | Window (P1) | Block (P7) | Difference |
|---|---:|---:|---:|
| `J(4)` J/query | 36.25 | 24.84 | -31% |
| `J(32)` J/query | 94.95 | 92.76 | -2% |

The window overstates short-depth energy, which is what the falsification predicted: a 0.3 s
tail samples the previous query's elevated power, and the effect is largest where queries are
shortest. Substituting the full-sample accuracies into the block energies gives
`1 - (24.84/0.450)/(92.76/0.493) = 70.7%`, still above 58.17%. So the window estimator was
**conservative**: it understated the saving.

## What this means

- The qualitative claim (">20% saving") is robust to both estimators.
- The point saving is not identified by this run. The honest statement is a range across
  estimators: roughly **58% to 76%**, with the width driven by the accuracy denominator and by
  the short-depth window bias.
- No absolute joule figure becomes claimable yet.

## Recommended fix

Re-run the block design with a representative accuracy denominator: 7 depths x 5 blocks x
**200 disjoint questions** (1,000 per depth). That keeps block-level energy replication, gives
`A(k)` at `n = 1,000` per depth, and makes `E(k)` directly comparable to P1. Cost: 7,000
generations plus 35 cooldowns, about **3-3.5 GPU-h**.

Alternative, cheaper and weaker: 7 depths x 2 blocks x 500 questions (14 blocks, ~3 h), fewer
energy replicates.

## Manifest gaps found

- `nvidia-smi --query-gpu=cuda_version` is not a valid field; the value recorded is the error
  string. CUDA must be parsed from the `nvidia-smi` header.
- `ollama_version` is recorded as `unknown`; `/api/version` is available and should be queried.

Both are reporting defects, not measurement defects, and are fixed in the runner before the next
run.

## Artifacts

- `runs/squad_qwen4b_p7_blocks/` - `blocks_design.json`, `raw.csv`, `manifest.json`,
  `blocks_design.partial.jsonl` (local-only).
- `analysis/measurement_hardening/` - `estimates.json`, `affine.json`, `convergence.json`,
  `report.md`.
- `runs/registry.csv` - row `squad_qwen4b_p7_blocks`.
