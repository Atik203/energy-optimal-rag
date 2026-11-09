# Pre-Registration — Energy-Optimal Retrieval Depth (G2)

**Status:** DRAFT — not yet frozen. Freeze at the P1 start, tag `prereg-freeze-v1`.
**Version:** 0.1-draft · 2026-11-09
**Registry:** none (no external registry). The frozen git tag and its SHA-256 are the record.
**Prereg hash:** `TBD` (recorded at freeze)
**Analysis plan:** [`analysis_plan.md`](analysis_plan.md)
**Amendments:** [`amendments.md`](amendments.md)

This document is written before the confirmatory data are collected. It records what will be
tested, on which population, with which decision rule, and what will count as failure. The
pilot (200 SQuAD questions) is prior evidence and is not part of the confirmatory sample.

## 1. Background and claim boundary

The pilot found a steep energy-depth tradeoff (`E(32) = 157.1` vs `E(1) = 45.5` J/correct,
3.45×), an affine energy model (`J = 15.74 + 2.283k`, `R² = 0.9990`), a context-side share
rising from 36.3% to 85.1%, and an optimal-depth identity that holds at `k = 2`
(gap +0.044, CI [−0.050, +0.128]) and fails at `k = 32` (+0.700). The static 2 pp claim is
dead: `k* = 32` at the boundary, `P(k* optimal) = 0.61`. At a 5 pp margin the pilot selected
`k = 4` with 69.3% savings and `N* = 876`; the adaptive oracle gain was 78.8%, an upper bound
with no learned policy.

The confirmatory study tests the 5 pp policy claim and the adaptive direction. It does not
test a universal `k*`, a 2 pp optimum, or a learned-policy gain that has not been measured.

## 2. Hypotheses

| ID | Hypothesis | Type |
|---|---|---|
| **H1** | Energy is affine in depth: `J(k) = a + bk` with `b > 0` and `R² ≥ 0.95` on SQuAD, and the affine fit is not rejected by a lack-of-fit check at the 5% level. | Confirmatory |
| **H2** | At a 5 pp EM non-inferiority margin, `k = 4` is non-inferior to `k = 32` on SQuAD at `n = 1,000`, with at least 20% energy savings. | Primary |
| **H3** | At the selected interior depth, the optimal-depth identity gap `ε_J − ε_A` has a 95% bootstrap interval that includes zero. | Confirmatory |
| **H4** | The context-side energy share `S(k)` lies in [0.10, 0.70] at the selected depth and increases with `k`. | Confirmatory |
| **H5** | The oracle query-conditional gain is at least 20%, and a learned policy captures at least 50% of it at matched accuracy on 200 held-out questions. | Confirmatory (adaptive) |
| **H6** | A fixed energy tax increases `k*`; a per-passage energy tax decreases `k*`, with the accuracy gate held fixed. | Confirmatory (causal) |
| **H7** | The direction of H2 replicates on Qwen2.5-1.5B-Instruct (`n = 500`) or HotpotQA distractor (`n = 500`). | Confirmatory (replication) |

The 2 pp margin is **not** a hypothesis. It is an estimation target reported with a confidence
interval and explicitly not used for certification.

## 3. Design

| Element | Primary | Replication | Distractor | Boundary |
|---|---|---|---|---|
| Dataset | SQuAD v1.1 dev | SQuAD v1.1 dev | HotpotQA distractor dev | SQuAD v1.1 dev |
| n | 1,000 | 500 | 500 | 200 |
| Depths | 0,1,2,4,8,16,32 | 0,1,2,4,8,16,32 | 0,1,2,4,8,10 | 32,48,64 |
| Reader | qwen3.5:4b | Qwen2.5-1.5B-Instruct | qwen3.5:4b | qwen3.5:4b |
| Retriever | BM25 top-32 | BM25 top-32 | BM25 top-10 | BM25 top-64 |
| Seed | 20261115 | 20261115 | 20261115 | 20261115 |
| Scoring | Normalized EM primary | Same | Same | Same |

Within each question, depth order is randomized. Every request carries a unique nonce. The
reader, prompt, decoding parameters, chunking, and scoring rule are fixed before the run. The
policy split is 600/200/200 by hashed question ID.

## 4. Primary estimand and test

**Estimand.** `E(k) = E[J_k] / E[C_k]`, estimated as `sum(J_k) / sum(C_k)` over the analysis
population. The primary decision compares `k = 4` (candidate) with `k = 32` (reference) at a
5 pp EM non-inferiority margin.

**Accuracy gate.** `A_min = A(32) − 0.05`. The candidate must also save at least 20% of energy
per correct answer relative to the reference. The gate is fixed; it is not re-derived from the
candidate's accuracy.

**Test.** One-sided paired test on the accuracy difference at α = 0.05. The null is
`A(4) − A(32) ≤ −0.05`; rejection supports non-inferiority. The 95% one-sided lower bound on
the difference must exceed −5 pp. Energy savings are reported as a ratio of sums with a
10,000-resample paired bootstrap interval.

**Decision rule.** H2 is supported iff the non-inferiority test rejects at α = 0.05 **and**
the point estimate of savings is at least 20%. If the test rejects but savings are below 20%,
the result is "non-inferior but not materially greener" and is reported as a failure of the
policy claim.

## 5. Secondary estimands

1. **2 pp margin.** Same procedure at a 2 pp margin, reported with a CI, no certification
   language.
2. **Optimal depth under the 5 pp gate.** `k* = argmin E(k)` over feasible depths, with
   bootstrap `P(k* optimal)`.
3. **Identity gap** at the selected depth, with a bootstrap interval.
4. **Context-side and retrieval-only shares** at every depth.
5. **Affine energy fit** and its `R²`.
6. **Certification cost** `N*` from the measured sweep energy.
7. **Margin sensitivity** at 2, 3, 4, 5, 6, 8, 10 pp.
8. **Scoring sensitivity** under lenient span and F1 ≥ 0.5.
9. **Reader and dataset replication** (H7).
10. **Policy capture** at matched accuracy (H5).

## 6. Sample size and power

At `n = 1,000`, a planning discordant rate of 0.08 gives a paired-difference standard error of
about 0.9 pp. The minimum detectable effect at 80% power is about 2.2 pp. Power for a 5 pp
non-inferiority test is greater than 0.99 when the true difference is 0 pp, about 0.998 at
1 pp, about 0.96 at 2 pp, and about 0.72 at 3 pp.

At `n = 200` the MDE is about 5.0 pp, which is why the pilot could not certify a 2 pp margin.
At `n = 500` the MDE is about 3.1 pp. The 500-question replication is powered for the
direction of H2, not for a 2 pp claim.

The 2 pp margin is estimation-only at every sample size in this design. The 95% interval
half-width at `n = 1,000` is about 1.8 pp, so the design can estimate a 2 pp difference but
cannot certify it against a 2 pp boundary.

## 7. Randomization and blinding

- Question order is fixed by the sampled ID list; depth order is shuffled within question by
  the run seed.
- The analysis script reads the raw CSV after the run; there is no interim unblinding.
- The analyst does not choose the margin after seeing the accuracy curve. The margins are in
  this document and in `configs/analysis/prereg.toml`.
- The policy test split is hashed before training and is evaluated once.

## 8. Exclusions

- A row is invalid if the nonce is missing, the request failed, the output is empty, or the
  power window has a sampler error. The invalid count is reported.
- A question is excluded only if it has no valid row at any depth. The count is reported.
- A depth is excluded only if it has no valid row for the analysis population. The count is
  reported.
- Wrong answers, slow answers, and throttled blocks are **not** excluded.
- No outcome-based exclusions. No trimming of the energy distribution unless pre-registered
  here: none is.
- The analysis population is intent-to-evaluate: every question sampled is analyzed if it has
  at least one valid row.

## 9. Analysis plan summary

The full plan is in [`analysis_plan.md`](analysis_plan.md). In brief: compute per-depth
accuracy, mean energy, and the ratio estimand; bootstrap over questions with 10,000 paired
resamples; run the one-sided non-inferiority test; fit the affine energy model; compute the
identity gap by finite differences; report the split; compute `N*`; evaluate the policy on the
held-out split; run the tax sign tests; and report every sensitivity analysis. The primary
test is the only confirmatory test; everything else is labeled exploratory or secondary.

## 10. Gates

The kill/reframe gates K1–K7 and the go gates G1–G5 are defined in
[`../ROADMAP.md`](../ROADMAP.md) section 4. They are adopted here by reference. The values are
frozen in `configs/analysis/prereg.toml`.

A gate may not be added, removed, or re-thresholded after the primary outcome is seen. K1–K4
and K6 firing is a kill/reframe. K5 and K7 are fixable measurement or framing problems before
they are kills.

## 11. Deviations

Any deviation from this document after the freeze is recorded in
[`amendments.md`](amendments.md) with the date, the original text, the replacement, the
reason, and whether outcome data had been seen. The amendment is mirrored in
[`../docs/DECISIONS.md`](../docs/DECISIONS.md). The analysis script records the prereg hash
and refuses to run on a mismatch.

## 12. Data and code availability

Code is MIT. Documentation and derived artifacts are CC BY 4.0. SQuAD and HotpotQA remain
CC BY-SA 4.0 and are not redistributed. The repository releases dataset IDs, versions,
checksums, configs, prompts, predictions, and aggregate statistics. Raw text stays in the
git-ignored `data/` tree and the run directories stay in git-ignored `runs/`.

## 13. Timeline

P0 week 1 (scaffold, golden reproduction), P1 weeks 2–3 (this study), P2 weeks 4–6
(replication, distractor, boundary, taxes), P3 weeks 7–10 (policy), P4 weeks 11–14 (theory and
sensitivity), P5 weeks 15–18 (paper), P6 weeks 19–20 (release). See `ROADMAP.md`.
