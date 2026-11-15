# Amendments

**Status:** empty log · opened 2026-11-09
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

_No amendments. The preregistration was frozen at `prereg-freeze-v1` on 2026-11-15 (SHA-256
`fb9e5bcfe8d93404f64bbf62e04cacc13fdcfbbcbfae02ec3212c6e12affc49f`)._
