# Roadmap — Depth Has a Knee → Q1 Hardening

**Status:** P0–P6 COMPLETE · Phase 6 (inference repair) COMPLETE 2026-11-25 · next: Phase 7 · last updated 2026-11-25
**Horizon:** 6–10 weeks · local RTX 3060 6 GB + optional H200 `1g.18gb` accuracy-only slice · ≤ $47 cash
**Repository:** https://github.com/Atik203/energy-optimal-rag · **branch model:** `dev` integration → `main` release (PRs only)
**Paper:** `paper/main.tex` (30 pp, 8 figs, 650 DPI) + `paper/out/main.pdf` · DOI `10.5281/zenodo.24352803` · tag `v0.2.1` behind `main`

**Legend:** ✅ done · ❌ gate fired (= finding, reported not tuned away) · 📋 todo · ⏳ in progress · 🔬 optional · ⏸️ blocked (needs approval/hardware). Phases 6–10 continue P0–P5; each phase ends at its G-gate.

This roadmap compresses finished work (§1) and specifies the Q1 program (§4) in agent-executable
detail. Gates are allowed to fire. A fired gate is a finding and must be reported, not tuned away.

---

## 1. Completed work (compressed — do not redo)

| Phase | Status | Result (one line; details in `docs/P*_RESULTS.md`) |
|---|---|---|
| Pilot (200 q × 7 k) | ✅ | Signal only: 2 pp dead (`P(k*)=0.61`); 5 pp uncertified (`k=4`, 69.3%) |
| P0 golden | ❌ | Calibration FAIL (`k=0` 0.7944 < 0.80); sweep uncalibrated |
| P1 (1,000 q × 7 k) | ❌ | 5 pp NOT established: `-4.30 pp`, lower `-6.17`, `p=0.2691`; savings `58.17%`; K3/K5/G1/G2 fail |
| P2 arms + probes | ✅ | H7 split (Qwen1.5B `+2.00` / HotpotQA `-10.80`); boundary/16k null; all energy uncalibrated |
| P3 policy | ❌ | G4 fail: capture `-2.46%`, AUC `0.733`; matched oracle `28.64%` (`n=186` test) |
| P4 + sims | ✅ | Coverage rejected 3/4; `R×Q` decomposition; 5 pp needs ~7.1k pairs |
| Metrology (D-028) | ✅ | Per-query NVML seq-dependent; P1 `J` provisional, P2 range-only |
| Paper + release | ⏳ | 30 pp + 8 figs; repro + backup done; release pending — owned by Phase 10 |

Rule: no new run re-thresholds P0–P4 gates. New data needs a **new prereg**; old runs are never patched.

---

## 2. Claim boundary (binding on all agents)

**Core thesis (audit round 2):** depth has a **knee**, not an optimum. Beyond `k≈4`, extra passages
buy recall the reader cannot use, so accuracy flattens while energy per correct rises 2.4× from
`k=4` to `k=32`. The knee sits where
recall gains and precision losses cancel, and its location is reader- and task-conditional.

**The decomposition is the paper** (k = 4 → max depth; from `analysis/recall_precision.json`):

| Arm | ΔR | ΔQ | Recall term `Q(4)·ΔR` | Precision term `R(max)·ΔQ` | Net ΔA |
|---|---:|---:|---:|---:|---:|
| P1 Qwen4B, 4→32 | +11.7 pp | −2.8 pp | **+6.8** | **−2.5** | +4.3 |
| Qwen1.5B, 4→32 | +11.4 pp | −8.0 pp | +5.2 | −7.2 | −2.0 |
| Llama3B, 4→32 | +11.4 pp | −13.3 pp | +6.9 | −12.0 | −5.0 |
| HotpotQA, 4→10 | +5.6 pp | +8.4 pp | +2.4 | +8.4 | +10.8 |

The recall term is stable (+2.4 to +6.9 pp); the precision term swings 20 pp. **Q, not R, sets the
sign of the depth effect.** This explains the near-zero 5 pp estimate, the k=4↔8 instability, the
P3 failure (BM25 predicts R, not Q), HotpotQA's strong transport, and why no universal `k*` exists.

**What may be claimed:** the paired contrast excludes zero (McNemar `p=0.0002`); the qualitative
saving (>20% under both estimators); the `R×Q` decomposition; the metrology negative; P3 as a
negative on a small test set; HotpotQA as **transport**, not replication.

**What may NOT be claimed:**
- No "5 pp falsified" and no "superiority confirmed". The 5 pp result is a **precision failure**
  (`p=0.2691` does not reject `d ≤ −5 pp`), and switching to a superiority estimand post hoc is
  itself a reviewer target. Say "not established" and "the paired contrast excludes zero".
- No absolute `J`, `E(0)`, `N*`, `S(k)`, or intercept `a` as results; report ranges/diagnostics.
- No universal `k*`; no adaptive-policy gain; no coverage-theory prediction; no `P(k*) ≥ 0.6` as a
  confirmatory criterion (see §4 Phase 6, item 8).
- No energy claim from H200/MIG, 16k probe, or any uncalibrated arm.
- No pooling SQuAD `A(4)−A(32)` with HotpotQA `A(4)−A(10)`.
- **No "7.21% non-abstention routing gap."** Under fixed per-depth block costs that gap is
  **0.000%** — it was per-query energy noise. The routing headroom is **22.5% vs static `k=4`**.
  P3's −2.46% must be described as a baseline-choice/measurement artifact, not as proof that
  BM25 features cannot route.
- **No per-query window energy as an estimator.** The window sum is 81.7% of the replay total;
  windows are diagnostic only.

---

## 3. Why this is not yet Q1 (audit rounds 1–3)

**Round 1 (3 reviewers):** B1 energy construct falsified · B2 power misspecified (discordance
0.131 vs planned 0.08; realized power 0.152; ~16.3k pairs for 80%) · B3 H7 disjunctive with shifted
reference · B4 post-selection inference ignored · B5 sensor/calibration fragility · B6 no wall
meter, CPU proxy, missing manifests · B7 contribution is a null without replacement.

**Round 2 (3 deep analyses) — plan-changing:**

- **R1 — Phase 7 was under-identified.** One replay/block ratio is **one equation for seven
  unknown per-depth biases**, and the factor is demonstrably not depth-common (`k=0` 0.8089 vs
  `k=32` 1.0587). A scalar cannot correct a per-depth curve.
- **R2 — Probe-based routing cannot pay for itself.** A reader-side probe (`k=0`, 14.59 J/query at
  A≈0.42) costs `≈34.8 J/correct`, far above the headroom available against a cheap baseline.
  Break-even is `≈1.8 J/query`. **Correction (round 3):** this rules out *probe-based* routing,
  not router policies built on **free pre-generation features** (BM25 + question shape), which carry
  no probe cost. R5 supersedes the earlier blanket conclusion.
- **R3 — The planned `P≥0.8 → ≥0.6` change is a forbidden re-threshold.** Keep 0.8 reported as
  failed; present 0.6 only as a simulation-derived exploratory "what would have been needed".
- **R4 — Sequencing errors:** rewriting energy prose before the estimator changes forces two
  rewrites; "reuse P1 rows + fresh split" is contradictory (P3 consumed all 1,000 IDs); picking
  Phase 9 after seeing Phase 8 is a forking path; the DOI is stale at v0.2.1.
- **R5 — The 7.21% router target is a measurement artifact (decisive).** The "non-abstention
  matched gap" is computed against static `k=1` with **per-query windows**. Recomputing the same
  oracle with **fixed per-depth block costs** gives **0.000%**: every question starts at the
  cheapest depth and the cheapest upgrades cost zero, so the gap is zero by construction. The
  7.21% exists only because some deeper rows measured cheaper than the same question's `k=1` row —
  the oracle was selecting **energy noise**, not a question property. Consequences: (a) P3's
  −2.46% is partly a baseline-choice artifact, not proof that BM25 features fail; (b) the correct
  routing headroom is against a **deeper** static depth — **22.5% vs `k=4`** on all 1,000 P1 rows
  (23.0% on the P3 test split), 38.1% vs `k=8`; (c) an exploratory binary rule (`k=1` if
  `p(correct@1) ≥ 0.355`, else `k=4`) already captured **60.3%** of the `k=4` gap at **−1.07 pp**
  on the reused P3 test IDs — feasibility, not confirmation.
- **R6 — Per-query windows are not a partition.** The recorded replay totals `7,336.9 J` vs block
  sum `7,195.7 J` (ratio 1.020), but the **per-query window sum is `5,996.7 J` = 81.7%** of the
  replay total. Windows miss 18.3% of the timeline, so they cannot be the estimator; a single
  global replay/block factor cancels in the savings ratio and leaves depth-specific bias intact.

---

## 4. Q1 hardening phases 6–10 (agent-executable)

Conventions: read `AGENTS.md` first; seeds from config, never literals; joules in J, accuracy in
[0,1], depths integers; `pytest -q`, `validate`, `ruff format/check` before commit; every number
traces to `runs/<run_id>/raw.csv` or registered output; never commit raw text, weights, secrets, or
`runs/<run_id>/` data (registry row only). Each phase lists goal, hypothesis, inputs, steps,
outputs, acceptance.

### Phase 6 — ✅ done 2026-11-25 · Inference repair and reframe (CPU-only, 0 GPU-h)

- **Goal:** remove the three places a methods reviewer finds an *error* rather than a limitation.
  No energy-language edits in this phase (those wait for Phase 7; see Phase 10).
- **Result (✅):** `docs/PHASE6_RESULTS.md`, `analysis/phase6/`, D-029, claims C-052–C-057.
  Cluster design effect 0.98 on 806 clusters (interval unchanged); energy is affine in prompt
  tokens (R2 0.902, BIC 29,290) better than in depth (0.888 / 30,212) and the depth coefficient
  conditional on tokens is −0.11 (SE 0.11); `k≥1` fit `a=26.90 [25.85,27.95]`, `b=2.149
  [2.055,2.243]`; cross-fitted selection picks `k=4` in all five folds with a 58.13% held-out
  saving and a 0.03 pp winner's curse, while K3 stays failed at 0.7244; P3 capture corrected to
  −9.8% [−22.8,−1.8] against the matching 7.21% gap; H7 on 1.5B relabelled inconclusive
  (95% CI −1.46 to +5.46); gold-first overload −3.73 pp [0.73, 6.72]; three readers on the same
  500 IDs are −2.80 / +2.00 / +5.00 pp. Paper held at 30 pages; 426 tests pass.
- **Hypotheses:** (H-cost, re-analysis) the paired contrast is negative; (H-het) the depth effect
  is reader×task-conditional; (H-cancel) `Q` term dominates the sign.
- **Inputs:** `analysis/squad_qwen4b_p1/{noninferiority,bootstrap}.json`,
  `analysis/recall_precision.json`, `analysis/inference/p1.json`, `analysis/policy/policy.json`,
  `analysis/simulations/s3.json`, `paper/main.tex`.
- **Steps:**
  1. **Article-level clustering.** SQuAD has multiple questions per paragraph; question-level
     bootstrap ignores within-article correlation. Report cluster-robust SE and the design effect
     before publishing the NI bound — this can only widen the interval.
  2. **Token-vs-depth confound.** Refit `J = a + c·T` (prompt tokens) against `J = a + b·k`;
     compare AIC/BIC and lack-of-fit. If tokens explain it, H1 is "cost of tokens", not "cost of
     depth" — state which.
  3. **Uncertainty on the affine fit.** CIs on `a` and `b` (inverse-variance or cluster-weighted),
     correct residual df, and no `k=0` intercept claim.
  4. **Selection-adjusted inference.** Repeated 2-/5-fold cross-fitting plus a parametric-bootstrap
     winner's-curse correction. Split-half at `n=1,000` leaves 500 per side and cannot resolve 5 pp.
  5. **Reframe P3 and H7 honestly.** P3 capture `−2.46%` needs a bootstrap CI (almost certainly
     ±25 pp at `n=186`) → "no evidence of gain", not "the policy fails". H7 Qwen1.5B `+2.00 pp`
     with upper `+4.90` is **inconclusive**, not a sign reversal.
  6. **Gatekeeping, not labelling.** Fixed hierarchical chain (H2 primary → H3/H4 descriptive → H7
     split-α), or no p-values on secondary hypotheses. State that `k=4` was pilot-selected, so the
     confirmatory test is conditional on that candidate.
  7. **Free mechanism analyses.** (a) Gold-rank-conditional accuracy: condition on the gold passage
     being rank 1 and compare `k=1` vs `k=32` — direct evidence for reader overload vs retrieval
     failure. (b) Same-ID 3-reader subset: restrict to the 500 IDs shared by Qwen1.5B/Llama so the
     reader contrast is not confounded by different question sets.
  8. **Cancel the re-threshold.** Keep `P(k*)≥0.8` reported as **failed**; add an explicitly
     exploratory, simulation-derived section on what stability would have been needed.
  9. **Positive deliverables from existing data.** `k*(δ)` frontier table; "price of the
     guarantee" (10→5 pp costs 3.7 pp of savings; 5→3 pp costs 7.8; 3→2 pp costs 17.5;
     `E(4)/E(2) ≈ 1.10`); cancellation table promoted to the Fig. 1 slot.
  10. **Hygiene:** README/DOI drift, v0.2.0 vs v0.2.1, "no confirmatory results" line, title.
- **Outputs:** edited `paper/main.tex` (structure + numbers, no energy prose), regenerated
  `p1_contrasts.png` / new cancellation figure, `analysis/inference/` additions, `docs/DECISIONS.md`.
- **Acceptance (G6):** cluster-robust SE reported; token-vs-k comparison reported; no absolute-J
  claim without range; 5 pp labeled "not established"; 0.8 still failed; `verify_main.py` clean;
  420 tests pass.
- **Effort:** small, CPU-only, ~1 day with agents.

### Phase 7 — 📋 todo · Metrology: block estimator + falsified windows (5–8 GPU-h) — DO SECOND

- **Goal:** replace the falsified per-query window with a block estimator, and report the window
  failure as a finding rather than correcting it with a scalar.
- **Hypotheses:**
  - **H-M1 (window falsification):** the per-query window sum is not a partition of the replay
    total (already observed `0.8173`); therefore windows are diagnostic only.
  - **H-M2 (CV):** per-depth CV is ≤ a pre-specified threshold at `k ≥ 4`; `k ∈ {0,1}`
    reported but not gated.
  - **H-M3 (carryover):** `J(k | preceding depth)` differs across predecessors; quantify `γ`.
- **Inputs:** `docs/MEASUREMENT_VALIDITY.md`, `analysis/calibration_bias.json`,
  `analysis/measurement/replay_qwen15b.json`, `runs/squad_qwen4b_p1/{blocks,repeat,manifest}.json`.
- **Steps (new run IDs + new prereg — never patch P1):**
  1. **Block estimator is primary.** `B ≥ 5` blocks per depth, all seven depths, `Q = 20`,
     randomized block order, cooldown at every block start, pre-specified discard `W`, **same
     question set per block**. Integrate the block window as one measurement, subtract idle over the
     block, and use the ratio of sums:
     `E(k) = Σ_b J_block(k,b) / Σ_b C(k,b)`; `Sav = 1 − E(4)/E(32)`. CI = cluster bootstrap
     over blocks (and questions for the accuracy denominator).
  2. **Replays as validation, not correction.** `R ≥ 10` replays (exact sweep permutation plus
     different permutations). Report the **distributions** of `replay/block` and
     `per-query sum/replay` with 95% CIs. Do **not** apply a single global factor: it cancels in the
     savings ratio and leaves depth-specific bias.
  3. **Carryover regression (uses existing rows).** Fit
     `J_i = α + βk_i + γk_{i−1} + δtemp_i + εclock_i` with cluster-robust SEs; report `γ`.
     Add a crossed subset: for target depth `k`, vary the predecessor over `{0,4,32}`.
  4. **CV distributions.** All seven depths, 5 blocks; report full distributions, not median/max.
  5. **Depth-resolved wall meter** (last step, then re-baseline idle): condition `k ∈ {1,4,32}`
     (~1 h) matching the new block run's power mode/thermal state. Report
     `system_J/(GPU_J + CPU_proxy)` as a **range**; never rescale P1.
  6. **Manifest schema.** Driver, CUDA, power mode, clocks, Ollama version/digest, model digest,
     HF cache/revision, ambient temperature, throttle reasons, screen/AC state, batch size,
     concurrency. Backfill a P1 sidecar with `unknown` — **never fabricate** values.
  7. **Affine fit on `k ≥ 1`**; `k=0` reported as a floor, not a fit point.
- **Outputs:** `prereg/measurement_hardening_prereg.md` (frozen before runs), `runs/<block*>/`,
  `analysis/measurement_hardening/`, updated validity figure, `docs/DECISIONS.md`.
- **Acceptance (G7):** block estimator with CI; windows explicitly reported as falsified (`0.817`)
  and not used; `γ` reported; CV distributions for all seven depths; wall ratio as a range;
  manifest complete.
- **Effort:** medium; single GPU, batch 1, no concurrent jobs; `df -h`/`du -sh` before runs.

### Phase 8 — 📋 todo · Causal tests + retargeted router (6–9 GPU-h) — THE Q1 BET

- **Goal:** identify the mechanism causally, and test a router that has **real** headroom.
- **Correction that drives this phase (R5):** the quoted 7.21% gap is a per-query-noise artifact
  (`0.000%` under fixed block costs vs `k=1`). The real headroom is against static `k=4`:
  **22.5%** on all 1,000 P1 rows, **23.0%** on the P3 test split. An exploratory rule captured
  **60.3%** of it at `−1.07 pp` — feasibility only.
- **Hypotheses:**
  - **H-overload:** at fixed gold rank 1, adding distractors lowers accuracy (reader overload, not
    retrieval failure).
  - **H-dense:** precision collapse is a BM25-rank artifact; dense retrieval restores monotonicity
    or shifts the knee.
  - **H-route:** a pre-generation policy captures ≥ 30% of the `k=4` gap at a 2 pp accuracy margin.
- **Steps:**
  1. **Freeze `prereg/qc_prereg.md` first**, then draw a **fresh sample ≥ 1,000 SQuAD dev
     questions not in P1/P3**, run `k ∈ {1,4}` (~2,000 generations, ~1 h). **Report the `k=4`
     oracle gap before running the policy; stop rule: gap < 10% → do not run it.**
  2. **C3 distractor dose-response (1–2 h).** 300–500 questions with gold at rank 1 at `k=1`;
     hold gold first and add 0/1/3/7/15/31 distractors after it. Add a position condition (gold at
     rank 1/8/32 at fixed `k`). Paired McNemar/GLMM + trend test. This is the causal test of `Q`.
  3. **C2 dense 2×2 (2 h, `n = 1,000`).** Use **already-cached** models (no download):
     `sentence-transformers/all-MiniLM-L6-v2` (rev `1110a243…`, Apache 2.0) and the
     `cross-encoder/ms-marco-MiniLM-L-6-v2` reranker (rev `233902d2…`). Same 45,651 passages,
     same 70-word chunks, same reader/prompt/decoding, same `k` grid. Precompute and freeze rankings.
     Estimand: `Δ = [A_d(4)−A_d(32)] − [A_b(4)−A_b(32)]` with a paired bootstrap.
     Report `R/Q` decomposition **before** the accuracy claim; retriever energy measured separately.
     `n=500` is direction-only.
  4. **Router (primary, pre-generation).** Features: BM25 top/second/gap/mean/std/entropy/n-positive,
     question length, wh-type, plus a few pre-generation interactions. **No `p(correct|k=0)`**
     (constant 0.001, leaky, and probe-dominated), no gold presence, no post-generation signal in the
     primary arm. Mandatory baselines: static `k=1/4/8/32`, P3 BM25-only, presence oracle,
     confidence-only, random with the same depth histogram, knapsack oracle, and one
     Adaptive-RAG/Self-RAG/FLARE/IRCoT-style baseline or a defensible justification. Report capture
     **with a CI**, accuracy difference, energy difference, depth histogram, AUC, calibration,
     learning curve.
  5. **Decision rule (frozen):** capture ≥ 30% of the `k=4` gap with 95% CI lower bound > 0,
     and accuracy-loss CI lower bound > `−2 pp`. Null conditions: fresh gap < 10%; capture CI
     includes 0; accuracy beyond margin; flat ablation.
  6. **Value-of-information note.** Probe-based routing cannot pay (`≈34.8 J/correct` probe vs
     `≈7.3 J/correct` headroom); pre-generation routing can, because its features are free.
     Report both, and use this to explain P3.
  7. **Token-matched padding (0.5 h)** and **equivalence tests (TOST)** for null claims.
- **Outputs:** `prereg/qc_prereg.md` + freeze tag, `runs/<qc_*>/`, `analysis/qc_*/`, new
  `artifacts/claims_evidence.csv` rows, `artifacts/ledger.csv` rows.
- **Acceptance (G8):** fresh gap reported; router capture CI with the 2 pp margin (or documented
  null with MDE); causal contrast confirms direction; dense DiD with CI and `R/Q` decomposition.
- **Effort:** medium; dense models already cached — no download approval needed unless a
  retrieval-tuned encoder (`BAAI/bge-small-en-v1.5`, ~133 MB) is requested.

### Phase 9 — 🔬 optional · Pick at most one (0–2 GPU-h)

- **D3 token-level attribution** (0 GPU-h if timestamps kept): prefill vs decode per `k`,
  `J/prefill-token` constancy — upgrades H1 to a hardware-grounded model. **Do this first.**
- **D2 abstention-aware policy** (1–2 h) as a *secondary* arm alongside the Phase 8 depth
  router. The 28.64% abstention figure is a coverage/selective-prediction gain, not depth routing —
  report it under that label, with its own cost accounting.
- **Dropped: reader-strength scaling law.** The premise is already contradicted by the data
  (Qwen1.5B does not peak early; Llama peaks at 4; Qwen4B rises to 32), and `n=300` cannot identify
  `k_peak` vs size.

### Phase 10 — 📋 todo · Rewrite, artifact, release (CPU-only)

- **Goal:** 15–18 pp + supplement, structured by claim not by project phase.
- **Steps:**
  1. **Clean-room repro first** — it may reveal missing files that force re-runs, which cannot be
     afforded at the end.
  2. **Energy prose (deferred 6b):** all absolute `J/E/N*/S(k)/a` → ranges/diagnostics; point + CI
     stated once with "provisional".
  3. **Structure:** decision problem → paired design + measurement audit → cost curve + context
     share → accuracy cost + margin frontier → `R/Q` cancellation + P3 failure → heterogeneity →
     per-deployment calibration → limitations.
  4. **Cut:** P0 forensics → 3 sentences; gate alphabet → G1/G4; S1–S3 → 1 paragraph; identity
     derivation → footnote; notation/checklist schematics → supplement. Keep claim map at 8–10 rows.
  5. **Venue chosen before Phase 8:** IR/ML (IP&M, KBS, Information Sciences, Patterns, TMLR) with
     energy as a ratio-based secondary claim; an energy venue makes the wall meter and a second
     hardware class mandatory.
  6. **Retitle** away from "Energy-Optimal": *Depth Has a Knee: Reader-Conditional Accuracy–Energy
     Trade-offs in Retrieval-Augmented Generation*.
  7. **Artifact:** release predictions (SQuAD is CC BY-SA; withholding outputs makes the headline
     negative unverifiable), full lock + manifest, one-command repro, cell-level number→artifact→hash
     map, MLPerf-Power field mapping, artifact-appendix checklist.
- **Acceptance (G10):** traceability, DPI, clean-room repro, Overleaf `main.tex` root verified.
- **Release checklist (pending):** 1) Overleaf compile matches `paper/out/main.pdf`; 2) clean-room
  repro passes; 3) secret scan clean; 4) publish **v0.3.0 before submission** (current DOI is
  v0.2.1, behind `main` — a reviewer clicking it gets a different paper); 5) tag + push;
  6) verify `docs/BACKUP.md` checksums.

---

## 5. Gates (G6–G10 exit gates; old K/G frozen as history)

| Gate | Phase | Criterion | Pass action |
|---|---|---|---|
| **G6** | 6 | Cluster-robust SE + token-vs-k + cross-fit reported; 5 pp = "not established"; 0.8 still failed | Enter Phase 7 |
| **G7** | 7 | Block estimator with CI; windows falsified (0.817) and unused; carryover `γ` reported; CV for all seven depths; manifest complete | Block estimator is the primary energy result |
| **G8** | 8 | Prereg frozen; fresh `k=4` gap reported; router capture CI vs 2 pp margin; causal contrast direction; dense DiD with CI | Headline contribution (or documented null with MDE) |
| **G10** | 10 | 15–18 pp; traceability; clean-room repro; v0.3.0 DOI + tag | Submit |

A gate may not be added, removed, or re-thresholded after seeing the primary outcome. New studies
get new preregs; amendments go in `prereg/amendments.md` + `docs/DECISIONS.md`.

---

## 5b. Q1 acceptance outlook (reviewer judgment, not data)

| Stage completed | Paper becomes | Est. Q1 chance |
|---|---|---:|
| Now | Rigorous null + provisional joules | ~10% |
| + Phase 6 | Statistically clean negative + mechanism | ~25–30% |
| + Phase 7 | Block-identified joules; windows falsified | ~35–40% |
| + Phase 8 | Knee + causal control + confirmed router | ~50–60% |
| + Phase 10 | Full paper + artifact | ~55–65% |

Reading: Phase 6 is the best credibility per hour (free). Phase 8 is the biggest single jump,
and it is now a *positive* bet rather than a bound: the retargeted `k=4` gap is 22.5% and the
exploratory rule already captured 60% of it. If the fresh confirmation fails, the paper falls back
to ~40–45% (knee + causal control, no router). The residual ceiling is scope — one confirmatory corpus, one retriever family, one
laptop class — which no phase removes; only a second corpus or second hardware class would, and
both are outside budget. If Phase 8's causal contrast comes back flat or inverted, the fallback is
a measurement/reproducibility venue or a short paper, not a tuned positive.

---

## 6. Budget and schedule

| Item | Cost | Notes |
|---|---|---|
| GPU compute (Phases 7–9) | **$0** | Local RTX 3060 6 GB, batch 1, single job; **~12–18 GPU-h** new work (Phase 7 5–8, Phase 8 6–9, Phase 9 0–2) |
| Electricity | ~$2 | Indicative, not metered billing |
| Wall meter | **$25** | Depth-resolved 3×3×100 run (Phase 7, last) |
| Backup USB | $10 | Verify checksums before new runs |
| Contingency | $10 | Hard cap **≤ $47** unchanged |
| Storage | 0 | Project space only; `df -h`/`du -sh`; 200 GB quota |
| H200 slice | $0 | Accuracy-only replication only; SSH via `uiu-h200`; **no energy claim** |

Order: **Phase 6 (now) → 7 → 8 → 9 (optional) → 10.** Do not run the new sweep on the old
estimator. Do not train on P3 test IDs. Do not download weights, use paid APIs, or write outside
`E:\PROJECT\energy-optimal-rag` without asking.

---

## 7. Deliverables (additive)

1. `prereg/measurement_hardening_prereg.md` and `prereg/qc_prereg.md` (+ freeze tags) before
   any Phase 7/8 outcome.
2. `runs/<new_id>/raw.csv` + registry rows + `analysis/<phase>/` for Phases 7–9.
3. Updated `paper/main.tex`, figures (≥600 DPI), `paper/out/main.pdf` via Overleaf `main.tex` root.
4. Extended `artifacts/claims_evidence.csv` + `artifacts/ledger.csv`.
5. `docs/DECISIONS.md` entries for every estimator/hardware/environment change.
6. New Zenodo version **v0.3.0** + tag from clean `main` after clean-room repro.

---

## 8. Out of scope

- Universal `k*`; frontier/API readers; dense-retriever *training*; multi-GPU/datacenter energy;
  carbon-optimal beyond a banded, explicitly illustrative conversion; production/SLO study.
- 5 pp re-certification at ~7–16k pairs as the sole Q1 bet (exceeds budget, still null-prone).
- **Probe-based** routing as a claim (a `k=0` probe costs ~34.8 J/correct vs ~7.3 J/correct of
  headroom). Pre-generation routing on free features is in scope and is Phase 8's primary test.
- H200 energy via MIG (`power.draw = N/A`); 32k CPU-offload; raw-text redistribution.

---

## 9. Change control (binding)

1. `prereg/PREREGISTRATION.md` + `analysis_plan.md` stay frozen at `prereg-freeze-v1`; deviations →
   `prereg/amendments.md` (date, original, replacement, reason, outcome-seen?) + `docs/DECISIONS.md`.
2. New-data phases require a **new** frozen prereg + tag before outcomes are read.
3. Gate re-thresholding after seeing an outcome is forbidden — including the `0.8 → 0.6` change.
4. Secret scan + `git status` before any data/config commit; `pytest -q`, `validate`,
   `ruff format` + `ruff check` green before any paper-affecting commit.
