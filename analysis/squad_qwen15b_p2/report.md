# P2 replication analysis - squad_qwen15b_p2

Calibration: **not applied** (all depths passed: False).

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct | S(k) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 500 | 0 | 0.0080 | 18.90 | 2362.47 | 0.000 |
| 1 | 500 | 0 | 0.3160 | 31.55 | 99.84 | 0.471 |
| 2 | 500 | 0 | 0.3320 | 35.16 | 105.90 | 0.736 |
| 4 | 500 | 0 | 0.3600 | 37.28 | 103.57 | 1.286 |
| 8 | 500 | 0 | 0.3380 | 46.34 | 137.09 | 1.986 |
| 16 | 500 | 0 | 0.3660 | 65.27 | 178.32 | 2.762 |
| 32 | 500 | 0 | 0.3400 | 401.83 | 1181.85 | 0.888 |

Affine descriptive fit: `J(k) = -8.3172 + 11.0245 k`, R2 = 0.8507; quadratic lack-of-fit p = 0.0022.

## H7 direction replication

- Paired n = 500; discordant b = 44, c = 34; invalid at k=4/k=32 = 0/0.
- Mean difference A(4) - A(32) = 2.00 pp (one-sided 95% upper bound 4.90 pp).
- Directional one-sided p (null: contrast >= 0) = 0.871308.
- Point estimate matches P1's negative direction: False.
- **H7 supported (whole directional interval negative): False.**

The 5 pp non-inferiority test is secondary and not powered on this arm: lower bound -0.90 pp, p = 3.683821260436204e-05, non-inferior = True.

## Energy contrast

- Savings 1 - E(4)/E(32) = 91.24% (95% CI 89.93 to 92.36%).
- P(k* optimal) = {"0": 0.0, "1": 0.6647, "16": 0.0, "2": 0.0777, "32": 0.0, "4": 0.2576, "8": 0.0, "none": 0.0}.

P1 reference: -4.30 pp (one-sided lower -6.17 pp); direction negative.

H7 is direction-only. This arm does not certify 5 pp, does not set a universal k*, and does not change the P1 negative decision.
