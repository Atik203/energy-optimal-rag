# Roadmap — Depth Has a Knee → Q1 Hardening

**Status:** P0–P6 COMPLETE · 2 audit rounds COMPLETE (6 reviewers, 2026-11-22) · entering Q1-hardening · last updated 2026-11-23
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

---

## 3. Why this is not yet Q1 (audit round 1 + round 2)

**Round 1 (3 reviewers):** B1 energy construct falsified · B2 power misspecified (discordance
0.131 vs planned 0.08; realized power 0.152; ~16.3k pairs for 80%) · B3 H7 disjunctive with shifted
reference · B4 post-selection inference ignored · B5 sensor/calibration fragility · B6 no wall
meter, CPU proxy, missing manifests · B7 contribution is a null without replacement.

**Round 2 (3 deep analyses) — new, plan-changing:**

- **R1 — Phase 7 was under-identified.** One replay/block ratio is **one equation for seven
  unknown per-depth biases**, and the factor is demonstrably not depth-common (`k=0` 0.8089 vs
  `k=32` 1.0587). A scalar cannot correct a per-depth curve.
- **R2 — The router cannot pay for itself.** Non-abstention headroom is `7.21% × 59.57 ≈ 4.3
  J/correct`; the cheapest reader-side probe (`k=0`, 14.59 J/query at A≈0.42) costs `≈34.8
  J/correct`. Break-even probe is `≈1.8 J/query` (~12% of a `k=0` pass). Routing is net-negative
  even if perfect — a finding, not a feature. G8 must therefore bound the value of routing, not
  hunt for 30% capture on 186 questions.
- **R3 — The planned `P≥0.8 → ≥0.6` change is a forbidden re-threshold.** Keep 0.8 reported as
  failed; present 0.6 only as a simulation-derived exploratory "what would have been needed".
- **R4 — Sequencing errors:** rewriting energy prose before the estimator changes forces two
  rewrites; "reuse P1 rows + fresh split" is contradictory (P3 consumed all 1,000 IDs); picking
  Phase 9 after seeing Phase 8 is a forking path; the DOI is stale at v0.2.1.

---

## 4. Q1 hardening phases 6–10 (agent-executable)

Conventions: read `AGENTS.md` first; seeds from config, never literals; joules in J, accuracy in
[0,1], depths integers; `pytest -q`, `validate`, `ruff format/check` before commit; every number
traces to `runs/<run_id>/raw.csv` or registered output; never commit raw text, weights, secrets, or
`runs/<run_id>/` data (registry row only). Each phase lists goal, hypothesis, inputs, steps,
outputs, acceptance.

### Phase 6 — 📋 todo · Inference repair and reframe (CPU-only, 0 GPU-h) — DO FIRST

- **Goal:** remove the three places a methods reviewer finds an *error* rather than a limitation.
  No energy-language edits in this phase (those wait for Phase 7; see Phase 10).
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

### Phase 7 — 📋 todo · Metrology identification (5–7 GPU-h) — DO SECOND

- **Goal:** turn two biased estimators into one identified, bounded answer (fixes R1).
- **Hypotheses:** (H-ident) per-depth calibration factors are identifiable from ≥3 permutation
  replays; (H-common) the factor is *not* depth-common beyond the floor — to be tested, not assumed.
- **Inputs:** `docs/MEASUREMENT.md`, `docs/MEASUREMENT_VALIDITY.md`,
  `runs/squad_qwen4b_p1/{blocks,repeat,manifest}.json`.
- **Steps (new run IDs + new prereg — never patch P1):**
  1. **Replay the primary arm.** The existing replay was Qwen1.5B; replay **P1's exact
     permutation** as a continuous block (1–2 h). Split into 4 × 30 min sessions with the same
     permutation and test for boundary drift (a 2 h continuous replay is itself a thermal confound).
  2. **Over-identify the factors.** Run **three replays under different permutations**, or
     pre-specify a one-parameter bias model `bias_k = c·g(k)` with `g` fixed in advance. A single
     scalar ratio cannot be the primary estimator for a 7-point curve.
  3. **Known-load validation.** Burn a fixed constant-power synthetic load for N seconds; compare
     the NVML integral to `P×t`. The chain has never been checked against a known energy.
  4. **Interleaved calibration blocks.** Blocks after a 2.5 h sweep measure the hot state, not the
     sweep's mean. Interleave every ~500 queries (or pre/post and interpolate).
  5. **Hierarchical bootstrap.** Resample blocks *and* queries so factor uncertainty enters the
     savings CI; today the factor is a point correction.
  6. **Convergence rule.** Sweep / block / replay / deconvolution side by side with a pre-specified
     tolerance (e.g. ±3 pp) deciding which is primary.
  7. **Depth-resolved wall meter** (∼$25, last step, then re-baseline idle): 3 depths × 3 repeats ×
     100 queries, and **test** the depth-common-factor assumption (ratio homogeneity). One
     aggregate number cannot support the invariance argument.
  8. **CPU energy or retitle.** Measure CPU package energy (RAPL/HWiNFO) or explicitly retitle to
     GPU energy; the `20 W × t` proxy is applied to BM25 wall time and is approximately k-invariant,
     so "retrieval share falls with k" is a denominator artifact.
  9. **Session variance.** ≥3 independent sessions on `n=200` subset (`k∈{1,4,32}`); report ICC.
  10. **Carryover control.** Williams/Latin-square subset at `k∈{1,4,16,32}` plus a lag-adjusted
      estimator (preceding depth as covariate). Randomisation balances but does not debias.
  11. **Pilot↔P1 bridge.** ~100 common questions under both protocols on one day to decompose the
      `+53%` intercept shift (15.74→24.08 J).
  12. **Baseline sensitivity.** Pre-run idle vs local pre-query floor vs per-window floor: three
      savings values. Plus thermal traces, clock-vs-J scatter, drop-first-50 numerically.
- **Outputs:** `runs/<replay*>/`, `runs/<repeat*>/`, `analysis/measurement_hardening/`, updated
  validity figure, `docs/DECISIONS.md`.
- **Acceptance (G7):** per-depth factors identified (or bias model pre-specified and tested);
  estimators agree within tolerance **or** the claim is demoted; known-load check within a stated
  budget; wall factor depth-common or explicitly rejected.
- **Effort:** medium; single GPU, batch 1, no concurrent jobs; `df -h`/`du -sh` before runs.

### Phase 8 — 📋 todo · Causal identification + transport (4–6 GPU-h) — THE Q1 BET

- **Goal:** turn the descriptive `R×Q` decomposition into an identified mechanism and a transport
  claim. **Not** a router hunt.
- **Hypotheses:** (H-overload) at fixed gold rank 1, adding distractors lowers accuracy — reader
  overload, not retrieval failure; (H-dense) precision collapse is a BM25-rank artifact, so dense
  retrieval restores monotonicity or shifts the knee; (H-voi) routing cannot repay its probe cost.
- **Steps:**
  1. **Freeze `prereg/qc_prereg.md` first** (before any outcome is read, including calibration
     factors). Then run a **new 500 × 7 SQuAD sweep** (~1.5 h) as the Phase 8 test set — P3 consumed
     all 1,000 P1 IDs, so a fresh split requires fresh questions.
  2. **C3 distractor dose-response (1–2 h, highest value).** 300–500 questions where gold is rank 1
     at `k=1`; hold gold first and add 0/1/3/7/15/31 distractors after it. Add a position condition
     (gold at rank 1/8/32 at fixed `k`). Paired McNemar/GLMM + trend test. This is the causal test
     of `Q` and pre-empts the position-bias objection.
  3. **C2 dense 2×2 (1.5–2 h).** {BM25, dense} × {raw order, cross-encoder rerank}, `k∈{4,16,32}`,
     `n=500`; report `recall@k` for both retrievers and index-build joules with amortisation
     break-even. Do not confound retrieval quality with ordering. Inference-only; **ask before
     downloading weights**.
  4. **Held-out replication (1 h).** `A(4)−A(32)` on the fresh 1,000-question split, accuracy only.
     Cheap test of whether −4.30 pp is stable or a sampling draw.
  5. **Token-matched padding (0.5 h).** Fixed prompt tokens, vary the number of *relevant*
     passages — separate relevance from length.
  6. **Value-of-information bound (0 GPU-h).** Formally: routing pays only if
     `probe_cost < headroom(δ)/A`. With the measured `k=0` probe this fails by ~8×. Report the
     break-even probe cost and the `capture(δ)` curve. **This is a positive contribution that
     explains P3.**
  7. **Router — optional only.** If run: cross-fit on all 1,000 questions (not `n=186`), include
     abstention (the 28.64% prize), charge probe cost, report ECE/Brier, random-depth null with the
     same marginal histogram, and set the criterion to a minimum detectable effect (≥5% energy at
     matched accuracy, 95% CI excluding zero). Budget 4–6 h. It does not gate the paper.
  8. **Equivalence tests** (TOST) for null claims ("dense does not restore monotonicity", "router
     adds nothing") with pre-specified margins.
- **Outputs:** `prereg/qc_prereg.md` + freeze tag, `runs/<qc_*>/`, `analysis/qc_*/`,
  new `artifacts/claims_evidence.csv` rows, `artifacts/ledger.csv` rows.
- **Acceptance (G8):** a pre-specified causal contrast confirms the predicted direction (either
  direction publishable) **and** the dense arm is estimated with a CI (no NI test at `n=500` —
  underpowered for 5 pp) **and** the VoI bound is reported.
- **Effort:** medium; model-download approval has lead time — request it in Phase 7.

### Phase 9 — 🔬 optional · Pick at most one (0–2 GPU-h)

- **D3 token-level attribution** (0 GPU-h if timestamps kept): prefill vs decode per `k`,
  `J/prefill-token` constancy — upgrades H1 to a hardware-grounded model. **Do this first.**
- **D2 abstention-aware policy** (1–2 h) only if the router is retained; the abstention prize
  (28.64% vs 7.21%) is the only headroom that can pay for itself.
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
| **G7** | 7 | Per-depth factors identified (or bias model tested); estimators agree within tolerance; known-load check | Keep range as primary energy result |
| **G8** | 8 | Prereg frozen; causal contrast confirms direction; dense estimated with CI; VoI bound reported | Headline contribution |
| **G10** | 10 | 15–18 pp; traceability; clean-room repro; v0.3.0 DOI + tag | Submit |

A gate may not be added, removed, or re-thresholded after seeing the primary outcome. New studies
get new preregs; amendments go in `prereg/amendments.md` + `docs/DECISIONS.md`.

---

## 5b. Q1 acceptance outlook (reviewer judgment, not data)

| Stage completed | Paper becomes | Est. Q1 chance |
|---|---|---:|
| Now | Rigorous null + provisional joules | ~10% |
| + Phase 6 | Statistically clean negative + mechanism | ~25–30% |
| + Phase 7 | Joules you can defend or bound | ~35–40% |
| + Phase 8 | "Depth has a knee" with a causal control | ~45–55% |
| + Phase 10 | Full paper + artifact | ~50–60% |

Reading: Phase 6 is the best credibility per hour (free). Phase 8 is the biggest single jump
(~35% → ~50%). The residual ceiling is scope — one confirmatory corpus, one retriever family, one
laptop class — which no phase removes; only a second corpus or second hardware class would, and
both are outside budget. If Phase 8's causal contrast comes back flat or inverted, the fallback is
a measurement/reproducibility venue or a short paper, not a tuned positive.

---

## 6. Budget and schedule

| Item | Cost | Notes |
|---|---|---|
| GPU compute (Phases 7–9) | **$0** | Local RTX 3060 6 GB, batch 1, single job; **~11–17 GPU-h** new work |
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

1. `prereg/qc_prereg.md` (+ freeze tag) before any Phase 8 outcome.
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
- Router as the acceptance gate (VoI arithmetic says it cannot pay for its probe).
- H200 energy via MIG (`power.draw = N/A`); 32k CPU-offload; raw-text redistribution.

---

## 9. Change control (binding)

1. `prereg/PREREGISTRATION.md` + `analysis_plan.md` stay frozen at `prereg-freeze-v1`; deviations →
   `prereg/amendments.md` (date, original, replacement, reason, outcome-seen?) + `docs/DECISIONS.md`.
2. New-data phases require a **new** frozen prereg + tag before outcomes are read.
3. Gate re-thresholding after seeing an outcome is forbidden — including the `0.8 → 0.6` change.
4. Secret scan + `git status` before any data/config commit; `pytest -q`, `validate`,
   `ruff format` + `ruff check` green before any paper-affecting commit.
