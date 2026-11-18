# Query-conditional depth policy

Split: 600 train / 200 validation / 200 test.
Best static depth on validation: k=1 (accuracy 0.4000).
Policy confidence threshold: 0.05.

| Split | Method | Accuracy | J/correct | Saving vs static |
|---|---|---:|---:|---:|
| test | static k=1 | 0.3850 | 65.71 | — |
| test | policy | 0.3800 | 66.38 | -1.02% |
| test | oracle | 0.6050 | 38.58 | 41.28% |

Oracle gap captured by the policy: -2.48%.

G4 requires an oracle gain of at least 20% and a policy capture of at least 50% at matched accuracy. The test split is used once.
