# Roadmap — Energy-Optimal Retrieval Depth (G2)

**Status:** post-pilot MARGINAL · initial public scaffold · last updated 2026-11-11
**Horizon:** 20 weeks · 3–4 people · local RTX 3060 6 GB only · ≤ $47 cash
**Repository:** https://github.com/Atik203/energy-optimal-rag

This roadmap is a working plan, not a promise of results. Gates are allowed to fire. A
fired gate is a finding and must be reported, not tuned away.

---

## 1. Claim boundary

### 1.1 What the pilot established

The pilot ran 200 SQuAD v1.1 dev questions × 7 depths (`k ∈ {0,1,2,4,8,16,32}`), 1,400
generations, on an RTX 3060 Laptop 6 GB with Ollama `qwen3.5:4b` (Q4) and BM25 top-32.

| Quantity | Pilot value |
|---|---|
| Energy per correct answer | `E(32) = 157.1` vs `E(1) = 45.5` J/correct → **3.45×** |
| Affine energy fit | `J(k) = 15.74 + 2.283k` J, `R² = 0.9990` |
| Accuracy | `A_EM` 0.395 (`k=1`) → 0.570 (`k=32`); flat **0.520–0.535** for `k = 4–16` |
| Context-side energy share | 36.3% (`k=2`) → **85.1%** (`k=32`) |
| Retrieval-only share (BM25 CPU proxy) | 3.5% (`k=32`) – 17.3% (`k=1`) |
| Optimal-depth identity | holds at `k=2`: gap **+0.044**, CI [−0.050, +0.128]; fails at `k=32`: **+0.700** |
| Repeat CV (`k=8`) | median **3.80%**, max **9.24%** |
| Static 2 pp claim | `k* = 32` boundary, bootstrap `P(k* optimal) = 0.61 < 0.8` → **DEAD** |
| 5 pp margin (pilot signal, not certified) | `k = 4`, **69.3%** savings, `N* = 876` queries; proposal reports `P = .537` for the 5 pp selection |
| Adaptive oracle | **78.8%** gain at matched accuracy — upper bound, no learned policy |

### 1.2 What may be claimed now

- The energy-depth tradeoff is real and steep under the pilot conditions.
- The affine energy model and the context-side share are measurable and stable.
- The identity is a useful diagnostic at an interior optimum and correctly flags
  over-retrieval at high `k`.
- At a **5 pp** EM margin, the pilot selected `k = 4` with **69.3%** savings and `N* = 876`.
  This is a **pilot signal, not certified**: the proposal reports `P = .537` for the 5 pp
  selection, below the G2 threshold of 0.8, and no pilot non-inferiority test is reported. The
  rerun must report the non-inferiority test and the selection probability separately.
- Query-conditional depth is a promising direction; the 78.8% figure is an oracle upper
  bound, not a policy result.

### 1.3 What may not be claimed

- No universal `k*` across datasets, readers, retrievers, or hardware.
- No "2 pp optimal" depth. The 2 pp margin is dead as a decision rule at the current power.
- No "5 pp certified" result before the powered rerun.
- No learned-policy gain until a policy is trained and evaluated on held-out questions.
- No carbon-optimal claim beyond constant-factor reporting.
- No generalization to frontier readers, dense retrievers, or full NQ from this design.

---

## 2. Phases

| Phase | Weeks | Goal | Key outputs | Exit gate |
|---|---|---|---|---|
| **P0** | 1 | Scaffold and golden reproduction | Repo, CI green, environment lock, data manifest, 200-question golden reproduction of the pilot curve, measurement harness checks | Golden `E(k)` within 10% of pilot at each depth; K7 passes; `validate` clean |
| **P1** | 2–3 | Powered SQuAD rerun | `n = 1,000` × 7 depths, frozen prereg, raw ledger, primary 5 pp non-inferiority analysis | G1 or documented failure; K1–K7 adjudicated; freeze respected |
| **P2** | 4–6 | External validity and causal test | Qwen2.5-1.5B replication (`n = 500`), HotpotQA distractor (`n = 500`, `k ≤ 10`), 16k boundary probe (`k ∈ {32,48,64}`, `n = 200`), fixed/per-passage energy taxes | G5 replication; tax signs match Corollary 1; boundary probe resolves |
| **P3** | 7–10 | Query-conditional policy | Feature set, policy model, 600/200/200 split, matched-accuracy evaluation, oracle gap capture | G4: oracle gain ≥20% and policy captures ≥50% at matched accuracy, or documented negative |
| **P4** | 11–14 | Theory validation and sensitivity | Identity tests across datasets/readers, certification-cost curves, margin sensitivity, distractor counterexample check, robustness to scoring rule | Theory report; identity and comparative statics either supported or revised |
| **P5** | 15–18 | Paper | Manuscript draft, supplement, figures, tables, claims-evidence map | Internal review; every number traces to `runs/<run_id>/raw.csv` |
| **P6** | 19–20 | Buffer and release | Camera-ready fixes, reproducibility package, Zenodo DOI, data card, release tag | Clean-room reproduction on a second machine; archive deposited |

### Phase detail

**P0 — Scaffold and golden reproduction (week 1).** Build the repository, CI, environment
lock, config schema, CLI validation, and the measurement harness. Re-run a 200-question
SQuAD subset on the same reader and compare the curve to the pilot. The purpose is to prove
the harness, not to produce new evidence. If the golden reproduction differs by more than
10% at any depth, stop and diagnose before P1.

**P1 — Powered SQuAD (weeks 2–3).** Freeze the preregistration before looking at the new
accuracy data. Run `n = 1,000` at 7 depths. Primary test: 5 pp EM non-inferiority at the
pre-specified interior depth (`k = 4` vs `k = 32`), with ≥20% energy savings required for a
positive policy claim. The 2 pp margin is estimated and reported with a CI but is not a
certification target. This phase decides whether the paper has a static policy result.

**P2 — Replication and causal test (weeks 4–6).** Three independent stresses: a weaker
reader (Qwen2.5-1.5B-Instruct, `n = 500`), a multi-hop/distractor dataset (HotpotQA,
`n = 500`, `k ∈ {0,1,2,4,8,10}` because the distractor setting supplies 10 paragraphs), and
a boundary probe (`k ∈ {32,48,64}`, `n = 200`) to test whether the pilot's boundary optimum
was a grid artifact. The probe also includes a 16k-token context check to test whether the
boundary is a 4096-context artifact; if the 6 GB card cannot hold 16k, the limit is reported
rather than dropped. Add the energy-tax manipulation: a fixed dummy GPU computation raising
`a` by 10–30% and a per-passage dummy computation raising `b` by 10–30%, with the prediction
that `k*` increases for the fixed tax and decreases for the per-passage tax.

**P3 — Query-conditional policy (weeks 7–10).** The static population optimum is the wrong
object if queries are heterogeneous. Build features from BM25 scores (top score, score gap,
score entropy), question type, length, and retrieval recall proxies. Train a simple policy
(logistic/decision tree or cost-sensitive classifier) on a 600-question target training split,
tune on 200 validation questions, and evaluate once on 200 held-out questions. The 600/200/200
split is a target: hashed per-question assignment can produce slightly different realized
counts, which are reported. There is no test-set tuning. Evaluate at matched accuracy against
the best static `k`, and report the fraction of the oracle gap captured. The oracle is an
upper bound; the learned policy is the result.

**P4 — Theory validation and sensitivity (weeks 11–14).** Test the identity across datasets
and readers. Fit the coverage model and report its failure where it fails. Map the
certification-cost curve `N*` and its sensitivity to the margin. Stress the distractor
counterexample: if `A(k)` is non-monotone, a greedy policy stops at a local optimum. Report
margin sensitivity (2, 3, 4, 5, 6, 8, 10 pp) and scoring sensitivity (strict EM, lenient span
match, F1 ≥ 0.5). Conclusions must not depend on a single scoring rule.

**P5 — Paper (weeks 15–18).** Write the paper as a decision-theory + causal-measurement
paper, not a curve paper. The headline is the margin-indexed policy result and the
certification decision, with the failed 2 pp claim reported in the results. Every table and
figure is generated by a script from a registered run.

**P6 — Buffer and release (weeks 19–20).** Re-run the full analysis from raw CSVs in a clean
environment, verify checksums, deposit the reproducibility package (Zenodo), and tag the
release. The paper is not submitted until the clean-room reproduction matches.

---

## 3. First 10-day sprint

| Day | Task | Output | Acceptance check |
|---:|---|---|---|
| 1 | Repository scaffold, CI, governance files | Public repo, green CI (or documented CI failure) | `pytest -q` passes locally and in CI |
| 2 | Environment lock, CLI validation, config schema | `environment.yml`, lock template, `rag_energy.cli validate` | All TOML configs parse; `validate` exits 0 |
| 3 | Data prep: SQuAD dev download, 70-word chunking, BM25 index | `data/manifest.json` populated, processed parquet (git-ignored) | 1,000 questions and ≥45k passages; recall@32 reproducible |
| 4 | Energy harness validation: NVML, idle, block calibration, nonce | Harness test report | Idle CV < 20%; block factors recorded; nonce forces full prefill |
| 5 | Golden reproduction: 200 questions × 7 depths | `runs/golden_*/raw.csv` | `E(k)` within 10% of pilot at every depth; repeat CV < 20% |
| 6 | Freeze preregistration and configs | Signed prereg commit, `configs/analysis/prereg.toml` | Prereg hash recorded; no analysis code reads outcomes before freeze |
| 7 | Power simulation and sample-size lock | Power table, decision memo | `n = 1,000` justified for 5 pp; 2 pp declared estimation-only |
| 8 | Run P1 primary sweep (first half) | Raw CSV, registry entry | No sampler errors; thermal log complete |
| 9 | Run P1 primary sweep (second half) and QA | Complete `n = 1,000` run | All depths present; exclusions documented |
| 10 | Gate review K1–K7 and G1–G5 | Gate memo, go/no-go for P2 | Decision recorded in `docs/DECISIONS.md`; no post-hoc gate changes |

Days 8–9 may slip if the 3060 must be shared. The sprint buffer is day 10; the phase buffer
is P6.

---

## 4. Gates

Gates are evaluated once per phase on the pre-specified analysis population. Any change to a
gate after the freeze is an amendment and must be logged.

### 4.1 Kill / reframe gates (K1–K7, adapted from the brief)

| Gate | Criterion | Pilot result | Rerun action if it fires |
|---|---|---|---|
| **K1** | Relative energy effect <10% | **PASS** (245% effect) | If it fires on the rerun, stop the depth story; report the null |
| **K2** | `k*` at boundary `{0, K_max}` | **FAIL** (`k* = 32`) | Extend grid once (16k probe); if still boundary, reframe as "don't over-retrieve" |
| **K3** | `P(k* optimal) < 0.8` | **FAIL** (0.61) | Increase `n`/repeats once; if it persists, drop static certification |
| **K4** | Context share <5% and flat | **PASS** (36–85%) | If it fires, the lever is generation, not depth; reframe |
| **K5** | `k*` spans >1 depth across bootstrap/datasets | **FAIL** (span 3 gated) | Pivot to query-conditional policy; do not claim a population `k*` |
| **K6** | Oracle gain <15% | **PASS** (78.8%) | If it fires on held-out policy evaluation, kill the adaptive component |
| **K7** | Repeat CV >20% or MDE > observed effect | **PASS** (3.80% median) | Fix measurement (more repeats, wall meter); do not interpret the curve |

K1–K4 and K6 firing is a kill/reframe. K5 and K7 are fixable measurement or framing problems
before they are kills.

### 4.2 Go gates (G1–G5, adapted to the post-pilot claim)

| Gate | Criterion |
|---|---|
| **G1** | 5 pp non-inferiority at an **interior** `k`, with **≥20%** energy savings vs `k = 32` |
| **G2** | Upper confidence bound on the accuracy loss **≤5 pp**, and bootstrap `P(k* optimal) ≥ 0.8` for the 5 pp selection |
| **G3** | Context-side share at the selected `k` in **[0.10, 0.70]**, and the share varies with `k` |
| **G4** | Oracle gain **≥20%**, and a learned policy captures **≥50%** of it at matched accuracy |
| **G5** | Replication on the 1.5B reader **or** HotpotQA |

G1 and G2 are the static-policy gates. G3 protects against a degenerate split. G4 is the
adaptive-policy gate. G5 is the external-validity gate. A paper may be written with G1, G3,
and G5 but without G4; it may not claim adaptivity without G4.

---

## 5. Budget

Local-only compute. No rental, no paid API, no cloud inference.

| Item | Cost | Notes |
|---|---:|---|
| GPU compute | **$0** | Local RTX 3060 Laptop 6 GB; 15–20 GPU-hours total across P0–P4 |
| Electricity | **~$2** | 15–20 GPU-h at ~100 W plus host overhead; indicative, not metered billing |
| Plug-in wall meter | **$25** | Cross-check on a 30-query subset per condition |
| USB backup drive | **$10** | Cold backup of raw runs, manifest, and checksums |
| Contingency | **$10** | Replacement fan/thermal paste or a spare SSD |
| **Total** | **≤ $47** | Hard cap |

**Storage:** ~5 GB on `E:` for raw data, processed parquet, run CSVs, and figures; model
weights stay in the existing Ollama store (3.3 GB) and are never copied into the repo. The
USB drive holds a second copy of `runs/`, `artifacts/`, and the manifest.

**Time:** 15–20 GPU-hours is the compute budget. Human time is the binding constraint:
3–4 people, 20 weeks, with P5 and P6 staffed for writing and release.

---

## 6. Deliverables

1. **Open harness (MIT):** installable `rag_energy` package, CLI, configs, and scripts.
2. **Frozen dataset IDs and manifest:** SQuAD v1.1 dev and HotpotQA distractor, with
   versions, licenses, and SHA-256 checksums in `data/manifest.json`.
3. **Raw energy ledger:** per-query CSV per run (`runs/<run_id>/raw.csv`) and the aggregated
   tracked ledger (`artifacts/ledger.csv`).
4. **Analysis scripts:** reproducible bootstrap, non-inferiority, identity, policy, and
   power calculations.
5. **Preregistration and amendments:** `prereg/PREREGISTRATION.md`, `analysis_plan.md`,
   `amendments.md`.
6. **Paper draft and supplement:** `paper/`, with every number mapped in
   `artifacts/claims_evidence.csv`.
7. **Reproducibility package:** environment lock, model digests, config hashes, data
   checksums, and a clean-room reproduction script; archived with a Zenodo DOI.
8. **Data card:** `docs/DATA_CARD.md`, covering provenance, sampling, licensing, and limits.
9. **Measurement protocol:** `docs/MEASUREMENT.md` and `docs/PROTOCOL.md`.
10. **Risk log:** `docs/RISKS.md`, reviewed at every phase gate.

---

## 7. Risks

| # | Risk | Why it matters | Mitigation |
|---|---|---|---|
| R1 | Strict EM vs lenient scoring | Strict EM drove the 2 pp failure; a string match may decide the green verdict | Pre-register EM primary, report lenient span and F1 ≥0.5 as sensitivity; conclusions must survive both |
| R2 | Reader strength / SQuAD saturation | A stronger reader could flatten the accuracy curve and move `k*` | 1.5B replication and HotpotQA; report reader-conditional results, no universal claim |
| R3 | Single corpus / single retriever | SQuAD closed corpus and BM25 limit external validity | HotpotQA distractor; report recall@k; state the boundary explicitly |
| R4 | Thermal throttling | Pilot clock fell 39% and temperature rose 16 °C | Randomize `k` within question, log clocks/temperature, block calibration at steady state |
| R5 | NVML coarse resolution | 100 ms samples are not 100 ms of independent information on this laptop | Block calibration, repeat CV, wall-meter cross-check, report sensor caveat |
| R6 | Ollama prefix cache | Reused KV prefixes confound depth with request order | Unique 10-hex nonce at the start of every request; verify prefill times |
| R7 | Energy noise | Small effects can be swamped | Idle subtraction, 20-query blocks, repeats, bootstrap, pre-registered MDE |
| R8 | Adaptive policy overfitting | 600/200/200 is small; features can leak | Strict split, no test-set tuning, report learning curve and held-out only |
| R9 | Gate binding defeats the tax test | If accuracy is at ceiling, the gate may not move `k*` | Choose a mid-accuracy condition for taxes; pre-register the gate and report both gated and unconstrained |
| R10 | Data licensing | SQuAD/HotpotQA are CC BY-SA 4.0; redistribution may violate terms | No raw text in repo; release IDs, prompts, predictions, and checksums only |
| R11 | Schedule slip | 20 weeks with a small team | P6 buffer; drop the boundary probe or the 1.5B replication before dropping the primary |

---

## 8. Out of scope

- A universal `k*` across tasks, readers, or hardware.
- Frontier or API readers (GPT, Claude, Gemini); no paid API calls.
- Full DPR/NQ corpus or dense-retriever training.
- Multi-GPU or datacenter GPU measurements.
- Carbon-optimal claims beyond constant-factor reporting and the split in Corollary 3.
- Prompt tuning, fine-tuning, or reranker training as a primary contribution.
- A production serving system or latency SLO study.

---

## 9. Change control

The preregistration is frozen before the P1 confirmatory analysis. After the freeze:

1. No edit to `prereg/PREREGISTRATION.md` or `prereg/analysis_plan.md` without an entry in
   `prereg/amendments.md`.
2. Every amendment states the date, the original text, the replacement, the reason, and
   whether outcome data had been seen.
3. Every deviation is also logged in `docs/DECISIONS.md`.
4. The analysis script records the prereg hash and the config hash in the run registry.
5. A gate may not be added, removed, or re-thresholded after seeing the primary outcome.
   Exploratory analyses are labeled exploratory.

The freeze commit is tagged `prereg-freeze-v1`. The tag is annotated and pushed; it is the
reference point for the paper's methods section.
