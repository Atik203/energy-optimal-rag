# Measurement validity: per-query window bias

**Date:** 2026-11-19. Diagnostic only; no registered gate is changed.

## Probe

`scripts/14_power_probe.py` ran 20 queries per depth on Qwen2.5-1.5B with a
continuous NVML sampler and a 3 s quiet window after each query. The pre-run
idle was 15.48 W (CV 0.14%). The power signal did **not** return to idle within
3 s:

| k | pre-query net W | 0.0–0.2 s | 0.6–1.0 s | 2.0–3.0 s |
|---:|---:|---:|---:|---:|
| 0 | 5.3 | 6.4 | 8.8 | 5.0 |
| 1 | 6.3 | 7.9 | 10.5 | 5.6 |
| 2 | 7.2 | 9.2 | 13.0 | 6.0 |
| 4 | 9.7 | 13.7 | 18.9 | 8.2 |
| 8 | 15.9 | 20.7 | 27.5 | 10.3 |
| 16 | 31.5 | 37.0 | 36.6 | 10.7 |
| 32 | 63.8 | 61.1 | 40.1 | 14.6 |

The pre-query floor is 5–64 W above the pre-run idle and depends on the previous
depth. A 0.3 s tail therefore measures the neighbour's power level, not the
current query alone.

## Replay discriminator

`scripts/15_replay.py` replayed the sweep's exact 20-question depth permutation
as one continuous block:

- replay total: **7,336.9 J** over 140 queries (142.1 s)
- sum of the seven constant-depth blocks: **7,195.7 J**
- ratio: **1.020**

The continuous replay is within 2% of the constant-depth blocks. The sweep's
per-query sum is much larger (e.g. Qwen1.5B k=0 19.7 J/query vs block 5.1
J/query). The gap is a **window-estimator bias**, not extra work.

## Neighbour dependence

`analysis/calibration_bias.json` shows that `k=0` energy depends on the
preceding row's depth:

| Arm | previous depth 1 | previous depth 32 | swing |
|---|---:|---:|---:|
| P1 Qwen4B | 15.75 J | 19.59 J | +24% |
| Qwen1.5B | 14.66 J | 21.73 J | +48% |
| HotpotQA | 17.64 J | 21.51 J | +22% |
| Llama 3B | 12.84 J | 23.33 J | +82% |

A query's measured energy must not depend on which query preceded it. This is
the internal falsification of the per-query estimator at short depths.

## Bounded savings

Savings computed from sweep means and from block means (same accuracy):

| Arm | Contrast | Sweep | Block |
|---|---|---:|---:|
| P1 Qwen4B | 4 vs 32 | 68.5% | 64.3% |
| Qwen1.5B | 4 vs 32 | 92.1% | 90.9% |
| HotpotQA | 4 vs 10 | 23.0% | 31.4% |
| Llama 3B | 4 vs 32 | 68.9% | 77.3% |

The qualitative saving is robust: every arm is above the 20% floor under both
estimators. The point value is not: P1's 58.17% calibrated figure is
conservative relative to both, while HotpotQA's 23.03% becomes 23.0–31.4%.

## Consequences

- The block gate is doing its job: it rejects an estimator that is not
  invariant to the query sequence.
- P2 energy remains uncalibrated. The correct statement is a range, not a
  point.
- P1's all-seven pass is marginal: `k=0` is 0.8089, 1.1% above the floor, and
  the same bias is present. P1's absolute `J` is **provisional**; the accuracy
  contrast and the qualitative savings are unaffected.
- A correct future estimator must either replay the sweep sequence or bracket
  each query with a locally measured floor. A fixed 0.3 s tail is not enough.
