# Phase 8 Step 3 - dense 2x2 DiD

BM25 `squad_qwen4b_p7_blocks_full` (n=1000) vs dense `squad_qwen4b_qc_dense` (n=1000).

| arm | R(4) | R(32) | Q(4) | Q(32) | A(4) | A(32) |
|---|---|---|---|---|---|---|
| bm25 | 0.775 | 0.892 | 0.592 | 0.549 | 0.459 | 0.490 |
| dense | 0.711 | 0.884 | 0.620 | 0.559 | 0.441 | 0.494 |

DiD = -2.20 pp [-5.40, +1.00].

DiD includes zero (TOST at +-2 pp decides equivalence); reported as a null finding, not a failure.
