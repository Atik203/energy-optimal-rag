# Preregistration - measurement hardening (Phase 7)

**Status:** drafted 2026-11-25, **not yet frozen**.
**Freeze procedure:** review, then tag `prereg-measurement-v1` and record the SHA-256 of this
file in `configs/analysis/prereg.toml`. No Phase 7 outcome may be inspected before the tag.
**Supersedes nothing.** `prereg-freeze-v1` remains the frozen analysis for P1-P4 and is not
amended here.

## 1. Purpose and claim boundary

The per-query NVML window estimator is falsified (`docs/MEASUREMENT_VALIDITY.md`, D-028,
`docs/PHASE6_RESULTS.md`): the window sum recovers 81.7% of a continuous replay total, and the
`k=0` energy depends on the preceding depth by +24% to +82%. This study replaces the estimator.
It does not re-adjudicate any P1-P4 gate.

**Claimable after this study (only if the decision rules pass):**

- an energy-per-correct-answer estimate from block totals, with a cluster-bootstrap interval;
- a savings range for `k=4` against `k=32`;
- a statement about whether the calibration factor is depth-common.

**Not claimable, regardless of outcome:**

- any absolute joule figure as a deployment guarantee;
- any change to K1-K7, G1-G5, or the P1 verdict;
- any universal optimal depth;
- any energy claim from the H200 slice or a 16k allocation.

## 2. Hypotheses

| ID | Hypothesis | Falsified if |
|---|---|---|
| H-M1 | A continuous replay total agrees with the sum of constant-depth block totals within 3%. | The ratio lies outside `[0.97, 1.03]`. |
| H-M2 | Block-to-block CV of energy per query is at most 20% at `k >= 4`. | Any depth in `{4,8,16,32}` exceeds 20%. |
| H-M3 | Energy per query is affine in depth for `k >= 1`, with a positive slope. | Slope CI includes zero or is negative. |

The following are **reported, not gated**: the per-query window ratio (expected near 0.82), the
carryover coefficient, the depth-commensurability of the calibration factor, and the
system-to-GPU energy ratio.

## 3. Design

| Item | Value |
|---|---|
| Depths | `0, 1, 2, 4, 8, 16, 32` |
| Blocks per depth | 5 |
| Questions per block | 20, identical across blocks |
| Block order | Randomized, seed 20261115, recorded |
| Cooldown | 120 s before every block |
| Discarded queries | 2 per block, to restore steady state after cooldown |
| Measured generations | 700 |
| Total generations | 770 |
| Idle baseline | 60 s before the run; idle CV must be `<= 0.20` or the run stops |
| Replays | 10 continuous replays of a 140-query permutation (separate run ID) |
| Session variance | 3 sessions, `n = 200`, `k in {1,4,32}` (separate run ID) |
| Wall meter | `k in {1,4,32}`, 3 repeats x 100 queries, run last |

## 4. Estimator

For depth `k` with `B = 5` blocks:

```
E(k)  = sum_b J_block(k,b) / sum_b C(k,b)
Sav   = 1 - E(4) / E(32)
```

`J_block(k,b)` is the trapezoidal integral of NVML power over the block window minus
`idle_power_w` times the block duration. `C(k,b)` is the number of exact matches in the block.
The interval is a cluster bootstrap that resamples whole blocks with replacement inside each
depth (2,000 resamples, seed 20261115).

Per-query windows are computed and reported as a diagnostic only. They are never the estimator.

## 5. Precision

Five blocks per depth give a bootstrap interval whose expected half-width is 2-4 pp on the
savings ratio, given the observed block-to-block CV of 3-19% in P1. If the realized half-width
exceeds 6 pp, the result is reported as an interval and no point saving is quoted.

## 6. Exclusions

- A block is invalid if the reader reloads inside it (`load_s > 1.0`) or if fewer than two
  power samples are captured. An invalid block is rerun once, at the end of the schedule.
- A query is invalid if the request errors. Invalid queries stay in the denominator as wrong
  answers, matching the P1 rule, unless the whole block is invalid.
- No exclusion may depend on the observed energy or correctness.

## 7. Analysis

1. Block estimator for all seven depths; ratio of sums; cluster bootstrap.
2. CV per depth, reported as a distribution.
3. Affine fit on `k >= 1` with cluster-robust standard errors; `k=0` reported as a floor.
4. Replay ratios: `replay/block` and `per-query sum/replay`, each with a 95% interval over the
   10 replays.
5. Carryover regression on the sweep rows: `J_i = a + b k_i + g k_{i-1} + d temp_i + e clock_i`.
6. Session ICC from the three sessions.
7. Wall-meter ratio `system_J / (GPU_J + CPU_proxy)` as a range.

## 8. Decision rules (fixed before the run)

| Condition | Action |
|---|---|
| H-M1 holds and the savings interval clears 20% | Block estimate becomes the primary energy result |
| H-M1 fails by more than 3 pp | Report both estimators; demote absolute `J` to a range |
| H-M2 fails at any `k >= 4` | Report that depth as not measurable; do not quote its cost |
| `k=0` factor again within 2% of the 0.8 floor | Report `k=0` as a floor only; exclude it from every fit |
| Wall ratio varies with depth beyond its interval | Report GPU-only energy and retitle the quantity `E_GPU` |
| Any frozen gate would need a new threshold | Stop; the study is reported as inconclusive |

## 9. Deviations

| Date | Original | Replacement | Reason | Outcome seen? |
|---|---|---|---|---|
| - | - | - | - | - |

## 10. Freeze block

- File SHA-256: `TO-BE-FILLED-AT-FREEZE`
- Freeze tag: `TO-BE-FILLED-AT-FREEZE`
- Frozen by: Atikur Rahaman
- Date: `TO-BE-FILLED-AT-FREEZE`
