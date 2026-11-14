# P0 sweep analysis - golden_squad_qwen4b_p0

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct |
|---:|---:|---:|---:|---:|---:|
| 0 | 200 | 0 | 0.0000 | 7.77 | inf |
| 1 | 200 | 0 | 0.4500 | 15.18 | 33.73 |
| 2 | 200 | 0 | 0.4800 | 16.69 | 34.77 |
| 4 | 200 | 0 | 0.5050 | 19.80 | 39.21 |
| 8 | 200 | 0 | 0.5150 | 27.13 | 52.68 |
| 16 | 200 | 0 | 0.5550 | 42.41 | 76.41 |
| 32 | 200 | 0 | 0.5250 | 76.15 | 145.05 |

Affine fit: `J(k) = 11.1023 + 2.0225 k`, R² = 0.9941.
Calibration: **not applied**.
P0 anchor check: **FAIL**.
The anchor check is not adjudicable as a clean energy test.
