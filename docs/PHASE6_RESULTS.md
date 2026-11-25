# Phase 6 - Inference repair and reframe (results)

**Status:** complete 2026-11-25. CPU-only re-analysis of registered rows. No new
measurements, no gate changes, no re-thresholding.
**Generator:** `scripts/21_phase6_inference.py` (seed 20261115, bootstrap 2,000).
**Outputs:** `analysis/phase6/*.json` and `analysis/phase6/report.md`.
**Tests:** `tests/test_phase6_inference.py` (6 tests on the cluster-robust and OLS helpers).
**Claims:** `artifacts/claims_evidence.csv` C-052 to C-057.

## Why this phase exists

The Q1 audit found three places where a methods reviewer would find an *error* rather than a
limitation: an unclustered interval, a silently misspecified power calculation, and a
selection procedure that was never checked out of sample. It also found that the P3 "capture"
denominator did not match the gap it was supposed to describe. Phase 6 fixes all four using
data already on disk.

## 1. Context clustering

SQuAD has several questions per article. The 1,000 P1 questions fall in **806 contexts**
(median cluster size 1, max 5), so clustering is weak but not absent.

| Quantity | Value |
|---|---|
| Mean `A(4)-A(32)` | -4.30 pp |
| iid SE | 1.14 pp |
| cluster SE | 1.13 pp |
| Design effect | **0.98** |
| Cluster 95% CI | [-6.51, -2.09] pp |
| Cluster one-sided lower | -6.15 pp |

**Reading:** clustering does not widen the interval on this sample. The negative result is
not an artefact of treating questions as independent. Report the cluster interval, not the
iid one, because it is the defensible choice.

## 2. Depth or tokens (this changes the H1 story)

Prompt length, not passage count as such, carries the energy.

| Model | R2 | BIC | Coefficient |
|---|---|---|---|
| `J = a + b k` | 0.8878 | 30,211.6 | b = 2.2772 (cluster SE 0.0101) |
| `J = a + c T` | **0.9017** | **29,290.0** | c = 0.0272 J/token (cluster SE 0.0001) |
| `J = a + b k + c T` | 0.9017 | 29,296.7 | b = **-0.1117** (SE 0.1059); c = 0.0285 |

`corr(k, T) = 0.993`; mean prompt tokens rise 86 -> 2,769 from `k=0` to `k=32`.

**Reading:** conditional on tokens, depth adds nothing (coefficient indistinguishable from
zero, slightly negative). Depth is the control knob; context length is the physical cost.
Consequence for the paper: H1 stays "supported" as an affine description, but the mechanism
sentence must say *tokens*, and the transfer argument should be phrased per token, not per
passage.

## 3. Affine fit with uncertainty, `k >= 1`

The `k=0` point is a floor (1 correct in 1,000) and was dragging the intercept down.

| Fit | Intercept `a` | Slope `b` |
|---|---|---|
| Six positive depths (weighted) | 26.90 [25.85, 27.95] | 2.149 [2.055, 2.243] |
| All seven depths (reported previously) | 24.0759 | 2.2772 |

Weighted `R2 = 0.999` on the six positive depths. Both fits are now reported; the paper quotes
the `k >= 1` fit with intervals and keeps the seven-depth fit as the historical number.

## 4. Cross-fitted selection

Rule: smallest depth clearing 5 pp and 20% savings on four folds, scored on the fifth.

| Quantity | Value |
|---|---|
| Selected depth by fold | `[4, 4, 4, 4, 4]` |
| Mean held-out saving | **58.13%** (SD 1.96) |
| Winner's curse | **0.03 pp** |

**Reading:** the *deployment* choice is stable; the preregistered bootstrap stability gate
(K3, `P(k*) >= 0.8`) still fails at 0.7244 because resampling the argmin is a stricter
question. Both statements are now in the paper, and the distinction is explicit. This is
*not* a re-threshold: 0.8 remains failed.

## 5. P3 capture: the denominator was wrong

The registered `matched_oracle_gap_captured_pct = -2.46%` divided the policy saving
(`-0.71%`) by the **abstention-inclusive** gap (28.64%), while being described as the
non-abstention capture.

| Quantity | Value |
|---|---|
| Policy saving vs static `k=1` | -0.71% |
| Matched no-abstention gap | 7.21% |
| Capture (correct denominator) | **-9.8%** [-22.8, -1.8] |
| Capture (registered, abstention denominator) | -2.46% |

**Reading:** direction unchanged (the policy loses), magnitude corrected, and the interval is
now reported. A second observation is more important than the correction: **with fixed
per-depth costs the same oracle has a 0.000% gap against `k=1`**, because every question
already starts at the cheapest depth. The 7.21% figure is per-query energy noise, not routing
headroom. Routing headroom must be measured against a *deeper* baseline (Phase 8 retargets
to `k=4`: 22.5% on the full P1 rows).

## 6. Reader overload, tested directly

590 of the 1,000 questions (59.0%) have the gold passage at rank 1 under BM25.

| Quantity | `k=1` | `k=32` | Difference |
|---|---|---|---|
| Exact match, gold first | 0.6525 | 0.6153 | **+3.73 pp** [0.73, 6.72] |

**Reading:** when the answer is already in the prompt at rank 1, adding 31 distractors still
costs 3.73 pp. That cannot be a retrieval failure. It is direct evidence for reader overload
and for the "knee" framing.

## 7. Three readers on identical questions

The 500 P2 question IDs are shared by all three SQuAD readers, so the heterogeneity is not
confounded by different questions.

| Reader | `A(4)` | `A(32)` | `A(4)-A(32)` | 95% CI |
|---|---|---|---|---|
| Qwen3.5-4B | 0.488 | 0.516 | **-2.80 pp** | [-5.93, +0.33] |
| Qwen2.5-1.5B | 0.360 | 0.340 | +2.00 pp | [-1.46, +5.46] |
| Llama-3.2-3B | 0.476 | 0.426 | **+5.00 pp** | [+1.63, +8.37] |

**Reading:** depth tolerance falls with reader capability. The 4B reader is the only arm where
the deeper prompt is still better; both weaker readers prefer `k=4`. The Llama interval
excludes zero. This replaces "the direction did not replicate" with a defensible
reader-conditional statement, and H7 on the 1.5B arm is now labelled **inconclusive**, not
reversed.

## 8. Cancellation decomposition

From `k=4` to the maximum depth, in pp:

| Arm | `dR` | `dQ` | `Q(4)dR` | `R(max)dQ` | Net |
|---|---:|---:|---:|---:|---:|
| P1 Qwen4B (4->32) | +11.7 | -2.8 | +6.8 | -2.5 | +4.3 |
| Qwen1.5B (4->32) | +11.4 | -8.0 | +5.2 | -7.2 | -2.0 |
| Llama 3B (4->32) | +11.4 | -13.3 | +6.9 | -12.0 | -5.0 |
| HotpotQA (4->10) | +5.6 | +8.4 | +2.4 | +8.4 | +10.8 |

**Reading:** the recall term is stable (+2.4 to +6.9); the precision term swings 20 pp. The
sign of the depth effect is set by precision. This is now Table `tab:cancel` in the paper.

## 9. Price of the guarantee

Tightening the accuracy margin costs savings:

| Tighten | Savings lost |
|---|---|
| 10 -> 8 pp | 0.00 pp |
| 8 -> 6 pp | 3.75 pp |
| 6 -> 5 pp | 0.00 pp |
| 5 -> 4 pp | 0.00 pp |
| 4 -> 3 pp | 7.80 pp |
| 3 -> 2 pp | 17.49 pp |

**Reading:** the marginal price of accuracy rises sharply below 5 pp, which makes 5 pp the
cheapest defensible guarantee on this curve rather than an arbitrary choice.

## 10. Paper changes made

- Abstract: 1.5B now "inconclusive" with the two-sided interval; capture corrected; cancellation
  and gold-first overload added.
- Results: cluster-robust sentence; `26.90 + 2.149k` with intervals; new "Depth or tokens?"
  paragraph; cross-fitted selection paragraph; G4 capture corrected in text, table, and claim
  map; P2 reframed; new same-ID reader paragraph; cancellation table; gold-first test;
  price-of-guarantee sentence.
- Removed to hold the 30-page limit: the reporting-checklist table and the `sim_ratio` figure.
- Figure count: 8 -> 7 (`docs/paper/FIGURES.md`, `docs/paper/README.md` updated).

## 11. What Phase 6 did not do

- No new data, so no absolute joule claim is revived.
- No re-thresholding: K3 stays failed at 0.8; the exploratory 0.6 discussion is not used.
- The per-query window estimator is still falsified; Phase 7 replaces it with a block estimator.
- The router is still unproven; Phase 8 retargets it to the 22.5% gap against `k=4`.

## 12. Reproduction

```powershell
python scripts\21_phase6_inference.py
pytest -q
```

Expected: nine JSON files plus `report.md` in `analysis/phase6/`; 426 tests pass.
