# P0 sweep analysis - fixed_a

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct |
|---:|---:|---:|---:|---:|---:|
| 0 | 150 | 0 | 0.0000 | 23.82 | inf |
| 1 | 150 | 0 | 0.4333 | 29.14 | 67.25 |
| 2 | 150 | 0 | 0.4667 | 30.81 | 66.03 |
| 4 | 150 | 0 | 0.5267 | 33.93 | 64.42 |
| 8 | 150 | 0 | 0.5333 | 41.72 | 78.23 |
| 16 | 150 | 0 | 0.5600 | 56.97 | 101.73 |
| 32 | 150 | 0 | 0.5867 | 92.56 | 157.78 |

Affine fit: `J(k) = 25.4920 + 2.0717 k`, R² = 0.9970.
Calibration: **not applied**.
P0 anchor check: **FAIL**.
The anchor check is not adjudicable as a clean energy test.
