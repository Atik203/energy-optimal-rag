# Analysis Plan

**Status:** DRAFT — revised 2026-11-11 before freeze (population/failure clarification, split
wording); not yet frozen. Companion to [`PREREGISTRATION.md`](PREREGISTRATION.md).
**Version:** v0.1.0 · 2026-11-09
**Frozen at:** `prereg-freeze-v1` (pending)
**Software:** Python 3.12, numpy/pandas/scipy/statsmodels, seed `20261115`.

This plan is written so that another analyst can reproduce every number from
`runs/<run_id>/raw.csv` without reading the paper draft.

## 1. Unit and population

The unit is a question. A **valid row** requires a non-empty nonce, a completed request, and a
power window with no sampler error. A failed or empty generation after a completed request is a
**wrong answer** (`correct = 0`) and is retained, not invalidated; a row is **invalid** only for
a protocol violation: missing nonce, request/backend failure, or sampler error. Descriptive
`A(k)`, `J(k)`, and `E(k)` use every sampled question with a valid row at depth `k`, and
`n_valid(k)` and `n_invalid(k)` are reported at each depth. A question is not dropped from
depth `k` because it has no row at another depth. The primary paired test uses questions with
valid rows at both `k = 4` and `k = 32`; the paired `n`, the discordant counts, and the invalid
counts are reported. There are no outcome-based exclusions: no winsorizing, trimming, or
imputation, and wrong, slow, and throttled answers stay in.

## 2. Preprocessing

1. Load `raw.csv`; verify `n_questions × n_depths` plus repeats.
2. Recompute `correct_em`, `correct_lenient`, and `f1` from `prediction` and `gold` with the
   frozen normalization in `rag_energy.scoring`. A mismatch with the stored value is a
   pipeline bug, not a data point.
3. Keep `j_gpu_raw` and `j_gpu_calibrated`; the calibrated value is primary.
4. Compute `j_total = j_gpu_calibrated + j_retrieval_proxy`.
5. Do not winsorize, trim, or impute. Report the raw distribution.

## 3. Estimands

For each depth `k`:

```
A(k)  = (1/n) * sum_i C_ik
J(k)  = (1/n) * sum_i J_ik
E(k)  = sum_i J_ik / sum_i C_ik          # ratio of sums, not mean of ratios
S(k)  = (J_ret(k) + J_pre(k)) / J(k)
S_r(k)= J_ret(k) / J(k)
```

`J_pre(k)` is estimated from the fitted affine slope `b` times `k`, following the pilot. The
retrieval term is the CPU proxy. Here `n = n_valid(k)`, the number of sampled questions with a
valid row at depth `k`; `n_invalid(k)` is reported alongside. `E(k) = inf` when `sum C = 0`;
that is a real outcome and is reported as such.

The feasibility set is `{k : A(k) ≥ A(32) − margin}`. The selected depth is the feasible `k`
with the smallest `E(k)`. Ties go to the smaller `k` (cheaper retrieval), declared in advance.

## 4. Primary non-inferiority test

Let `d_i = C_i4 − C_i32` for paired question `i` over questions with valid rows at both
depths. The null is `E[d] ≤ −0.05`; the alternative is `E[d] > −0.05`. Use a one-sided paired
test at `α = 0.05` (exact McNemar for the sign, or a paired z-test with a continuity
correction; report both if they disagree). The decision rule also requires at least 20%
savings:

```
savings = 1 − E(4) / E(32) ≥ 0.20
```

Confidence intervals for the difference use a paired bootstrap (10,000 resamples) and a
one-sided 95% lower bound. Report the paired `n`, the discordant pair counts (`b`, `c`), the
invalid counts, the exact p-value, the lower bound, and the savings interval.

The 2 pp margin repeats the procedure with `margin = 0.02` and is labeled
**estimation-only**. It is never described as certified.

## 5. Bootstrap

- 10,000 resamples of questions. Descriptive statistics resample questions with a valid row at
  the depth being estimated; the primary test resamples the paired population with valid rows
  at both `k = 4` and `k = 32`.
- Percentile 95% intervals for `E(k)`, `A(k)`, `S(k)`, the identity gap, and `N*`.
- `P(k* optimal)` is the fraction of resamples in which each depth is the feasible minimizer
  under the 5 pp gate.
- Report the bootstrap seed and the number of resamples.
- If a resample has zero correct answers at a depth, `E = inf`; retain it. Do not drop it.

## 6. Energy model and identity

Fit `J(k) = a + bk` by ordinary least squares over the depth means. Report `a`, `b`, `R²`, and
a lack-of-fit check (residual pattern and a quadratic-term test). The pilot values were
`a = 15.74`, `b = 2.283`, `R² = 0.9990`.

Compute `ε_J(k) = k * b / (a + bk)` from the fit. Compute `ε_A(k)` by a central finite
difference over the empirical `A(k)`; at the grid edges use a one-sided difference and label
it. The identity gap is `ε_J − ε_A` with a bootstrap interval. The pilot gaps were +0.044 at
`k = 2` (CI includes 0) and +0.700 at `k = 32`.

The identity is a local diagnostic. It cannot distinguish a local from a global minimum. If
`A(k)` is non-monotone, report the distractor counterexample regime and use a global search
for `k*`.

## 7. Coverage model

Fit `A(k) = 1 − (1 − A_0)(1 − p)^k` by constrained least squares (`A_0 ∈ [0,1)`,
`p ∈ (0,1]`). Report `R²`, residual pattern, and a monotonicity test on the empirical curve.
The pilot fit was poor (`A_0 = 0.324`, `p = 0.0218`, `R² = 0.332`); a poor fit is evidence
against the stylized model, not a reason to discard the identity diagnostic.

## 8. Certification cost

```
C_cert = total measured energy of the sweep (J)
N*     = C_cert / (A(k*) * (E(k_0) − E(k*)))
```

with `k_0 = 32` as the default depth. Report `N*` for each feasible candidate, with a
bootstrap interval. The pilot sweep cost 49.6 kJ and gave `N* = 876` for `k = 4`, 1,000 for
`k = 8`, and 1,489 for `k = 16`. `N*` is a break-even calculation, not a deployment guarantee.

## 9. Margin and scoring sensitivity

Repeat the selection and savings calculation at margins 2, 3, 4, 5, 6, 8, and 10 pp, under
EM, lenient span, and F1 ≥ 0.5. Report the full table. The paper's conclusion must state
whether the qualitative result ("never the maximum depth") survives all three rules. If the
selected depth changes, report the dependence and do not choose the favorable rule.

## 10. Query-conditional policy

- Features: BM25 top score, second score, gap, mean, standard deviation, entropy, number of
  positive scores, question length, question type.
- Split target: 600 train / 200 validation / 200 test by SHA-256 of `seed:question_id`. The
  realized counts may differ slightly because assignment is per question; they are reported.
  No test-set tuning; the test split is evaluated once.
- Model: cost-sensitive classifier or shallow decision tree; validation selects the model and
  operating point; test is touched once.
- Oracle: the cheapest correct depth per test question with hindsight.
- Evaluation at matched accuracy: hold accuracy at the best static `k`'s test accuracy and
  compare energy per correct answer.
- Report capture = `(E_static − E_policy) / (E_static − E_oracle)`.
- Report a feature-free baseline (always the static `k`) and a learning curve.

The 78.8% pilot oracle gain is an upper bound and is not a policy result.

## 11. Energy-tax analysis

For each condition, estimate `k*` under the same gate and compare with the no-tax baseline.
Report the sign, the effect size, and a bootstrap interval. The predicted signs are fixed:
fixed tax increases `k*`, per-passage tax decreases it. Also report the unconstrained optimum
and the mid-accuracy-gate optimum, because a binding gate can mask the movement. A wrong sign
is a falsification of the affine/split model, not a null result.

## 12. Multiplicity

There is exactly one primary test (H2, 5 pp non-inferiority). Every other test is secondary or
exploratory and is labeled as such. No family-wise correction is applied to the primary
because it is a single test. If a secondary family is promoted to confirmatory, Holm's
procedure is applied and the promotion is recorded as an amendment.

## 13. Missing data and failures

- A missing row at one depth does not remove the question from the other depths' descriptive
  statistics; the paired test uses only questions with valid rows at both `k = 4` and `k = 32`.
- Report `n_valid(k)` and `n_invalid(k)` at every depth, and the paired `n`, discordant counts,
  and invalid counts for the primary test, not just the nominal `n`.
- A run aborted before completion is registered as `aborted` and is not analyzed as if
  complete.
- A failed or empty generation after a completed request is a wrong answer, not a missing data
  point. It stays in the denominator. A row is invalid only for a protocol violation.

## 14. Reproducibility

- The analysis records the git commit, the config hash, and the prereg hash.
- Every table and figure is generated by a script from a registered run.
- The clean-room reproduction re-runs the analysis from raw CSVs on a second machine and must
  match to numerical precision.
- The claims-evidence map (`artifacts/claims_evidence.csv`) links each paper claim to a run
  and a statistic.

## 15. Reporting order

1. Primary 5 pp result (test, CI, savings).
2. Descriptive curves (`A`, `J`, `E`, `S`, `S_r`).
3. Identity and energy model.
4. Certification cost.
5. Sensitivity (2 pp estimation, margins, scoring rules).
6. Replication and distractor.
7. Policy and oracle.
8. Tax manipulation.
9. Limitations and gates.
