# Phase 9 - token attribution

Run `squad_qwen4b_p1`; 7000 requests.

| k | prefill s | eval s | prompt tok | J/prefill-tok (mJ) |
|---:|---:|---:|---:|---:|
| 0 | 0.098 | 0.021 | 86 | 169.07 |
| 1 | 0.130 | 0.070 | 166 | 150.99 |
| 2 | 0.161 | 0.075 | 250 | 107.26 |
| 4 | 0.231 | 0.086 | 417 | 77.95 |
| 8 | 0.386 | 0.094 | 750 | 54.52 |
| 16 | 0.717 | 0.106 | 1424 | 41.03 |
| 32 | 1.474 | 0.114 | 2769 | 32.93 |

J/prefill-token constancy: max/min = 5.134.
Under J = a + b*T this ratio must fall with T (fixed cost amortized); the test is the token model against the depth model:
Depth model J = 21.25 + 2.2348k, R2 = 0.8965.
Token model J = 13.88 + 0.02549*Tpre + 1.135*Tdec, R2 = 0.9575.
Marginal prefill cost is about 25 mJ/token; decode about 1.1 J/token.
