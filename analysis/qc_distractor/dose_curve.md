# Phase 8 Step 2 - distractor dose-response

Run `squad_qwen4b_qc_distractor`; 500 questions per dose, 4 question-aligned segments.

| dose | k-equiv | accuracy | 95% CI | J/query |
|---:|---:|---:|---|---|---:|
| 0 | 1 | 0.382 | [0.340, 0.425] | 19.64 |
| 1 | 2 | 0.408 | [0.366, 0.452] | 21.95 |
| 3 | 4 | 0.462 | [0.419, 0.506] | 26.63 |
| 7 | 8 | 0.490 | [0.446, 0.534] | 33.68 |
| 15 | 16 | 0.512 | [0.468, 0.556] | 50.75 |
| 31 | 32 | 0.528 | [0.484, 0.571] | 84.72 |

Trend: 3.06 pp per doubling (repeated-measures 3.06, 95% CI [1.43, 4.69]).
Rise dose 0 to 31: +14.6 pp (flat bound +-2 pp).

H-overload: **REJECTED: accuracy rises with dose (positive slope); reader overload at fixed gold rank 1 is not observed.**
