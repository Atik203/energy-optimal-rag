# P3 Results — Query-conditional depth policy (negative)

**Data:** P1 sweep (`squad_qwen4b_p1`), 1,000 questions, seven depths, calibrated
energy. Split: 600 train / 200 validation / 200 test, seed `20261115`. Features
are computed before generation from the BM25 score distribution (top score,
second score, gap, mean, std, softmax entropy, number of positive scores) plus
question length. The policy is a per-depth logistic correctness model; it picks
the cheapest depth whose predicted correctness clears a threshold tuned only on
validation.

## Static baseline

The best static depth on validation by energy per correct answer is `k = 1`
(accuracy 0.400, `E = 63.37` J/correct). The test split gives `k = 1` accuracy
0.385 and `E = 65.71` J/correct.

## Policy and oracle on the held-out test split

| Method | Accuracy | J/correct | Saving vs static |
|---|---:|---:|---:|
| Static `k = 1` | 0.385 | 65.71 | — |
| Learned policy | 0.380 | 66.38 | −1.02% |
| Hindsight oracle (unconstrained) | 0.605 | 38.58 | 41.28% |
| Hindsight oracle (matched accuracy) | 0.385 | 45.63 | 30.56% |

The tuned confidence threshold is 0.05, so the policy almost always falls back
to the static depth. It captures **−2.48%** of the unconstrained oracle gap and
**−3.35%** of the matched-accuracy gap.

## G4 adjudication

G4 requires an oracle gain of at least 20% and a policy capture of at least 50%
at matched accuracy. The oracle gain condition is met (30.56% matched; 41.28%
unconstrained), but the policy capture condition fails (−3.35% matched; −2.48%
unconstrained), so **G4 is not supported** and no adaptive claim is made.

## Caveats

- The unconstrained oracle accuracy (0.605) is higher than the static accuracy
  (0.385), so its 41.28% gain is not a matched-accuracy quantity. The
  matched-accuracy oracle holds accuracy at 0.385 and still gives a 30.56% gap,
  which the policy also fails to capture.
- The negative result is for this feature set and policy class (BM25-only
  logistic models). It does not prove that no query-conditional policy can work.
- The test split was evaluated once; the threshold was tuned on validation only.

## Artifacts

- `analysis/policy/policy.json`
- `analysis/policy/report.md`
- `scripts/07_train_policy.py`
- `src/rag_energy/stats/policy.py`
