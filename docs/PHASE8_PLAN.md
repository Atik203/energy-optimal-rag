# Phase 8 plan — causal mechanism: distractor dose-response + dense 2×2 (no router)

**Status:** plan for approval, 2026-11-26. No GPU run starts until `prereg/qc_prereg.md`
is frozen and tagged.
**Budget:** ~4.5 h measured + ~1 h contingency = **~5.5 h GPU**, single RTX 3060 Laptop,
batch size 1, no concurrent jobs. No wall meter (D-031). No downloads (dense models cached).
**Claim boundary:** unchanged. No universal `k*`, no adaptive-policy claim (router dropped),
no absolute joule figure as a guarantee, GPU energy only.

## Why this is the Q1 bet

Phase 7 established the knee (`E(k)` minimised at `k=1`–`k=2`, flat to `k=4`, steep after)
and the R/Q cancellation (recall +2.4 to +6.9 pp, precision −12.0 to +8.4 pp) as descriptions.
Phase 8 tests the mechanism causally:

- **H-overload:** at fixed gold rank 1, adding distractors lowers accuracy (reader overload,
  not retrieval failure). Causal test of the precision term `Q`.
- **H-dense:** the precision collapse is a BM25-rank artifact; dense retrieval restores
  monotonicity or shifts the knee. Tests whether the knee travels with the retriever.

The router is **dropped** (owner decision 2026-11-26, following the audit: real headroom is
22.5% vs static `k=4`, but routing is not the Q1 argument). No H-route, no policy capture
claim, no Adaptive-RAG baseline needed.

## Energy method (Phase 7 lessons are binding)

- Block estimator is primary: randomized block order, 120 s cooldown, idle sampled from the
  **tail of each block's cooldown**, `PROTOCOL` tag in the resume ledger, per-run analysis
  directories. Per-query windows are diagnostic only.
- Every joule is **GPU energy from NVML**. Absolute `J` is a range; the **ratio** is the
  reportable quantity (sessions held it to 0.92 pp across a 3–6% level shift).
- Smoke first on every GPU script; resume-safe ledgers; `df -h` before runs.

## Step 0 — prereg freeze (CPU, gating)

Write `prereg/qc_prereg.md` with estimands, hypotheses, sample frames, decision rules, and
the G8 acceptance below. Freeze and tag **before any GPU run** (pattern:
`prereg-measurement-v1` → tag `prereg-qc-v1`, record SHA-256). Any later change goes in
`prereg/amendments.md` + `docs/DECISIONS.md`, never by editing the frozen file.

## Step 1 — fresh `k=4` gap (GPU ~0.8 h, gating)

- **Frame:** fresh sample of **1,000 SQuAD dev questions not in P1/P3 or any earlier split**
  (10,570 total; 2,250 used across p0/p1/replication/boundary/context/tax; P3 is a hashed
  subset of P1, so excluding P1 excludes P3). Deterministic exclusion by qid, seed
  `20261115`, recorded in the prereg.
- **Design:** `k ∈ {1,4}`, 5 blocks × 200 disjoint questions per depth (same protocol as
  run 2), ~2,000 generations. Reuses `scripts/22_run_blocks_design.py` with a new
  `configs/runs/squad_qwen4b_qc_fresh.toml`.
- **Report first:** the `k=4` oracle gap on this sample. **Stop rule: gap < 10% → halt the
  dose-response position conditions** (the mechanism test needs headroom to be meaningful).
- **Time:** decode ~17 min (k=1 ≈ 92 s + k=4 ≈ 109 s per 200-block × 5) + 10 × 120 s
  cooldowns ≈ 37 min + startup/baselines ≈ **45 min**.

## Step 2 — distractor dose-response (GPU ~1.5 h, THE causal test)

- **Frame:** 500 questions (owner decision), disjoint from Step 1, with gold at rank 1 at
  `k=1` under BM25.
- **Doses:** hold gold first, append 0/1/3/7/15/31 distractors after it (6 levels ≈
  k=1/2/4/8/16/32 in prompt length). Paired by question across doses.
- **Position condition:** gold at rank 1/8/32 at fixed total length (only if the Step 1
  stop rule passes). Separates position sensitivity from pure length.
- **Analysis:** paired McNemar/GLMM per dose vs dose 0 + trend test over dose. Estimand is
  the accuracy dose curve; energy per dose is reported as a range. New script
  `scripts/30_qc_distractor.py` (block protocol, smoke first).
- **Time:** decode ≈ 41 min (0.46+0.47+0.54+0.70+0.96+1.81 s/q × 500) + cooldowns ≈
  12 min + position conditions ≈ 35 min ≈ **~1.5 h**.

## Step 3 — dense 2×2 (GPU ~1 h + CPU precompute)

- **Encoder:** `sentence-transformers/all-MiniLM-L6-v2` (cached in `G:\SmartScan-Cache\hf\hub`;
  verified 2026-11-26). No download. Cross-encoder reranker stays out of scope.
- **Precompute (CPU):** dense rankings over the same 45,651 passages, same 70-word chunks,
  frozen before any reader run. New script `scripts/31_qc_dense_precompute.py`. Record the
  model revision hash in the prereg.
- **Reader (GPU):** 1,000 fresh questions (disjoint from Steps 1–2) × `k ∈ {4,32}` under
  dense rankings. The BM25 arm is **reused from run 2** — no new BM25 GPU time.
- **Estimand:** `Δ = [A_d(4) − A_d(32)] − [A_b(4) − A_b(32)]` with a paired bootstrap, and
  the **R/Q decomposition before the accuracy claim**. Retriever energy measured separately
  and reported, never folded into the reader comparison silently.
- **Direction rule:** `n=500` would be direction-only; with `n=1,000` the DiD is adjudicated.
- **Time:** decode ≈ 39 min (0.54 s/q × 1000 + 1.81 s/q × 1000) + 10 × 120 s cooldowns ≈
  **~1 h**.

## Step 4 — token-matched padding (GPU ~0.2 h)

~600 generations of length-matched padding at fixed `k` to separate prompt-length energy
from passage-count effects. Small, runs last among GPU work.

## Frozen decision rules (go in the prereg, not here)

- G8 needs: fresh gap reported; causal contrast confirms direction (distractor trend
  negative with CI excluding flat); dense DiD with CI **and** R/Q decomposition.
- Nulls are findings: flat dose curve, dense DiD including zero, or a dense knee at the
  same place (mechanism is reader-side, not rank-artifact) are all reported, not tuned away.
- Equivalence (TOST) for any null claim; no re-thresholding after outcomes (AGENTS.md §4).

## Outputs and acceptance

- `prereg/qc_prereg.md` + freeze tag + SHA-256.
- `runs/<qc_fresh|qc_distractor|qc_dense>/`, `analysis/qc_*/` (per-run dirs), registry rows,
  `artifacts/ledger.csv` rows, `artifacts/claims_evidence.csv` rows (C-070+), `docs/DECISIONS.md`
  (D-034+), `docs/PHASE8_RESULTS.md`.
- **Acceptance (G8):** fresh gap reported; causal contrast direction confirmed with trend CI;
  dense DiD with CI and R/Q decomposition; token-padding contrast reported. Router items are
  out of scope by decision, not by omission.

## Risks

| Risk | Mitigation |
|---|---|
| Thermal/idle drift (Phase 7 replay lesson) | Cooldown-separated blocks, idle from cooldown tail, protocol-tagged ledger, smoke first |
| Fresh sample overlaps P1/P3 | Deterministic qid exclusion, recorded before the freeze |
| Dense rankings shift mid-phase | Precompute once, freeze, hash the revision |
| Scope creep (reranker, bge, router) | Explicitly out; each needs a new decision + prereg amendment |
| Absolute-J overclaim | Ratios only; level reported as a range with the 3–6% occasion component |

## Timeline

1. Prereg freeze + tag (CPU, ~1 h with review).
2. Step 1 GPU (~0.8 h) + analysis (CPU) — stop-rule checkpoint.
3. Step 2 GPU (~1.5 h) + Step 3 precompute (CPU, parallel-safe: no GPU).
4. Step 3 GPU (~1 h) + Step 4 (~0.2 h) + close-out (CPU).
