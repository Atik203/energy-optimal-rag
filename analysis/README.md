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
   ├─ metadata.json        run/config/prereg/git/seed provenance
   ├─ bootstrap.json       P(k* optimal), resample settings, seed
   ├─ identity.csv         elasticities and gap with CI
   ├─ noninferiority.json  5 pp test, 2 pp estimation
   ├─ certification.json   C_cert, N* per candidate
   ├─ fit.json             affine fit, quadratic lack-of-fit, H1 verdict
   ├─ sensitivity.json     margins × scoring rules
   ├─ gates.json           K1–K7 and G1–G5 evaluations
   ├─ policy.json          train/validation/test, capture, baseline
   ├─ taxes.json           sign tests for fixed and per-passage conditions
   └─ report.md            human-readable summary
```

There is no `analysis/golden_squad_qwen4b_p0_r3/`: the clean `_r3` block calibration failed
at `k=0` (0.7944), so no calibrated analysis was produced. The first-run failure analysis is
under `analysis/golden_squad_qwen4b_p0/` and is uncalibrated.

## Phase 6 inference repair

`analysis/phase6/` holds the analyses added after the first review round. All are CPU-only
re-analyses of registered rows; no gate changes.

| File | Content |
|---|---|
| `cluster_robust.json` | Paired contrasts with context-clustered SEs and the design effect |
| `token_vs_depth.json` | `J = a + b k` against `J = a + c T` (prompt tokens), cluster SEs, AIC/BIC |
| `affine_ci.json` | Intercept and slope with 95% intervals, `k >= 1`, `k=0` as a floor |
| `selection.json` | Cross-fitted selection of `k*`, held-out savings, winner's curse |
| `policy_ci.json` | Bootstrap interval for the P3 capture ratio |
| `gold_rank.json` | Accuracy when the gold passage is retrieved first (reader overload) |
| `reader_subset.json` | Three readers on the same 500 question IDs |
| `price_of_guarantee.json` | Savings bought by loosening the accuracy margin |
| `cancellation.json` | Recall/precision terms from `k=4` to the maximum depth |
| `report.md` | Human-readable summary |

Regenerate with `python scripts/21_phase6_inference.py`.

## Phase 7 measurement hardening

`analysis/measurement_hardening/<run_id>/` holds the block-estimator outputs, one directory per
run so that runs in the record cannot overwrite each other.

| Run | Output |
|---|---|
| `squad_qwen4b_p7_blocks` | First block run (20 questions per block); the energy-precision result |
| `squad_qwen4b_p7_blocks_full` | Representative run (200 disjoint questions per block, 1,000 per depth); the reported result |

Each directory contains `estimates.json` (ratio-of-sums `E(k)`, accuracy, CV, savings with the
cluster-bootstrap interval and every depth against the reference), `affine.json` (weighted fit on
`k >= 1`, `k=0` as a floor), `convergence.json` (replay agreement at the frozen 3 pp tolerance),
and `report.md`.

Regenerate with:

```bash
python scripts/23_phase7_analysis.py --run-id squad_qwen4b_p7_blocks_full
python scripts/23_phase7_analysis.py --run-id squad_qwen4b_p7_blocks
```

Results and interpretation: `docs/PHASE7_RESULTS.md`, decision D-032.

## Rules

- Analysis code reads only `runs/<run_id>/raw.csv` and the frozen config.
- `metadata.json` records the run ID, config hash, prereg hash, git commit, analysis seed, and
  whether block calibration was applied.
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
