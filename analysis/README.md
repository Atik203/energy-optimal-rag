# Analysis

Generated analysis outputs live here. They are derived from registered raw runs. Small
tabular and report outputs may be tracked; large figures are git-ignored. The tracked
evidence index is `artifacts/ledger.csv`, and claims are indexed in
`artifacts/claims_evidence.csv`.

## Layout

```
analysis/
└─ <run_id>/
   ├─ estimates.csv        A(k), J(k), E(k), S(k), S_r(k), CIs
   ├─ p0_check.json        P0 J-anchor and affine-fit check
   ├─ bootstrap.json       P(k* optimal), resample settings, seed
   ├─ identity.csv         elasticities and gap with CI
   ├─ noninferiority.json  5 pp test, 2 pp estimation
   ├─ certification.json   C_cert, N* per candidate
   ├─ sensitivity.csv      margins × scoring rules
   ├─ policy.json          train/validation/test, capture, baseline
   ├─ taxes.json           sign tests for fixed and per-passage conditions
   └─ report.md            human-readable summary
```

## Rules

- Analysis code reads only `runs/<run_id>/raw.csv` and the frozen config.
- Every output records the run ID, config hash, prereg hash, git commit, and analysis seed.
- No hand-edited numbers. If a table is wrong, fix the generator and regenerate.
- The 5 pp result is primary. The 2 pp result is estimation-only and must be labeled.
- The oracle is an upper bound and is labeled as such in every output.
- Sensitivity analyses are reported with the primary, not buried.

## Reproducing

```bash
python scripts/05_analyze.py --run-id <run_id>
python scripts/06_power.py --margin 0.05 --discordant-rate 0.08
python scripts/07_train_policy.py --run-id <run_id>
```

A clean-room reproduction runs the same commands from the raw CSVs on a second machine and
must match to numerical precision.

## What is not here

- Raw data (see `data/`).
- Model weights.
- Notebooks with hidden state. Promote logic into `src/rag_energy/` or `scripts/`.
