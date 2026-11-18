# P0 sweep analysis - boundary_qwen4b_p2

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct |
|---:|---:|---:|---:|---:|---:|
| 32 | 200 | 0 | 0.4750 | 98.41 | 207.18 |
| 48 | 200 | 0 | 0.4850 | 134.55 | 277.42 |
| 64 | 200 | 0 | 0.5050 | 169.39 | 335.42 |

Affine fit: `J(k) = 27.6550 + 2.2179 k`, R² = 0.9999.
Calibration: **applied**.
P0 anchor check: **FAIL**.
