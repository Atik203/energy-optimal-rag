# Artifacts

Tracked, checksummed summaries of the project's evidence. Raw runs stay git-ignored; this
directory is the auditable index.

## Files

| File | Purpose | Tracked |
|---|---|---|
| `ledger.csv` | One row per aggregated artifact: path, SHA-256, bytes, license | Yes |
| `claims_evidence.csv` | One row per paper claim: run, statistic, value, CI, n | Yes |
| `README.md` | This file | Yes |
| `figures/` | Generated figures (git-ignored) | No |

## `ledger.csv` schema

| Column | Meaning |
|---|---|
| `artifact_id` | `A-0001`, in creation order |
| `run_id` | Registered run, or `pilot` for prior evidence |
| `kind` | `raw`, `analysis`, `figure`, `table`, `manifest`, `release` |
| `path` | Repo-relative path |
| `sha256` | SHA-256 hex digest |
| `bytes` | File size |
| `created_utc` | ISO 8601 |
| `license` | `MIT`, `CC-BY-4.0`, or upstream |
| `notes` | Provenance and caveats |

## `claims_evidence.csv` schema

| Column | Meaning |
|---|---|
| `claim_id` | `C-001`, in paper order |
| `claim_text` | The exact claim, with its qualifier |
| `status` | `supported`, `pilot`, `upper_bound`, `dead`, `exploratory` |
| `evidence_type` | `measurement`, `bootstrap`, `test`, `fit`, `derivation` |
| `run_id` | Registered run |
| `artifact_path` | Path to the analysis output |
| `statistic` | Name, e.g. `E_ratio_32_1` |
| `value` | Point estimate |
| `ci_low`, `ci_high` | Interval, if any |
| `n` | Sample size |
| `notes` | Gate, margin, or caveat |

## Rules

- A claim without a row here is not allowed in the paper.
- The 78.8% oracle gain is `upper_bound`, never `supported`.
- The static 2 pp claim is `dead`.
- A pilot number is `pilot` until the powered rerun reproduces it.
- Checksums are computed, never typed from memory.

## Licensing

Aggregated, derived artifacts are CC BY 4.0. Raw upstream text is not stored here. See
[`../DATA_LICENSE.md`](../DATA_LICENSE.md).
