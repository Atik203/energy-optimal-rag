# P2 Results — Energy-tax arms (causal test of Corollary 1)

**Runs:** `fixed_a` and `per_passage_b` (150 SQuAD questions each, seven depths,
reader `qwen3.5:4b`). A calibrated dummy GPU workload raises the fixed cost `a`
by ~20% (fixed_a, delta 3.15 J) or the per-passage cost `b` by ~20%
(per_passage_b, delta 0.46 J/passage). The dummy work runs inside the per-query
NVML window, so its energy is measured, not asserted.

## Results

Fixed tax (raises `a`):

| k | A(k) | J(k) J/query |
|---:|---:|---:|
| 0 | 0.0000 | 23.82 |
| 1 | 0.4333 | 29.14 |
| 2 | 0.4667 | 30.81 |
| 4 | 0.5267 | 33.93 |
| 8 | 0.5333 | 41.72 |
| 16 | 0.5600 | 56.97 |
| 32 | 0.5867 | 92.56 |

Per-passage tax (raises `b`):

| k | A(k) | J(k) J/query |
|---:|---:|---:|
| 0 | 0.0000 | 21.53 |
| 1 | 0.4267 | 27.12 |
| 2 | 0.4667 | 29.30 |
| 4 | 0.5333 | 33.16 |
| 8 | 0.5267 | 41.88 |
| 16 | 0.5600 | 62.53 |
| 32 | 0.5733 | 107.73 |

## Energy measurement status

- Fixed_a: calibration missed `k=0` only (factor 0.798); repeat CV passed
  (median 3.93%, max 12.60%).
- Per_passage_b: calibration missed `k=0` only (factor 0.695); repeat CV passed
  (median 1.81%, max 4.98%).
- Energy is uncalibrated on both arms (k=0 miss) and uncertified.

## Corollary 1 test

The accuracy curves do not plateau on either arm (accuracy keeps rising to
k=32), so a clean `k*` shift is not identifiable from these data; the
prediction is not adjudicable as a pass. The tax did change the cost structure
as intended (fixed tax: J(0) 23.82 vs baseline ~18.9; per-passage tax: slope
2.62 vs baseline 2.28), but the accuracy side did not cooperate. Report as
inconclusive on the prediction, not as a confirmation or refutation.
