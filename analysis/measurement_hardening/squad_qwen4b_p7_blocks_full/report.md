# Phase 7 - block estimator

Run `squad_qwen4b_p7_blocks_full`; 35 blocks.

| k | A(k) | J/query | E (J/correct) | blocks | CV |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.0020 | 8.59 | 4295.39 | 5 | 0.036 |
| 1 | 0.3860 | 20.40 | 52.84 | 5 | 0.070 |
| 2 | 0.4200 | 22.65 | 53.92 | 5 | 0.052 |
| 4 | 0.4590 | 28.33 | 61.72 | 5 | 0.043 |
| 8 | 0.4650 | 37.44 | 80.52 | 5 | 0.040 |
| 16 | 0.4790 | 54.50 | 113.78 | 5 | 0.043 |
| 32 | 0.4900 | 87.04 | 177.64 | 5 | 0.012 |

Savings at k=4 vs k=32: 65.25% [61.27, 69.11]

| k | saving vs k=32 | 95% CI |
|---:|---:|---:|
| 1 | 70.26% | [66.63, 74.19] |
| 2 | 69.65% | [66.00, 72.46] |
| 4 | 65.25% | [61.27, 69.11] |
| 8 | 54.67% | [49.58, 59.18] |
| 16 | 35.95% | [30.01, 41.25] |

Affine (k>=1): a = 19.15 J, b = 2.131 J/passage, 95% b interval [2.043, 2.219].

| reference | saving | gap (pp) | verdict at 3 pp |
|---|---:|---:|---|
| sweep | 58.17% | 7.08 | disagree |
| block calibration | 64.30% | 0.95 | agree |
| raw window | 68.47% | 3.22 | disagree |

G7 replay agreement: 1/3 references agree; fails, so absolute energy stays a range.
