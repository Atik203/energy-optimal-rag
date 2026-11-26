# Preregistration — Phase 8 router (full, max-reuse, confirmatory)

**Status:** DRAFT 2026-11-26 as `prereg/qc_router_prereg.md`. No GPU run starts until the freeze tag `prereg-qc-router-v1` exists. Any later change goes in `prereg/amendments.md` + `docs/DECISIONS.md`, never by editing this file after freeze.

## 1. Purpose and claim boundary

Phase 8 mechanism (dose-response + dense 2×2) is complete with no router. This prereg re-opens the router as a confirmatory study with maximum reuse that does not harm validity.

Claim boundary (D-032/D-033, ROADMAP §2) is unchanged: no universal `k*`, no probe-based routing claim, GPU energy only, absolute `J` a range, no H200/MIG energy, no 16k energy claim, no pooling SQuAD with HotpotQA, no re-thresholded gate.

**Not claimable, regardless of outcome:** any universal optimal depth; any probe-based (`k=0`) routing gain; any absolute joule figure as a deployment guarantee; `E(0)`, `N*`, `S(k)`, intercept `a`; any adaptive claim beyond the frozen `k in {1,4}` binary rule on pre-generation features.

## 2. Hypotheses

| ID | Hypothesis | Falsified / decided if |
|---|---|---|
| H-route | A pre-generation router over `k in {1,4}` captures ≥30% of the `k=4` oracle gap at ≤2pp accuracy loss. | Capture 95% CI lower bound ≤0, or accuracy-loss CI lower bound ≤−2pp, or flat ablation. Null is a finding. |

No probe feature (`p(correct|k=0)` constant 0.001, leaky, probe-dominated) in the primary arm. No gold presence, no post-generation signal.

## 3. Sample frames (seed 20261115, deterministic qid exclusion)

Exclusion list = union of all tracked SQuAD splits: `p0_golden` 200 + `p1_primary` 1000 (unique 1200) + `qc_fresh` 1000 + `qc_distractor` 500 + `qc_dense` 1000 + `qc_padding` 200 (from `runs/squad_qwen4b_qc_padding/padding.json` qids). Nominal sum 3900; unique excluded qids 3700 (P3 is a hashed subset of P1). Pool: 10,570 − 3700 = 6870 remaining dev qids.

- Train: `p1_primary` n=1000 (existing rows, CPU only, no new GPU).
- Select (threshold): `qc_fresh` n=1000 (existing rows, CPU only). Threshold frozen here before eval exists.
- Eval (once-only): `qc_router_eval` n=1000 fresh, disjoint from exclusion list and from each other above. Qid lists in `data/splits/qc_frames.json` (extended 2026-11-26, seed 20261115), per-frame hashes recorded below at freeze.
- `qc_router_eval`: n=1000, sha256 TBD at freeze.

Distractor/padding frames are never router eval (gold-first / length intervention bias).

## 4. Designs

- **Train (0 GPU):** P1 `1000 x {1,4}` correctness labels + BM25 pre-generation features (top/second/gap/mean/std/entropy/n-positive, question length, wh-type + pre-generation interactions only). Logistic-per-depth models (`src/rag_energy/stats/policy.py:train_policy`). Static comparator is `k=4` (the policy target), not `k=1`.
- **Select (0 GPU):** `qc_fresh` `1000 x {1,4}`. Tune only the confidence threshold on select to match static `k=4` accuracy. Freeze threshold. Report select-set capture as exploratory only, AUC, calibration, depth histogram.
- **Eval GPU (~0.8-1h):** `qc_router_eval` 1000 qids, `k in {1,4}`, 5 blocks x 200 qids per depth (same block protocol as run 2, `scripts/22_run_blocks_design.py`, new config `configs/runs/squad_qwen4b_qc_router.toml`): shards disjoint across replicates, each qid measured at both depths (paired within question), randomized block order, 120s cooldown before every block, idle from tail of each block cooldown, `PROTOCOL` tag, per-run analysis dir. ~2000 generations + 10x120s cooldowns ≈ 45min + startup ≈ 1h. Smoke first.
- **Energy costs (fixed):** per-depth mean block `J` from the eval run (`J1_bar`, `J4_bar`). Router eval uses fixed costs per decision (no per-query windows — the 7.21% artifact used per-query noise). Correctness is per-question. Windows diagnostic only.

## 5. Estimands (eval set only)

- `Gap = A_oracle{1,4} − A(4)` on eval, paired 95% CI (10k resamples, shared resample — D-035 fix).
- `Saving_static = 1 − E(4)/E(1)` with fixed costs (reference direction: router beats `k=4`, the deeper static).
- `Capture = Saving_policy / Gap_energy` where `Gap_energy` uses fixed costs at matched accuracy (allow_abstention=False — R5 correction, ROADMAP §2).
- `Acc_diff = A_policy − A(4)` with paired 95% CI; depth histogram; per-depth correctness-model AUC; calibration slope.
- Mandatory baselines on eval: static `k=1/4`, presence-oracle, confidence-only, random with same depth histogram, knapsack oracle. No Adaptive-RAG/Self-RAG/FLARE arm (out of scope — would need +1-2h GPU and separate prereg).

## 6. Energy method (Phase 7 lessons binding)

Block estimator primary: `E(k) = sum_b J_block(k,b) / sum_b C(k)`, randomized block order, 120s cooldown, idle from cooldown tail, `PROTOCOL` tag, per-run analysis dirs. Per-query windows diagnostic only. Every joule is GPU energy from NVML; absolute `J` is a range carrying 3-6% between-occasion component — the ratio is reportable.

## 7. Exclusions and stop rules

- Block invalid if reader reloads inside it (`load_s > 1.0`) or <2 power samples; rerun once at end. Invalid queries stay wrong answers (P1 rule D-009) unless block invalid. No outcome-based exclusions.
- Stop rule: eval `Gap < 10%` → report null without running extra baselines beyond static (mechanism headroom rule, D-035 precedent).
- Idle CV > 0.20 → run stops. Any frozen gate needing a new threshold → stop, reported inconclusive.

## 8. Analysis

1. Threshold frozen on select; applied once on eval (no re-tuning).
2. Capture with independent bootstrap CI (10k resamples); accuracy diff with paired CI.
3. TOST with bounds ±2pp for null accuracy claim.
4. Ablation: flat (all-`k=4`) must lose; feature ablation (BM25-only vs +shape) reported.
5. No re-thresholding after outcomes (AGENTS.md §4); exploratory labelled.

## 9. Frozen decision rules and G8-router acceptance

G8-router passes iff: (a) eval gap reported; (b) capture ≥30% with 95% CI lower bound >0; (c) accuracy-loss CI lower bound >−2pp; (d) depth histogram + AUC + calibration reported. Otherwise documented null with MDE. Router items no longer out-of-scope; probe routing stays out by decision.

Budget ~1h GPU eval + 0 GPU train/select + ~0.5h contingency = ~1.5h total, batch 1, no concurrent jobs; `df -h` first.

## 10. Deviations

| Date | Original | Replacement | Reason | Outcome seen? |
|---|---|---|---|---|
| - | - | - | - | - |

## 11. Freeze block (complete at freeze, not before)

- File SHA-256: see `prereg/qc_router_prereg.sha256`
- Freeze tag: `prereg-qc-router-v1`
- Frozen by / date: PI instruction 2026-11-26 ("Good we will do that. Plan for it and start") / 2026-11-27
- Eval frame: `qc_router_eval` n=1000, sha256 `4c16b6a644dfe16847b2f56f0e5a90227126d6e65827ce14c40e424ea3eea170`
- Threshold frozen on select before eval exists: `0.80` (`analysis/qc_router/select.json`; select acc 0.4550 vs static 0.4550, AUC k1 0.725 / k4 0.669, fixed J1 19.04 / J4 26.80 J/q)
- Eval outcome seen at freeze: no (`runs/squad_qwen4b_qc_router/` does not exist)
