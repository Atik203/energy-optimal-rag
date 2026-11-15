# P0 sweep analysis - squad_qwen4b_ctx16k_p2

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct |
|---:|---:|---:|---:|---:|---:|
| 32 | 200 | 0 | 0.4750 | 87.90 | 185.05 |
| 48 | 200 | 0 | 0.4850 | 125.32 | 258.39 |
| 64 | 200 | 0 | 0.5000 | 163.98 | 327.96 |

Affine fit: `J(k) = 11.6083 + 2.3776 k`, R² = 0.9999.
Calibration: **not applied**.
P0 anchor check: **FAIL**.
The anchor check is not adjudicable as a clean energy test.
