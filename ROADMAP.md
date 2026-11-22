# Roadmap — Energy-Optimal Retrieval Depth → Q1 Hardening

**Status:** P0–P6 COMPLETE · Q1 audit COMPLETE (3 reviewers, 2026-11-22) · entering Q1-hardening · last updated 2026-11-22
**Horizon:** Q1-hardening, 6–10 weeks · local RTX 3060 6 GB + optional H200 `1g.18gb` accuracy-only slice · ≤ $47 cash (unchanged)
**Repository:** https://github.com/Atik203/energy-optimal-rag
**Paper:** `paper/main.tex` (30 pp, single file, 8 figs, 650 DPI) + `paper/out/main.pdf` · DOI `10.5281/zenodo.24352803` · tag `v0.2.1` behind `main` (`328811e`)

**Legend:** ✅ done · ❌ gate fired (= finding, reported not tuned away) · 📋 todo (planned, not started) · ⏳ in progress · 🔬 optional (pick ≤1) · ⏸️ blocked (needs approval/hardware). Phases 6–10 continue P0–P5; each phase ends at its G-gate.

This roadmap compresses finished work (§1) and specifies the new Q1 program (§3–§5) in
agent-executable detail. Gates are allowed to fire. A fired gate is a finding and must be
reported, not tuned away. Prereg discipline (§7) still binds.

---

## 1. Completed work (compressed — do not redo)

| Phase | Status | Result (one line; details in `docs/P*_RESULTS.md`) |
|---|---|---|
| Pilot (200 q × 7 k) | ✅ | Signal only: 2 pp dead (`P(k*)=0.61`); 5 pp uncertified (`k=4`, 69.3%) |
| P0 golden | ❌ | Calibration FAIL (`k=0` 0.7944 < 0.80); sweep uncalibrated |
| P1 (1,000 q × 7 k) | ❌ | 5 pp NOT supported: `-4.30 pp`, lower `-6.17`, `p=0.2691`; savings `58.17%`; K3/K5/G1/G2 fail |
| P2 arms + probes | ✅ | H7 split (Qwen1.5B `+2.00` fail / HotpotQA `-10.80` pass); boundary/16k null; all energy uncalibrated |
| P3 policy | ❌ | G4 fail: capture `-2.48%`, AUC `0.733`; matched oracle `28.64%` |
| P4 + sims | ✅ | Coverage rejected 3/4; `R×Q` mechanism (0.015–0.024 vs 0.062–0.149); 5 pp needs ~7.1k pairs |
| Metrology (D-028) | ✅ | Per-query NVML seq-dependent; P1 `J` provisional, P2 range-only |
| Paper + release | ⏳ | 30 pp + 8 figs; repro + backup done; release pending — owned by Phase 10 |

Rule: no new run re-thresholds P0–P4 gates. New data needs a **new prereg**; old runs are never patched.

---

## 2. Claim boundary (post-audit — binding on all agents)

**What survives as a publishable core (calibration-free):**
- Paired accuracy cost on P1: `−4.30 pp`, two-sided 95% CI `[−6.53,−2.07]`, McNemar `p=0.0002` (superiority-pass, not NI-fail, framing).
- Qualitative savings floor: >20% under *both* sweep and block estimators on every arm (point 58.17% is provisional).
- Mechanism `A=R·Q`: two-stage RMSE `0.015–0.024` vs one-stage `0.062–0.149` on all 4 arms; explains SQuAD plateau, Llama peak, P3 failure (BM25 predicts `R`, not `Q`).
- P3 negative is a proper ML negative (AUC `0.733` flat 50→608 q; presence-oracle `47.8%` vs 50% gate).
- Metrology negative: per-query NVML windows falsified on this laptop class (citable).

**What may NOT be claimed (until the hardening phases pass):**
- No absolute `J`, `E`, `N*` (=6,189 descriptive only), `S(k)`, or affine intercept `a=24.08` as results — demote to diagnostic/range.
- No "5 pp certified", no universal `k*`, no 2 pp rule (dead), no adaptive-policy gain, no coverage-theory prediction.
- No pooling SQuAD `A(4)−A(32)` with HotpotQA `A(4)−A(10)`; HotpotQA is **transport**, not replication.
- No energy claim from H200/MIG slice (accuracy-only by construction), 16k probe (allocation-only), or any uncalibrated arm.
- No `P(k* optimal) ≥ 0.8` gate (S3 says unattainable at `n=1,000`; max K3-pass 0.155).

---

## 3. Q1 audit verdict (why this is not yet Q1 — 7 blocks)

Derived from 3 parallel reviewers (methods / measurement / contribution). Each block lists
severity and the phase that fixes it.

1. **B1 FATAL — energy construct falsified.** Sequence dependence + sweep/block gap (Qwen `k=0` 19.7 vs 5.1 J/q) + P1 `k=0` 1.1% above floor + intercept +53% pilot→P1. Breaks H1/H4/savings-point/`N*`/taxes. → fixes in Phase 6, Phase 7.
2. **B2 FATAL/MAJOR — power misspecification.** Plan assumed discordance 0.08; observed 0.131; realized power 0.152; 80% power needs ~16.3k pairs (~7.1k at 50%). `n=1,000` "comfortably powered for 5 pp" is a design miss. → Phase 6 reframe + Phase 10 new-study design.
3. **B3 MAJOR — H7 disjunctive replication.** "1.5B **or** HotpotQA" with shifted reference (`k=10` vs `32`), different task shape, sign split (+2.00 vs −10.80 pp). A-001 direction rule set after P1 sign known. 7 hypotheses + 12 gates adjudicated with "one primary test, no correction". → Phase 6 relabel + gatekeeping.
4. **B4 MAJOR — post-selection inference ignored.** `k*` selected and evaluated on same data; S3 winner's curse −0.6–3.4 J/correct, `N*` biased −20% at `n=200`; scoring flips EM `k=4` ↔ lenient/F1 `k=8`. → Phase 6 split-sample + S3-calibrated stability.
5. **B5 MAJOR — sensor + calibration fragility.** 100 ms cadence on ~1 Hz sensor; Qwen intercept −8.32 (impossible), CV 80.15%; P0 bimodal 0.732/1.676; repeats only at `k=8`. → Phase 7 repeats + refit w/o `k=0`.
6. **B6 MAJOR — no wall meter / proxy / bookkeeping.** D-016 waiver stands; CPU `20 W×t` unvalidated; P0 manifest lacks driver; throttling 88–90 °C, 1003→900 MHz under-reported. → Phase 7 meter + manifests + traces.
7. **B7 HIGH — contribution is null without replacement.** G1/G2/K3/K5/G4 fail; survivors H1/H4 are `O(n)`-expected; P3 strawman (no Adaptive-RAG/Self-RAG/FLARE/IRCoT baseline, no reader-confidence feature); single BM25/SQuAD/Q4-reader scope; theory (Thm.1–3) is statics + rejected coverage; 30-pp lab-notebook arc. → Phase 8 (reader-aware router + dense arm) + Phase 6 (Pareto/cost reframe) + Phase 10 rewrite.

Minimum resubmission without new GPU: demote absolute-J to ranges, relabel transport,
replace 0.8 gate, lead with superiority cost + `R×Q` + measurement audit, retitle away from
"Energy-Optimal" (see Phase 6).

---

## 4. Q1 hardening phases 6–10 (agent-executable)

Conventions for every phase: read `AGENTS.md` first; seeds from config, never literals;
joules in J, accuracy in [0,1], depths integers; `pytest -q`, `validate`, `ruff format/check`
before commit; every number traces to `runs/<run_id>/raw.csv` or registered analysis;
never commit raw text, weights, secrets, or `runs/<run_id>/` data (registry row only).
Numbering continues P0–P5: Phase 6 = reframe, 7 = measurement, 8 = contribution, 9 = optional scaling, 10 = paper + release. Each phase lists goal, hypothesis, inputs, steps, outputs, and acceptance so any agent or teammate can execute it.

### Phase 6 — 📋 todo · Honesty reframe + inference repair (CPU-only, 0 GPU-h) — DO FIRST

- **Goal:** make the paper reviewer-proof without new data; convert F2/F3/F4 + B7-presentation into a clean negative + mechanism story.
- **Hypotheses:** (H-cost, superiority, pre-registered as re-analysis): `A(4)−A(32) < 0` on P1 (already `p=0.0002`); (H-het): depth effect is reader×task-conditional (P1 −4.30 vs 1.5B +2.00 vs HotpotQA −10.80 vs Llama peak-at-4).
- **Inputs to read:** `analysis/squad_qwen4b_p1/noninferiority.json`, `bootstrap.json`, `analysis/recall_precision.json`, `analysis/inference/p1.json`, `analysis/simulations/s3.json`, `paper/main.tex` §§ Results/Limitations.
- **Steps:**
  1. Energy language sweep in `paper/main.tex`: every abstract/results/conclusion absolute `J/E/N*/S(k)/a` → "diagnostic, uncalibrated range (sweep X–block Y)"; keep point + CI exactly once with "provisional" qualifier; move `N*=6,189 [5,697,6,748]` + `β=1.164` derivation to footnote.
  2. Refit affine **excluding `k=0`** from registered `estimates.csv`; report slope `b` as range (sweep vs block), drop intercept-dependent claims; publish per-depth consistency + neighbour-dependence table (P1 +24%, Qwen +48%, HotpotQA +22%, Llama +82%) in main text.
  3. Inference repair: split-sample plan — select `k*` on half, estimate savings/`N*` on held-out half (or Bonferroni/Holm over 7 depths); replace `P≥0.8` with S3-calibrated criterion (modal depth + span; threshold ≥0.6 justified from `s3.json`); report model-averaged savings over feasible set alongside argmin.
  4. Relabel: HotpotQA "`transportability`" (own margin, never pooled); H-hierarchy — H2 primary, H1/H3/H4 descriptive, H7 conjunctive-or-split-α (Holm); scoring hierarchy EM primary with order-preservation requirement (not "never 32").
  5. Pareto reframing (no GPU): promote existing frontier to a decision tool — `k*(δ), Sav(δ), n_req(δ), N*(δ)` + $/CO₂ conversion table; headline becomes "given margin δ and volume V, pick k" instead of binary 5 pp pass/fail.
- **Outputs:** edited `paper/main.tex` + `tools/paper/scripts/` change (if any figure text changes) + `docs/DECISIONS.md` entry + `prereg/amendments.md` entry (re-analysis, no outcome-data change to gates).
- **Acceptance:** `make_figures.py --check` passes; `verify_main.py` (labels/refs/bib) clean; no absolute-J claim without "range/provisional"; 420 tests pass.
- **Effort:** small, CPU-only.

### Phase 7 — 📋 todo · Measurement hardening (3–6 GPU-h local) — DO SECOND

- **Goal:** replace two-biased-estimators with one approximately unbiased estimator + bound the system gap (fixes B1/B5/B6).
- **Hypotheses:** (H-replay): replay-sequence block factor calibrates the *contrast* (sweep/block/replay triple converges); (H-cv): per-depth CV is worst at `k∈{0,1}` and acceptable at `k≥4`.
- **Inputs:** `docs/MEASUREMENT.md`, `docs/MEASUREMENT_VALIDITY.md`, `runs/squad_qwen4b_p1/{blocks,repeat,manifest}.json`, `tools/paper/scripts/make_figures.py`.
- **Steps (new run IDs, new prereg — never patch P1):**
  1. **B1 sequence-matched calibration (2–3 GPU-h):** replay P1's exact permutation as one continuous block; calibration factor = replay/block ratio; re-derive savings as sweep/block/replay triple. New config in `configs/`, new `runs/<run_id>/`, registry row, `validate` clean.
  2. **B2 repeats (1–2 GPU-h):** `k ∈ {0,1,4,32}`, 5 blocks each, cooldown at block start; report full CV distributions (not median/max only); stop fitting affine through degenerate `k=0` (1/1,000 correct, `n_inf`=3802/10,000).
  3. **B3 wall meter (∼1 GPU-h + ∼$25):** full-condition (not 30-query subset) Kill-A-Watt-class run; report `system_J/(GPU_J+CPU_proxy)` descriptively; CPU 10/15/20 W bands in every energy table.
  4. **Bookkeeping (0 GPU-h):** driver/CUDA/power-mode/clocks/Ollama digest in *every* manifest; publish throttle-fraction traces, clock-vs-J scatter, drop-first-50 + pre/post-idle numerically; amend registry (D-016 follow-up).
- **Outputs:** new `runs/<replay_id>/`, `runs/<repeat_id>/`, `analysis/measurement_hardening/` JSON+report, updated validity fig, `docs/DECISIONS.md` entry.
- **Acceptance:** replay factor finite; per-depth CV table complete; wall factor reported (not used to rescale P1); block-gate rule pre-specified before seeing outcomes.
- **Effort:** medium; single GPU, batch 1, no concurrent jobs; stay in project space (200 GB, `df -h` check).

### Phase 8 — 📋 todo · From mechanism to contribution (medium GPU) — THE Q1 BET

- **Goal:** turn descriptive `R×Q` into a predictive, generalizable contribution (fixes B7-core + B4-theory).
- **C1 — Reader-aware difficulty router (highest leverage, ∼2–4 GPU-h).**
  - Hypothesis (H-Q): `Q(k)` decline is predictable from **reader-side** uncertainty, not BM25. Features: `p(correct|k=0)`, answer entropy / length-norm perplexity, BM25-gap × confidence interaction. BM25-only is the null.
  - Method: reuse P1 7k rows + add **0-passage confidence probe** (no new sweep); train on fresh split only (never P3 test IDs — P3 used hashed 608/206/186; new split required, see `docs/P3_RESULTS.md`); target: capture >30–50% of the **non-abstention** matched gap (7.21%, since 28.64%→7.21% without abstention) where BM25 got <0%.
  - Baselines required: Adaptive-RAG / Self-RAG / FLARE / IRCoT-style policy or explicit justification + static `k=1/4/32`; report AUC, learning curve (50→608), answer-presence oracle vs 50% gate.
  - Acceptance: held-out capture ≥30% at matched accuracy **or** documented negative with flat learning curve (publishable either way); features predicting `Q` ablation shown.
- **C2 — Dense-retriever transport arm (∼1–2 GPU-h + model-download approval).**
  - Hypothesis (H-dense): precision collapse is BM25-rank artifact; dense (BGE/DPR) + reranker restores monotonicity or shifts plateau. Same reader, same `k` grid, same NI/superiority test, `n=500–1,000` on same IDs.
  - Either outcome is Q1-informative (retrieval-quality vs reader-overload). Report `R(k)/Q(k)` curves alongside accuracy.
  - Out-of-scope lift: no dense *training*, inference-only; ask user before downloading weights (AGENTS.md §2/§10).
- **Outputs:** `configs/qc_*`, `runs/<qc_router_id>/`, `runs/<qc_dense_id>/`, `analysis/qc_router/`, `analysis/qc_dense/`, `artifacts/claims_evidence.csv` new rows (C-new IDs), `artifacts/ledger.csv` rows.
- **Effort:** medium; needs new prereg (`prereg/qc_prereg.md` + freeze tag) before any outcome is read.

### Phase 9 — 🔬 optional · Scaling / abstention / attribution (pick ≤1 before Phase 10)

- **D1 Reader-strength scaling law (high reward, ∼2–4 GPU-h):** sweep `0.5B/1.5B/4B/7B` at `n=300–500`; test `k_peak` vs size / `Q`-slope `γ` (hint: Llama peaks `k=4`, Qwen4B monotone, 1.5B flat). If `γ` scales inversely with capability → new regularity.
- **D2 Abstention-aware joint policy (∼1–2 GPU-h):** selective prediction (abstain at low confidence) + depth routing; compare vs depth-only; makes the 28.64%→7.21% decomposition an honest lever.
- **D3 Token-level attribution (0 GPU-h if timestamps kept):** prefill-vs-decode split per `k`, `J/prefill-token` constancy; upgrades H1 to hardware-grounded model.
- **Rule:** do NOT pursue 5 pp re-certification alone (~7–16k pairs, 15–60 GPU-h, exceeds budget, still single-condition null-prone), H200 accuracy-only expansion, more BM25 features, or more simulations.

### Phase 10 — 📋 todo · Q1 paper rewrite + submission + release (CPU-only + buffer)

- **Goal:** 18–22 pp + refs arc (from lab notebook to argument): *depth trades recall gains against reader-precision losses; the product plateaus while joules rise linearly — so static depth cannot win at fixed margin, and only reader-aware routing can.*
- **Keep (spine):** abstract negative + Fig P1 `A/J/E` + contrasts/selection + sensitivity (k=32 never selected) + `R×Q` + P3 1-para + HotpotQA/1.5B contrast + sweep box + window-bias fig + slim claim map (8 rows).
- **Cut/compress:** P0 forensics → 3 sentences; gate alphabet soup → G1/G4 only; S1–S3 + `sim_ratio` → 1 para; `k*=1.214` → footnote/drop; taxes → 2 sentences; boundary/16k → 2 sentences each; checklist/notation/N*-derivation/pilot table → compress (see contribution review §3).
- **New title direction:** away from "Energy-Optimal" toward cost + mechanism (e.g. *The Cost of Depth…*); retitle decided at submission prereg.
- **Acceptance:** every number traces to `raw.csv`/registered output; 0 undefined refs; all figs ≥600 DPI; `docs/paper/README.md` Overleaf steps verified; clean-room repro matches; Zenodo new version + tag.
- **Release checklist (pending — the unfinished work):** 1) Overleaf compile of `paper/main.tex` matches `paper/out/main.pdf`; 2) clean-room repro from `git archive` + raw-data copy passes; 3) secret scan + `git status` clean of raw text/weights/secrets; 4) publish new Zenodo version (current DOI `10.5281/zenodo.24352803` is v0.2.1, behind `main`); 5) tag release and push; 6) verify `docs/BACKUP.md` checksums.

---

## 5. Gates (G6–G10 exit gates; old K/G frozen as history)

| Gate | Phase exit | Criterion | Pass action |
|---|---|---|---|
| **G6** | Phase 6 | Paper honest: absolute-J demoted to ranges, HotpotQA labeled transport, S3-calibrated stability, Pareto tool in | Enter Phase 7; else revise text, do not relax |
| **G7** | Phase 7 | Replay-calibrated savings range clears 20% floor with pre-specified estimator | Keep range as primary energy result; else stay qualitative |
| **G8** | Phase 8 | Router captures ≥30% of non-abstention matched gap on held-out split, and/or dense arm completes with `R/Q` curves + same-reader test | Headline contribution / transport claim; else report negatives + heterogeneity finding |
| **G10** | Phase 10 | Paper meets keep/cut + traceability + DPI + clean-room repro; Zenodo new version + tag pushed | Submit; else revise, do not relax gates |

A gate may not be added/removed/re-thresholded after seeing the primary outcome. New studies get new preregs; amendments go in `prereg/amendments.md` + `docs/DECISIONS.md`.


---

## 5b. Q1 acceptance outlook (reviewer judgment, not data)

Rough, honest estimates of top-Q1 full-article acceptance at each stage.
These are judgments from the 3-reviewer audit, not measured probabilities.

| Stage completed | Paper one-liner | Est. Q1 chance | Why |
|---|---|---:|---|
| Now (negatives + mechanism, provisional J) | Rigorous null report | ~10% | B1/B5/B6 measurement blocks are fatal for absolute-J claims; B7 contribution is null-without-replacement |
| + Phase 6 reframe (ranges, transport label, Pareto tool) | Honest negative + decision tool | ~25% | Reviewer-proof on inference; still no positive deployable result |
| + Phase 7 hardening (replay estimator + wall meter) | Credible metrology + bounded savings | ~35% | Numbers trustworthy, but contribution still a negative |
| + Phase 8 router (C1 hits >=30% held-out capture) | Reader-aware routing that beats BM25 | ~55-65% | Positive, generalizable, mechanism-tested: genuine Q1 contribution |
| + Phase 8 dense arm (C2) | Retrieval-quality vs reader-overload settled | ~65-75% | Two transport axes; hard to reject on scope |
| + Phase 9 pick-one (scaling law or abstention win) | New regularity | ~75%+ | Second positive finding; strong Q1 case |

Reading: Phase 6 + Phase 7 are necessary but not sufficient — they remove
rejection reasons without adding an acceptance reason. Phase 8 is the
acceptance reason. Without Phase 8 (or Phase 9), the right target is a
reproducibility/measurement venue or a 10-page short paper, not a top-Q1
full article (per contribution review).

---

## 6. Budget and schedule

| Item | Cost | Notes |
|---|---|---|
| GPU compute (Phase 7–Phase 9) | **$0** | Local RTX 3060 6 GB, batch 1, single job; est. 8–15 GPU-h new work (Phase 7 3–6, Phase 8 3–6, Phase 9 optional 2–4) |
| Electricity | **~$2** | Indicative, not metered billing |
| Wall meter | **$25** | Full-condition cross-check (Q-B3); replaces 30-query-subset plan |
| Backup USB | **$10** | Already held; verify `docs/BACKUP.md` checksums before new runs |
| Contingency | **$10** | Fan/SSD; hard cap **≤ $47** unchanged |
| Storage | 0 | Stay in project space; `df -h`/`du -sh` before runs; 200 GB quota; never touch other users' files |
| H200 slice | $0 | Accuracy-only, `1g.18gb` max, SSH via `uiu-h200` only; **no energy claim**; record driver 580.178.04 / CUDA 13.5; no env changes without approval |

Order: **Phase 6 (now, 0 GPU-h) → Phase 7 → Phase 8 → Phase 9 (pick ≤1) → Phase 10.** Do not start Phase 8 training on P3 test IDs. Do not download weights / use paid APIs / write outside `E:\PROJECT\energy-optimal-rag` without asking.

---

## 7. Deliverables (additive to §1)

1. `prereg/qc_prereg.md` (+ freeze tag) for every new-data phase; analysis records prereg + config hashes.
2. `runs/<new_id>/raw.csv` + registry rows + `analysis/<phase>/` JSON/reports for Phases 7/8(/9).
3. Updated `paper/main.tex` + `paper/figures/` (all ≥600 DPI) + `paper/out/main.pdf` via Overleaf `main.tex`-as-root flow.
4. Extended `artifacts/claims_evidence.csv` (new C-IDs) + `artifacts/ledger.csv` rows.
5. `docs/DECISIONS.md` entries for every hardware/env/estimator change before confirmatory work.
6. New Zenodo version + tag **only** from clean `main` after clean-room repro.

---

## 8. Out of scope (unchanged + Q1 clarifications)

- Universal `k*`; frontier/API readers; dense-retriever *training*; multi-GPU/datacenter energy; carbon-optimal beyond constant-factor; prompt/fine-tune/reranker-training as primary; production/SLO study.
- 5 pp re-certification at ~7–16k pairs as the *sole* Q1 bet (cost exceeds budget, still null-prone).
- H200 energy via MIG/`power.draw=N/A`; 32k CPU-offload condition; raw-text redistribution (CC BY-SA 4.0 — IDs/predictions/checksums only).

---

## 9. Change control (binding)

1. `prereg/PREREGISTRATION.md` + `analysis_plan.md` stay frozen at `prereg-freeze-v1`; any deviation → `prereg/amendments.md` (date, original, replacement, reason, outcome-seen?) + `docs/DECISIONS.md`.
2. New-data phases (Phases 7/8/9) require a **new** frozen prereg + tag *before* outcomes are read; re-analysis (Phase 6) is labeled re-analysis.
3. Secret scan + `git status` before any data/config commit; `pytest -q`, `rag_energy.cli validate`, `ruff format` + `ruff check` green before any paper-affecting commit.
