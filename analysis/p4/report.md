# P4 theory validation

## squad_qwen4b_p1

- Rows: 7000; depths: [0, 1, 2, 4, 8, 16, 32].
- Accuracy monotone: True.
- Affine fit: `J = 24.0759 + 2.2772 k`, R2 = 0.9714, lack-of-fit p = 0.2813.
- Coverage fit: a0 = 0.31, p = 0.015, R2 = 0.2726.
- Identity gaps: k=0: 0.000 (forward), k=1: -0.446 (central), k=2: 0.065 (central), k=4: 0.200 (central), k=8: 0.386 (central), k=16: 0.566 (central), k=32: 0.703 (backward).

## squad_qwen15b_p2

- Rows: 3500; depths: [0, 1, 2, 4, 8, 16, 32].
- Accuracy monotone: False.
- Affine fit: `J = -8.3172 + 11.0245 k`, R2 = 0.8507, lack-of-fit p = 0.0022.
- Coverage fit: a0 = 0.25, p = 0.007, R2 = 0.1514.
- Identity gaps: k=0: -0.000 (forward), k=1: 3.559 (central), k=2: 1.517 (central), k=4: 1.221 (central), k=8: 1.092 (central), k=16: 1.046 (central), k=32: 1.177 (backward).

## hotpot_qwen4b_p2

- Rows: 3000; depths: [0, 1, 2, 4, 8, 10].
- Accuracy monotone: True.
- Affine fit: `J = 19.0097 + 3.2272 k`, R2 = 0.9992, lack-of-fit p = 0.0239.
- Coverage fit: a0 = 0.10, p = 0.073, R2 = 0.8789.
- Identity gaps: k=0: 0.000 (forward), k=1: -0.550 (central), k=2: -0.236 (central), k=4: 0.076 (central), k=8: 0.281 (central), k=10: 0.340 (backward).

## squad_llama3b_p2

- Rows: 3500; depths: [0, 1, 2, 4, 8, 16, 32].
- Accuracy monotone: False.
- Affine fit: `J = 18.3533 + 1.3618 k`, R2 = 0.9907, lack-of-fit p = 0.3171.
- Coverage fit: a0 = 0.34, p = 0.008, R2 = 0.0966.
- Identity gaps: k=0: 0.000 (forward), k=1: -0.479 (central), k=2: 0.042 (central), k=4: 0.218 (central), k=8: 0.427 (central), k=16: 0.604 (central), k=32: 0.760 (backward).

