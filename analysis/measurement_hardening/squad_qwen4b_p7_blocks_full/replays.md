# Phase 7 - permutation replays

Run `squad_qwen4b_p7_blocks_full`; 10 replays of 20 questions per depth.

| replay | total ratio | saving % |
|---:|---:|---:|
| 0 | 1.036 | 73.85 |
| 1 | 1.010 | 75.48 |
| 2 | 0.876 | 79.41 |
| 3 | 0.846 | 78.98 |
| 4 | 0.848 | 77.78 |
| 5 | 0.831 | 78.82 |
| 6 | 0.921 | 80.09 |
| 7 | 0.821 | 80.11 |
| 8 | 0.786 | 80.07 |
| 9 | 0.821 | 78.32 |

Total replay/block: median 0.847 (range 0.786-1.036, CV 9.5%).
Saving implied by the replays: median 78.90% (range 73.85-80.11); block estimator 65.25%.

| depth | replay/block median | range |
|---:|---:|---|
| 0 | 0.837 | 0.809-1.299 |
| 1 | 0.469 | 0.423-0.653 |
| 2 | 0.469 | 0.410-0.604 |
| 4 | 0.502 | 0.431-0.606 |
| 8 | 0.529 | 0.491-0.664 |
| 16 | 0.649 | 0.604-0.696 |
| 32 | 0.820 | 0.751-0.847 |

Position trend: -0.0216 per replay (R2 0.609, Spearman rho -0.855).
