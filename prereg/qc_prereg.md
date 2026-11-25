# Preregistration — Phase 8 causal mechanism (distractor dose + dense 2×2, no router)

**Status:** FROZEN 2026-11-26 as `prereg/qc_prereg.md`, tag `prereg-qc-v1`. No GPU run
starts until the tag exists. Any later change goes in `prereg/amendments.md` +
`docs/DECISIONS.md`, never by editing this file.

## 1. Purpose and claim boundary

Phase 7 described the knee (`E(k)` minimised at `k=1`–`k=2`, flat to `k=4`) and the
R/Q cancellation (Q sets the sign). Phase 8 tests the mechanism causally: whether
distractors at fixed gold rank lower accuracy (reader overload, H-overload), and
whether the precision collapse travels with the retriever (H-dense). The router is
dropped by owner decision 2026-11-26: no H-route, no policy-capture claim.
Claim boundary (D-032/D-033) is unchanged: no universal `k*`, no adaptive-policy
claim, GPU energy only, absolute `J` a range, no guarantee.

**Not claimable, regardless of outcome:** any universal optimal depth; any
adaptive-policy gain; any absolute joule figure as a deployment guarantee; `E(0)`,
`N*`, `S(k)`, intercept `a`; any energy claim from H200/MIG or 16k; any reranker /
second-encoder claim; any pooling of SQuAD with HotpotQA; any re-thresholded gate.

## 2. Hypotheses

| ID | Hypothesis | Falsified / decided if |
|---|---|---|
| H-overload | At fixed gold rank 1, adding distractors lowers accuracy. | Cochran–Armitage trend over dose is not negative at `α=0.05` one-sided, or per-dose CIs include flat. |
| H-dense | The precision collapse is a BM25-rank artifact; dense retrieval changes the `A(4)−A(32)` contrast. | DiD 95% CI includes zero (reported as null finding, not failure). |

No router hypothesis. A flat dose curve, a DiD including zero, or a dense knee at
the same place are findings (mechanism is reader-side), not failures.

## 3. Sample frames (seed 20261115, deterministic qid exclusion)

Exclusion list = union of all tracked SQuAD splits: `p0_golden` 200 + `p1_primary`
1000 (contains `replication` 500, `boundary` 200, `context` 200 = boundary IDs,
`tax` 150 — all nested). Nominal sum 2,250; **unique excluded qids 1,200**
(P3 is a hashed subset of P1, so excluding P1 excludes P3). Pool: 10,570 − 1,200
= **9,370** remaining dev qids. Three fresh frames drawn disjoint from the
exclusion list and from each other: fresh `n=1,000`, distractor `n=500`, dense
`n=1,000` (2,500 total). Qid lists in `data/splits/qc_frames.json` (generated 2026-11-26, seed 20261115), per-frame hashes:
- `qc_fresh`: n=1000, sha256 `79cc63a654b49765d0a9681ea3af8091f8d5394dba93d8ad2b4ad687e6ce36ad`
- `qc_distractor`: n=500, sha256 `fd72ca733cda1b1425dc4007673e6b48ad516a39011de9c9970ed046924477a3`
- `qc_dense`: n=1000, sha256 `e10eb333fa8fb474770edb9c0b70be5d969fe85b848386d2cfac56b2b9a28534`
Distractor eligibility (gold at rank 1 at `k=1` under BM25) uses retrieval ranks
only — never reader correctness or energy — and the eligible/ineligible counts
are reported.

## 4. Designs

- **Step 1 fresh gap (gating, ~0.8 h GPU):** fresh 1,000 qids, `k ∈ {1,4}`,
  5 blocks × 200 qids per depth (≈2,000 generations over 1,000 distinct qids). Same
  block protocol as run 2 (`scripts/22_run_blocks_design.py`, new config
  `configs/runs/squad_qwen4b_qc_fresh.toml`): shards are disjoint across replicates
  and each qid is measured at both depths (paired within question); block order
  randomized.
- **Step 2 dose-response (~1.5 h GPU):** 500 distractor qids, gold held first,
  appended distractors `d ∈ {0,1,3,7,15,31}` (≈k=1/2/4/8/16/32 prompt lengths),
  paired by question (3,000 generations). Position condition (gold at rank
  1/8/32 at fixed total length) runs **only if** the Step 1 stop rule passes.
  New script `scripts/30_qc_distractor.py`, block protocol, smoke first.
- **Step 3 dense 2×2 (~1 h GPU + CPU precompute):** bi-encoder
  `sentence-transformers/all-MiniLM-L6-v2` only (reranker out of scope; no
  download — cached, revision hash TBD at freeze). Rankings precomputed on CPU
  over the same 45,651 passages / 70-word chunks, frozen before any reader run
  (`scripts/31_qc_dense_precompute.py`). Reader GPU: dense 1,000 qids ×
  `k ∈ {4,32}` (2,000 generations); BM25 arm **reused from run 2**, no new BM25
  GPU time. Bootstrap resamples each retriever arm independently (paired within
  arm across `k`).
- **Step 4 padding (~0.2 h GPU):** ~600 generations of length-matched padding at
  fixed `k`, run last; separates prompt-length energy from passage-count effects.

## 5. Estimands

- **Fresh gap:** `Gap = A_oracle{1,4} − A(4)` on the fresh 1,000, with a paired
  95% CI; `A(1) − A(4)` reported alongside. This is the headroom number the
  position-condition stop rule uses.
- **Dose curve:** accuracy at each dose; per-dose paired differences vs dose 0
  (McNemar exact, Holm-corrected) + one-sided Cochran–Armitage trend test
  (primary). Energy per dose reported as a range only.
- **DiD:** `Δ = [A_d(4) − A_d(32)] − [A_b(4) − A_b(32)]` with a paired-within-arm
  bootstrap 95% CI; the **R/Q decomposition is reported before any accuracy
  claim**. Retriever energy measured separately, never folded into the reader
  comparison.

## 6. Energy method (Phase 7 lessons binding)

Block estimator primary: `E(k) = Σ_b J_block / Σ_b C`, randomized block order,
**120 s cooldown before every block**, idle sampled from the **tail of each
block's cooldown**, `PROTOCOL` tag in the resume ledger, per-run analysis dirs.
Per-query windows diagnostic only. Every joule is **GPU energy from NVML**;
absolute `J` is a range carrying the measured 3–6% between-occasion component —
the **ratio** is the reportable quantity.

## 7. Exclusions and stop rules

- Block invalid if reader reloads inside it (`load_s > 1.0`) or < 2 power
  samples; rerun once at end of schedule. Invalid queries stay wrong answers
  (P1 rule, D-009) unless the block is invalid. No outcome-based exclusions.
- **Stop rule:** fresh `Gap < 10%` → halt the position conditions (the 6-dose
  main curve still runs; the mechanism test needs headroom to be meaningful).
- Idle CV > 0.20 → run stops. Any frozen gate needing a new threshold → stop,
  study reported inconclusive.

## 8. Analysis

1. Fresh gap + paired CI (Step 1 reported before Step 2 position conditions).
2. Dose curve: McNemar per dose vs 0 + trend test; TOST equivalence with bounds
   +-2 pp if the curve is flat (a per-dose difference inside +-2 pp is equivalent to flat).
3. DiD with bootstrap CI + R/Q decomposition first; TOST with bounds +-2 pp if the DiD
   includes zero.
4. Padding contrast: length effect on `J` at fixed `k`.
5. No re-thresholding after outcomes (AGENTS.md §4); exploratory = labelled.

## 9. Frozen decision rules and G8 acceptance

G8 passes iff: (a) fresh gap reported; (b) causal contrast confirms direction
(trend negative, CI excludes flat) **or** a TOST-backed null is reported;
(c) dense DiD with CI **and** R/Q decomposition; (d) padding contrast reported.
Router items are out of scope by decision, not omission. Budget ~4.5 h measured
+ ~1 h contingency = **~5.5 h GPU**, batch 1, no concurrent jobs; `df -h` first.

## 10. Deviations

| Date | Original | Replacement | Reason | Outcome seen? |
|---|---|---|---|---|
| - | - | - | - | - |

## 11. Freeze block (complete at freeze, not before)

- File SHA-256: see `prereg/qc_prereg.sha256`
- Freeze tag: `prereg-qc-v1`
- Frozen by / date: PI instruction 2026-11-26 ("start implementation with subagents")
