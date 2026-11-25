# Amendments

**Status:** 1 amendment (A-001) · opened 2026-11-09
**Rule:** after `prereg-freeze-v1`, no edit to `PREREGISTRATION.md` or `analysis_plan.md`
without an entry here. Each entry is immutable. A reversal is a new entry, not an edit.

## Format

| Field | Required content |
|---|---|
| `amendment_id` | `A-001`, `A-002`, … in order |
| `date_utc` | ISO 8601 date |
| `prereg_version` | Version or tag being amended |
| `section` | Section heading and quoted original text |
| `replacement` | Exact new text or parameter value |
| `reason` | Why the change is necessary |
| `outcome_data_seen` | `yes` / `no` / `partial` — and which outcome |
| `impact` | Which hypotheses, gates, or tables are affected |
| `approved_by` | PI or team decision |
| `decision_log` | Link to the matching entry in `docs/DECISIONS.md` |

An amendment that changes a primary estimand, a gate threshold, or the sample size after
outcome data are seen is not an amendment; it is a new study and must be reported as such.

## Log

_No amendments before A-001. The preregistration was frozen at `prereg-freeze-v1` on
2026-11-15 (SHA-256
`fb9e5bcfe8d93404f64bbf62e04cacc13fdcfbbcbfae02ec3212c6e12affc49f`)._

---

### A-001 - H7 direction decision rule operationalized

- **amendment_id:** A-001
- **date_utc:** 2026-11-15
- **prereg_version:** `prereg-freeze-v1`
- **section:** Section 2, Hypotheses, H7: "The direction of H2 replicates on
  Qwen2.5-1.5B-Instruct (`n = 500`) or HotpotQA distractor (`n = 500`)."
- **replacement:** H7 is supported on an arm when the paired mean difference
  `A(4) - A(reference)` has the same sign as the P1 estimate, which was negative
  (`-4.30 pp`), **and** its one-sided 95% upper confidence bound is below zero. The
  test is one-sided at `alpha = 0.05` on paired question-level binary correctness. The
  reference depth is 32 on SQuAD and 10 on HotpotQA distractor, because that setting
  supplies exactly 10 paragraphs per question. H7 is a direction test only: it does not
  test a 5 pp or 2 pp margin, does not certify non-inferiority, and does not select a
  universal `k*`. The 5 pp non-inferiority estimate is reported as a secondary,
  unpowered quantity on each replication arm.
- **reason:** H7 names a direction but does not define a decision rule, a reference
  depth for HotpotQA, or an error rate. Leaving these implicit would allow the
  replication verdict to be chosen after seeing the result. This entry fixes the rule
  before any P2 outcome is analyzed.
- **outcome_data_seen:** no. No P2 raw row had been read or analyzed when this rule was
  fixed; the Qwen2.5-1.5B sweep was still collecting rows. No P1 threshold changes.
- **impact:** H7 only, on both replication arms (Qwen2.5-1.5B SQuAD and HotpotQA
  distractor). H2, the 5 pp margin, all gates, and both sample sizes are unchanged.
- **approved_by:** PI session decision, 2026-11-15.
- **decision_log:** `docs/DECISIONS.md` D-025.

---

### A-002 - HotpotQA sampling frame restricted to complete 10-paragraph questions

- **amendment_id:** A-002
- **date_utc:** 2026-11-15
- **prereg_version:** `prereg-freeze-v1`
- **section:** Section 2, Hypotheses, H7: "The direction of H2 replicates on
  Qwen2.5-1.5B-Instruct (`n = 500`) or HotpotQA distractor (`n = 500`)."
- **replacement:** The HotpotQA distractor sample is drawn from the 7,345 dev questions that
  provide exactly 10 paragraphs. The 60 dev questions with 2-9 paragraphs are excluded before
  sampling, so `k = 10` means 10 candidate paragraphs for every question and the reference depth
  is identical across questions. Sampling remains stratified by question type
  (bridge/comparison) with seed `20261115`.
- **reason:** HotpotQA dev is not uniform: 60 of 7,405 questions have fewer than 10 paragraphs.
  Including them would silently change the reference depth for those questions and make the
  H7 contrast incomparable. The frame restriction is fixed before any HotpotQA outcome is
  analyzed.
- **outcome_data_seen:** no. The restriction uses only the upstream paragraph counts, not
  model answers, accuracy, or energy.
- **impact:** HotpotQA H7 arm only. `n = 500`, the depth grid, the candidate/reference contrast
  (`4` vs `10`), the margin, and all gates are unchanged. The Qwen2.5-1.5B arm is unaffected.
- **approved_by:** PI session decision, 2026-11-15.
- **decision_log:** `docs/DECISIONS.md` D-026.

### A-003

- **amendment_id:** A-003
- **date_utc:** 2026-11-25
- **prereg_version:** `prereg-measurement-v1`
- **section:** Section 3, Design: "Questions per block 20, identical across blocks" and
  "Measured generations 700".
- **original:** 5 blocks per depth, 20 identical questions per block, 700 measured generations.
  The accuracy denominator for `E(k)` is therefore 20 questions per depth.
- **replacement:** 5 blocks per depth of **200 disjoint questions** each (1,000 distinct
  questions per depth; 7,000 measured generations). Block order, cooldown (120 s), discard rule
  (2 queries), depths, estimator, bootstrap, and every gate are unchanged. The estimator is
  still `E(k) = sum_b J_block(k,b) / sum_b C(k,b)`; the denominator now covers the full P1
  sample.
- **reason:** The first run (`squad_qwen4b_p7_blocks`) showed that 20 questions give an accuracy
  standard error of about 11 pp and a non-monotone `A(k)` (`A(4)=A(8)=0.65`, `A(16)=0.53`),
  against 0.450/0.467/0.481 on the full sample. The energy side passed its gates (block CV
  1.8-3.6% at `k >= 4`; affine slope 2.523 [2.329, 2.717]). The savings ratio therefore failed
  G7 on the denominator, not on the measurement. Increasing the denominator to 1,000
  questions per depth is the smallest change that makes `E(k)` comparable to P1.
- **outcome_data_seen:** **yes.** The change follows inspection of the first run's accuracy
  subsample and its 75.70% saving. This is disclosed because it is a design change made after
  seeing an outcome. It does not change any gate, margin, or decision rule; H-M1's 3 pp
  tolerance, H-M2's 20% CV gate, and H-M3 are unchanged. The first run remains in the record
  and is reported as run 1, not discarded.
- **impact:** GPU cost rises from about 2 h to about 3.5 h (7,070 generations). The estimator,
  bootstrap, and convergence rule are identical. No P1-P4 gate is affected.
- **approved_by:** PI instruction, 2026-11-25 ("do what is the best").
- **decision_log:** `docs/DECISIONS.md` D-030.

### A-004

- **amendment_id:** A-004
- **date_utc:** 2026-11-25
- **prereg_version:** `prereg-measurement-v1`
- **section:** Section 3, Design row "Wall meter: `k in {1,4,32}`, 3 repeats x 100 queries, run
  last"; Section 7, Analysis item 7; Section 8, the two wall-ratio decision rules.
- **original:** A depth-resolved wall-meter cross-check would be run last, and the
  `system_J / (GPU_J + CPU_proxy)` ratio would be reported as a range, with a decision rule for
  depth-invariant versus depth-varying ratios.
- **replacement:** The wall meter is **not measured**. The reported energy quantity is the GPU
  integral from NVML. No system-level energy figure is reported.
- **reason:** No meter will be purchased. The owner decided on 2026-11-25 that the project will
  not use one; D-016 had already waived it for P0 and P1.
- **outcome_data_seen:** yes. The decision follows the Phase 7 runs. It removes a measurement,
  so it cannot bias any remaining estimate in a favourable direction: removing a cross-check only
  narrows what may be claimed.
- **impact:** No absolute energy claim gains support; one source of support is removed. Every
  joule in the paper must be labelled GPU energy. An energy-venue submission becomes out of
  scope (it would need a meter and a second hardware class); the IR/ML venue path is unchanged.
- **approved_by:** PI instruction, 2026-11-25 ("we will not use the wall meter").
- **decision_log:** `docs/DECISIONS.md` D-031.
