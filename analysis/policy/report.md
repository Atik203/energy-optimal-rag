# Query-conditional depth policy

Split: 608 train / 206 validation / 186 test.
Best static depth on validation: k=1 (accuracy 0.3835).
Policy confidence threshold: 0.05.

| Split | Method | Accuracy | J/correct | Saving vs static |
|---|---|---:|---:|---:|
| test | static k=1 | 0.4194 | 59.57 | — |
| test | policy | 0.4194 | 59.99 | -0.71% |
| test | oracle (unconstrained) | 0.6667 | 37.65 | 36.80% |
| test | oracle (matched accuracy) | 0.4194 | 42.51 | 28.64% |

Oracle gap captured by the policy (unconstrained oracle): -1.92%.
Oracle gap captured by the policy (matched oracle): -2.46%.

G4 requires an oracle gain of at least 20% and a policy capture of at least 50% at matched accuracy. The test split is used once.
