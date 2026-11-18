# P2 replication analysis - hotpot_qwen4b_p2

Calibration: **not applied** (all depths passed: False).

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct | S(k) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 500 | 0 | 0.0080 | 19.53 | 2441.32 | 0.000 |
| 1 | 500 | 0 | 0.2000 | 22.05 | 110.26 | 0.147 |
| 2 | 500 | 0 | 0.2860 | 25.41 | 88.84 | 0.254 |
| 4 | 500 | 0 | 0.4100 | 31.46 | 76.74 | 0.411 |
| 8 | 500 | 0 | 0.4880 | 44.64 | 91.47 | 0.579 |
| 10 | 500 | 0 | 0.5180 | 51.65 | 99.70 | 0.625 |

Affine descriptive fit: `J(k) = 19.0097 + 3.2272 k`, R2 = 0.9992; quadratic lack-of-fit p = 0.0239.

## H7 direction replication

- Paired n = 500; discordant b = 12, c = 66; invalid at k=4/k=32 = 0/0.
- Mean difference A(4) - A(32) = -10.80 pp (one-sided 95% upper bound -8.00 pp).
- Directional one-sided p (null: contrast >= 0) = 0.000000.
- Point estimate matches P1's negative direction: True.
- **H7 supported (whole directional interval negative): True.**

The 5 pp non-inferiority test is secondary and not powered on this arm: lower bound -13.60 pp, p = 0.999675527281835, non-inferior = False.

## Energy contrast

- Savings 1 - E(4)/E(32) = 23.03% (95% CI 16.74 to 28.50%).
- P(k* optimal) = {"0": 0.0, "1": 0.0, "10": 0.0619, "2": 0.0, "4": 0.0002, "8": 0.9379, "none": 0.0}.

P1 reference: -4.30 pp (one-sided lower -6.17 pp); direction negative.

H7 is direction-only. This arm does not certify 5 pp, does not set a universal k*, and does not change the P1 negative decision.
