# P3 Results — Query-conditional depth policy (negative)

**Data:** P1 sweep (`squad_qwen4b_p1`), 1,000 questions, seven depths, calibrated
energy. Split: deterministic SHA-256 assignment of `seed:question_id` (608
train / 206 validation / 186 test), seed `20261115`. Features are computed before
generation from the BM25 score distribution (top score, second score, gap, mean,
std, softmax entropy, number of positive scores), question length, and question
type. The policy is a per-depth logistic correctness model; it picks the cheapest
depth whose predicted correctness clears a threshold tuned only on validation.

## Static baseline

The best static depth on validation by energy per correct answer is `k = 1`
(accuracy 0.3835). The test split gives `k = 1` accuracy 0.4194 and `E = 59.57`
J/correct.

## Policy and oracle on the held-out test split

| Method | Accuracy | J/correct | Saving vs static |
|---|---:|---:|---:|
| Static `k = 1` | 0.4194 | 59.57 | — |
| Learned policy | 0.4194 | 59.99 | −0.71% |
| Hindsight oracle (unconstrained) | 0.6667 | 37.65 | 36.80% |
| Hindsight oracle (matched accuracy) | 0.4194 | 42.51 | 28.64% |

The tuned confidence threshold is 0.05, so the policy almost always falls back
to the static depth. It captures **−1.92%** of the unconstrained oracle gap and
**−2.46%** of the matched-accuracy gap. Without abstention (only `k ≥ 1`), the
matched oracle gain is 7.21%, so most of the apparent oracle gap is an
abstention gain, not depth routing.

## Predictability audit

`analysis/policy_audit/` reports a CPU-only audit of how much signal the
pre-generation features contain. The out-of-fold AUC for `correct@1` is
**0.733**; the learning curve is flat from 50 to 608 training questions
(0.707, 0.717, 0.695, 0.727, 0.724), so more labels do not help. An
answer-presence oracle (retrieve at `k=1` when the gold string is in the top-1
passage, else `k=0`) reaches accuracy 0.4032 and 47.8% capture on the hashed
test split, below the 50% G4 floor. Even a perfect presence signal is at the
threshold, and the deployable AUC is 0.733.

## G4 adjudication

G4 requires an oracle gain of at least 20% and a policy capture of at least 50%
at matched accuracy. The oracle gain condition is met (28.64% matched; 36.80%
unconstrained), but the policy capture condition fails (−2.46% matched; −1.92%
unconstrained), so **G4 is not supported** and no adaptive claim is made.

## Caveats

- The unconstrained oracle accuracy (0.6667) is higher than the static accuracy
  (0.4194), so its 36.80% gain is not a matched-accuracy quantity. The
  matched-accuracy oracle holds accuracy at 0.4194 and still gives a 28.64% gap,
  which the policy also fails to capture. Without abstention, the gap falls to
  7.21%.
- The negative result is for this feature set and policy class (BM25-only
  logistic models). It does not prove that no query-conditional policy can work.
- The test split was evaluated once; the threshold was tuned on validation only.

## Artifacts

- `analysis/policy/policy.json`
- `analysis/policy/report.md`
- `scripts/07_train_policy.py`
- `src/rag_energy/stats/policy.py`
