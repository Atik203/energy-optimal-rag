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
