# Exploratory inference layer - squad_qwen4b_p1

All numbers below are **exploratory or sensitivity** analysis. The preregistered 5 pp verdict is unchanged.

## Primary (confirmatory, unchanged)

- Paired n = 1000; b = 44, c = 87; discordance = 0.1310.
- Mean difference A(4) - A(32) = -4.30 pp; one-sided lower bound -6.17 pp.
- Preregistered Wald z = 0.6156, p = 0.2691; verdict: **not supported**.

## Score and exact sensitivity

| Test | z | p (one-sided) | Non-inferior |
|---|---:|---:|---|
| Wald (preregistered) | 0.6156 | 0.2691 | False |
| Restricted-MLE score | 0.6120 | 0.2703 | False |
| Exact unconditional | - | 0.4182 | False |
| Exact conditional | - | 0.3112 | False |

## TOST

| Margin | p | Equivalence |
|---:|---:|---|
| +/-5 pp | 0.2691 | False |
| +/-2 pp | 0.9785 | False |

## Power at the observed discordance

| True d (pp) | Realized power | n at 50% | n at 80% |
|---:|---:|---:|---:|
| 0.0 | 0.9968 | 142 | 324 |
| -1.0 | 0.9679 | 222 | 506 |
| -2.0 | 0.8365 | 393 | 898 |
| -3.0 | 0.5432 | 880 | 2011 |
| -4.3 | 0.1518 | 7132 | 16296 |

MDE at 80% power: a true loss of 2.16 pp is the largest this design can still certify.

## BCa intervals

- Mean difference: -6.60 to -2.20 pp.
- Savings: 55.99 to 60.10%.

## Joint bootstrap

- P(NI and savings >= 20%) = 0.1540 over 10000 resamples.
- P(NI) = 0.1540; P(savings >= 20%) = 1.0000.
- Cluster bootstrap: skipped (the raw CSV has no 'context_id' column; P1 questions are independent and no clustering is defined).
