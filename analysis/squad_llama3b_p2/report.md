# P0 sweep analysis - squad_llama3b_p2

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct |
|---:|---:|---:|---:|---:|---:|
| 0 | 500 | 0 | 0.0020 | 16.49 | 8245.68 |
| 1 | 500 | 0 | 0.4160 | 21.29 | 51.17 |
| 2 | 500 | 0 | 0.4580 | 22.61 | 49.37 |
| 4 | 500 | 0 | 0.4760 | 24.34 | 51.14 |
| 8 | 500 | 0 | 0.4660 | 28.43 | 61.01 |
| 16 | 500 | 0 | 0.4380 | 38.22 | 87.26 |
| 32 | 500 | 0 | 0.4260 | 62.88 | 147.62 |

Affine fit: `J(k) = 18.3533 + 1.3618 k`, R² = 0.9907.
Calibration: **not applied**.
P0 anchor check: **FAIL**.
The anchor check is not adjudicable as a clean energy test.
