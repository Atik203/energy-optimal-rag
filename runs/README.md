# Runs

Every experiment is a registered run. A run has an ID, a config, a raw CSV, and a registry
row. The registry is tracked; the run directory is not.

## Layout

```
runs/
├─ README.md            this file
├─ registry.csv         tracked registry, one row per run
└─ <run_id>/            git-ignored
   ├─ raw.csv           one row per generation
   ├─ blocks.json       block calibration factors
   ├─ manifest.json     run metadata, hashes, environment
   └─ logs/             sampler and server logs
```

## Naming

`<dataset>_<reader>_<phase>`, lowercase, e.g. `squad_qwen4b_p1`, `squad_qwen15b_p2`,
`hotpot_qwen4b_p2`, `boundary_qwen4b_p2`, `fixed_a_p2`, `per_passage_b_p2`.

A rerun of the same ID gets a suffix `_r2`, not an overwrite. Never overwrite a completed run.

## Registry schema

| Column | Meaning |
|---|---|
| `run_id` | Unique run identifier |
| `timestamp_utc` | ISO 8601 start time |
| `phase` | `P0`–`P6` |
| `dataset` | `squad`, `hotpot` |
| `reader` | model name |
| `retriever` | `bm25` |
| `k_grid` | pipe-separated depths, e.g. `0\|1\|2\|4\|8\|16\|32` |
| `n_questions` | sampled questions |
| `seed` | run seed |
| `energy_sampler` | `nvml` |
| `status` | `planned`, `running`, `completed`, `aborted`, `invalid` |
| `git_commit` | short commit at run start |
| `config_path` | repo-relative config |
| `config_sha256` | SHA-256 of the effective merged config |
| `prereg_sha256` | SHA-256 of the frozen prereg and analysis plan; blank before freeze |
| `model_digest` | reader model digest recorded at run start |
| `raw_csv` | repo-relative path (git-ignored) |
| `notes` | free text, no commas outside quotes |

Use the exact column order. A malformed row breaks downstream tooling.

## Rules

- Register the run **before** it starts; update the status after it ends.
- A run that aborts stays in the registry with status `aborted`; it is not deleted.
- Do not commit `runs/<run_id>/`. Commit the registry row, the config, and the analysis output.
- The analysis script refuses a run whose config hash or prereg hash does not match.
- A run without a raw CSV is not a result.

## Status values

`planned` → config exists, no data yet. `running` → in progress. `completed` → all rows
present and validated. `aborted` → stopped before completion. `invalid` → protocol violation
that makes the run unusable; the reason goes in `notes`.
