# Phase 8 - distractor dose-response

Run `squad_qwen4b_qc_distractor` (qc-distractor-v1); 6 blocks, 500 paired questions per block.

| dose | k-equiv | accuracy | J/query |
|---:|---:|---:|---:|
| 0 | 1 | 0.382 | 19.64 |
| 1 | 2 | 0.408 | 21.95 |
| 3 | 4 | 0.462 | 26.63 |
| 7 | 8 | 0.490 | 33.68 |
| 15 | 16 | 0.512 | 50.75 |
| 31 | 32 | 0.528 | 84.72 |

Trend slope: 0.0306 accuracy points per doubling of (dose + 1).
