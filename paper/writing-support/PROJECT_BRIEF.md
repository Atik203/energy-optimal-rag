# PROJECT_BRIEF.md

Evidence base for drafting the energy-optimal-rag paper. Every material fact carries a source
pointer. Status labels: `logs` (measured), `code only`, `author`, `missing`.

- **Last scanned:** 2026-11-18 (updated after the P2 analysis was registered and the paper was updated)
- **Files read:** `README.md`, `ROADMAP.md`, `AGENTS.md`, `CITATION.cff`, `docs/P0_HARNESS_REPORT.md`,
  `docs/P1_RESULTS.md`, `docs/MEASUREMENT.md`, `docs/PROTOCOL.md`, `docs/IMPLEMENTATION_PLAN.md`,
  `docs/DECISIONS.md`, `prereg/PREREGISTRATION.md`, `prereg/analysis_plan.md`,
  `prereg/FREEZE.md`, `prereg/amendments.md`, `analysis/README.md`,
  `analysis/squad_qwen4b_p1/` (all outputs), `paper/README.md` (previous and current),
  `data/README.md`, `configs/base.toml`, `configs/analysis/prereg.toml`,
  `configs/runs/squad_qwen4b.toml`, `runs/registry.csv`, `runs/squad_qwen4b_p1/` (manifest,
  blocks, repeat), `artifacts/ledger.csv`, `artifacts/claims_evidence.csv`,
  `scripts/*.py` argument parsers, `G:\HaluRISC\Journal_Paper\halurisc.tex` (format reference).
- **Skimmed or skipped:** `src/rag_energy/` beyond the row-validity and analysis-writer paths;
  `tests/`; `web/`; `docs/proposal.md`, `docs/RISKS.md`, `docs/DATA_CARD.md`,
  `docs/RUNBOOK.md`; `data/manifest.json`; `artifacts/` contents beyond the three tracked CSVs.
  Skipped because they do not bear on the supplement or the brief's open questions; the
  manifest and proposal should be read before drafting the main paper's data and related-work
  sections.

## 1. Problem, gap, objective

- **Problem.** Retrieval depth `k` (the number of BM25 passages placed in the reader prompt)
  controls both accuracy and energy. Energy per query rises roughly linearly in `k`, accuracy
  rises and then plateaus, so the deployment question is a depth decision under an accuracy
  tolerance, not a curve description. [README.md §Status; ROADMAP.md §1.1]
- **Gap (as the repository states it).** The pilot's static 2 pp optimum failed: `k* = 32` at
  the grid boundary with bootstrap `P(k* optimal) = 0.61 < 0.8`. The 5 pp pilot selected
  `k = 4` with 69.3% savings but is a signal, not a certification: the proposal reports
  `P = .537` for the 5 pp selection and no pilot non-inferiority test is reported.
  [ROADMAP.md §1.1–1.2; README.md §Claim boundary; D-003, D-010]
  P1 then failed to confirm the 5 pp policy: the one-sided lower bound is −6.17 pp, outside the
  −5 pp margin, so the static policy claim is a documented negative while the energy savings
  (58.17%) and the descriptive energy model replicate.
  [docs/P1_RESULTS.md §2, §8; analysis/squad_qwen4b_p1/noninferiority.json]
- **Objective.** Test a margin-indexed policy claim — 5 pp normalized-EM non-inferiority at
  `k = 4` versus `k = 32` with at least 20% energy savings — and report the identity
  diagnostic, the certification cost `N*`, and (later) the adaptive policy. The study does not
  test a universal `k*`, a 2 pp optimum, or an unmeasured learned-policy gain.
  [prereg/PREREGISTRATION.md §2; ROADMAP.md §1.3]
  The paper's contribution is therefore the measurement and decision framework plus a negative
  static-policy result; the adaptive direction is the remaining route to a positive policy
  finding, and it is untested. [docs/P1_RESULTS.md §9–10; D-007]
- **Article type.** Measurement plus decision theory, with a causal tax manipulation and an
  adaptive-policy arm. Target venue is not stated in the repository; the format follows the
  reference manuscript `G:\HaluRISC\Journal_Paper\halurisc.tex` (Elsevier CAS).
  [paper/FORMAT.md §1; paper/README.md §File map]

## 2. Data

- **Primary.** SQuAD v1.1 dev, `n = 1,000`, depths `{0,1,2,4,8,16,32}`, seed `20261115`;
  normalized EM primary, lenient span and F1 ≥ 0.5 as sensitivity.
  [prereg/PREREGISTRATION.md §3; configs/runs/squad_qwen4b.toml]
- **Corpus.** 20,958 unique contexts and 45,651 70-word passages, built from the SQuAD train and
  dev files (dev alone has 10,570 questions and about 2,067 paragraphs); contexts truncated to
  256 words before chunking. [data/README.md §Datasets; docs/P0_HARNESS_REPORT.md §1]
- **Splits.** 200 P0 / 1,000 P1 / 500 replication / 200 boundary / 200 context / 150 tax.
  P0 is disjoint from P1; the nested arms are disjoint; IDs and per-split SHA-256 are tracked,
  never text. [docs/P0_HARNESS_REPORT.md §1; D-015]
- **Secondary.** HotpotQA distractor dev, `n = 500`, `k ∈ {0,1,2,4,8,10}`, 10 paragraphs per
  question (2 gold, 8 distractors). [prereg/PREREGISTRATION.md §3; data/README.md §Datasets]
- **Licence and release.** SQuAD and HotpotQA are CC BY-SA 4.0 and are not redistributed; only
  IDs, versions, checksums, configs, prompts, predictions, and aggregates are released.
  [README.md §Data policy; prereg/PREREGISTRATION.md §12]
- **Ethics and annotation.** No human-subject data and no new annotation; the study uses public
  benchmarks. An ethics statement is not present in the repository. `[missing — author to
  confirm]`

## 3. Method

- **Reader.** Ollama `qwen3.5:4b`, Q4, `num_ctx = 4096`, `num_predict = 24`, temperature 0,
  `top_k = 1`, seed 42, thinking off; model digest `d8b0f5e9…e38c04`.
  [configs/runs/squad_qwen4b.toml; runs/registry.csv]
- **Retriever.** `rank_bm25.BM25Okapi`, top-32, 70-word passages, lowercase-alphanumeric
  tokenizer; CPU only. [configs/base.toml; docs/MEASUREMENT.md §4]
- **Energy.** NVML `power.draw` at 100 ms, trapezoidal integral over the request plus a 0.3 s
  tail, idle-subtracted and clipped at zero; idle measured before warm-up with a 0.20 CV gate;
  20 warm-up queries discarded; 20-query block calibration per depth gated on
  `factor_csv ∈ [0.8,1.4]`, all-or-nothing; repeat CV from 3 × 20 queries at `k = 8`.
  [docs/MEASUREMENT.md §2–3, §7; D-019]
- **Adopted vs new.** The reader, BM25, normalized EM, paired non-inferiority testing, and
  percentile bootstrap are adopted standards. New to this project: the measurement
  harness and calibration discipline, the margin-indexed decision framing, the identity
  diagnostic, the certification-cost calculation, and the tax manipulation.
  [docs/IMPLEMENTATION_PLAN.md §1, §6–§10]
- **Key equations.** `A(k) = n_k^{-1} Σ C_ik`; `J(k) = n_k^{-1} Σ J_ik`;
  `E(k) = Σ J_ik / Σ C_ik` (ratio of sums); `S(k) = (J_ret + J_pre)/J(k)`;
  `J(k) = a + bk`; `ε_J = kb/(a+bk)`; `Δ = ε_J − ε_A`;
  `N* = C_cert / (A(k*)[E(k_0) − E(k*)])`. [prereg/analysis_plan.md §3, §6, §8]

## 4. Workflow

1. Prepare SQuAD train+dev: contexts, 70-word passages, IDs, split file, manifest.
   `scripts/00_prepare_data.py`. [data/README.md]
2. Smoke-test the reader, sampler, and nonce path. `scripts/01_smoke_test.py`.
3. Sweep `n` questions × 7 depths with shuffled depth order and a per-request nonce.
   `scripts/02_run_sweep.py --config …`. [docs/PROTOCOL.md §3–4]
4. Block-calibrate at all seven depths; write `blocks.json` only if the gate is evaluated.
   `scripts/04_run_blocks.py`. [docs/PROTOCOL.md §5]
5. Repeat block at `k = 8`; write `repeat.json`. `scripts/04b_repeat_cv.py`.
6. Analyze the raw CSV; write `analysis/<run_id>/`. `scripts/05_analyze.py --run-id …`.
7. Generate paper tables and figures from the analysis output; map each number in
   `artifacts/claims_evidence.csv`. `paper/scripts/make_tables.py` and
   `paper/scripts/make_figures.py` emit `\input` fragments and PNGs from the registered run and
   analysis outputs. [analysis/README.md §Rules; paper/README.md §Tables and figures]

## 5. Experiments

| Arm | n | Depths | Reader | Status | Source |
|---|---:|---|---|---|---|
| P0 golden harness | 200 | 0–32 | qwen3.5:4b | **FAIL** (block calibration) | docs/P0_HARNESS_REPORT.md |
| P1 primary | 1,000 | 0–32 | qwen3.5:4b | **COMPLETE, NOT SUPPORTED** | runs/registry.csv; docs/P1_RESULTS.md |
| Replication (H7) | 500 | 0–32 | Qwen2.5-1.5B-Instruct | **COMPLETE, H7 NOT SUPPORTED** | docs/P2_RESULTS.md |
| Exploratory reader | 500 | 0–32 | Llama 3.2 3B Instruct, Q4, 4k | **COMPLETE, exploratory** | docs/P2_RESULTS_LLAMA.md |
| HotpotQA distractor | 500 | 0–10 | qwen3.5:4b | **COMPLETE, H7 SUPPORTED** | docs/P2_RESULTS_HOTPOT.md |
| Boundary probe | 200 | 32,48,64 | qwen3.5:4b, 8k | **COMPLETE, no cliff** | analysis/boundary_qwen4b_p2 |
| Context-budget probe | 200 | 32,48,64 | qwen3.5:4b, 16k, plus 4k control | **COMPLETE, no accuracy gain** | analysis/squad_qwen4b_ctx16k_p2 |
| Energy taxes | 150 each | 0–32 | qwen3.5:4b | **COMPLETE, inconclusive** | docs/P2_RESULTS_TAXES.md |
| P3 policy | 600/200/200 | 0–32 | qwen3.5:4b (P1 rows) | **COMPLETE, G4 NOT SUPPORTED** | docs/P3_RESULTS.md |
| H200 64k accuracy check | 200 | 64 | Qwen3.5-4B | Not run; accuracy only | prereg §2; MEASUREMENT §12 |

**Setup.** One local RTX 3060 Laptop 6 GB, batch size 1, AC power, screen off, no concurrent
jobs; Python 3.12; wall meter waived for P0/P1 (D-016). [README.md §Status; docs/MEASUREMENT.md §1]
**Tests.** One primary one-sided 5 pp non-inferiority test at `k = 4` vs `k = 32`; 10,000
question-level paired bootstrap resamples; percentile 95% intervals; `P(k* optimal)`; identity
gap; `N*`. No multiplicity correction for the single primary test. [prereg/analysis_plan.md §4–5, §12]

## 6. Results index

| Result | Value | Source | Status |
|---|---|---|---|
| `E(1)` pilot | 45.5 J/correct | docs/PILOT_EVIDENCE.md; artifacts/claims_evidence.csv C-002 | pilot |
| `E(32)` pilot | 157.1 J/correct | docs/PILOT_EVIDENCE.md; C-003 | pilot |
| `E(32)/E(1)` pilot | 3.45× | README.md §Status; C-004 | pilot |
| Affine fit pilot | `J(k) = 15.74 + 2.283k`, `R² = 0.9990` | ROADMAP.md §1.1; C-005 | pilot |
| Accuracy pilot | `A_EM` 0.395 (`k=1`) → 0.570 (`k=32`); flat 0.520–0.535 at `k=4–16` | ROADMAP.md §1.1 | pilot |
| Context-side share pilot | 36.3% (`k=2`) → 85.1% (`k=32`) | ROADMAP.md §1.1 | pilot |
| Retrieval-only share pilot | 3.5% (`k=32`) – 17.3% (`k=1`) | ROADMAP.md §1.1 | pilot |
| Identity gap pilot | +0.044 at `k=2`, CI [−0.050, +0.128]; +0.700 at `k=32` | ROADMAP.md §1.1 | pilot |
| Repeat CV pilot | median 3.80%, max 9.24% | ROADMAP.md §1.1 | pilot |
| Static 2 pp pilot | `k* = 32` boundary, `P = 0.61` | ROADMAP.md §1.1; D-003 | pilot, dead |
| 5 pp pilot | `k = 4`, 69.3% savings, `N* = 876`; `P = .537` | ROADMAP.md §1.1; D-010 | pilot signal, not certified |
| Oracle gain pilot | 78.8%, upper bound | ROADMAP.md §1.1; D-007 | pilot, bound |
| P0 clean sweep | 1,400/1,400 rows, 0 invalid, idle CV 1.12% | docs/P0_HARNESS_REPORT.md §6 | logs, uncalibrated |
| P0 block factor | `k=0` `factor_csv = 0.7944` | docs/P0_HARNESS_REPORT.md §6 | logs, FAIL |
| P0 uncalibrated anchors | `J(1)=15.18`, `J(4)=19.80`, `J(32)=76.15`; `a=11.1023`, `b=2.0225`, `R²=0.9941` | docs/P0_HARNESS_REPORT.md §2 | logs, not adjudicable |
| P1 rows and invalidity | 7,000/7,000 rows, 0 invalid; 1,000 questions at all 7 depths | analysis/squad_qwen4b_p1/metadata.json; docs/P1_RESULTS.md §1 | logs |
| P1 calibration | All 7 factors pass: 0.8089, 1.2506, 1.2403, 1.3111, 1.2902, 1.2143, 1.0587 | runs/squad_qwen4b_p1/blocks.json | logs |
| P1 idle and repeat | 15.794 W, CV 1.23%; repeat median 2.81%, max 18.44%, MDE 5.62% | blocks.json; repeat.json; docs/P1_RESULTS.md §1 | logs |
| P1 primary 5 pp | `A(4)=0.450`, `A(32)=0.493`, diff −4.30 pp, lower −6.17 pp, `p=0.2691`, b/c 44/87 | noninferiority.json; C-025 | **not supported** |
| P1 savings | 58.17%, 95% CI [56.02, 60.14] | noninferiority.json; C-026 | supported (descriptive) |
| P1 affine fit | `J(k)=24.0759+2.2772k`, `R²=0.9714`, lack-of-fit `p=0.2813` | fit.json; C-027 | H1 supported |
| P1 context share | `S(4)=0.355`, increasing 0.209 → 0.807 | estimates.csv; C-028 | H4 supported |
| P1 identity gap | `Δ(4)=+0.2004` [0.1677, 0.2320]; `Δ(32)=0.703` | identity.csv; C-029 | H3 not supported |
| P1 certification | `N*=6,189` [5,697, 6,748]; `C_cert=311,992` J | certification.json | descriptive |
| P1 selection and gates | `k*=4`, `P(k* optimal)=0.7244`; K1 K2 K4 K7 pass, K3 K5 fail; G1 G2 fail, G3 pass | gates.json; bootstrap.json | adjudicated |
| P2 Qwen rows | 3,500/3,500 rows, 0 invalid | runs/registry.csv; docs/P2_RESULTS.md | logs |
| P2 Qwen H7 | `A(4)=0.360`, `A(32)=0.340`, diff +2.00 pp, upper +4.90 pp | analysis/squad_qwen15b_p2/direction.json; C-030 | **not supported** |
| P2 Qwen calibration | 4/7 factors pass; repeat CV max 80.15% | runs/squad_qwen15b_p2/blocks.json; repeat.json | energy uncalibrated |
| P2 Hotpot rows | 3,000/3,000 rows, 0 invalid | runs/registry.csv; docs/P2_RESULTS_HOTPOT.md | logs |
| P2 Hotpot H7 | `A(4)=0.410`, `A(10)=0.518`, diff −10.80 pp, upper −8.00 pp | analysis/hotpot_qwen4b_p2/direction.json; C-033 | **supported** |
| P2 Hotpot calibration | 6/7 factors pass (k=0 miss); repeat CV max 6.77% | runs/hotpot_qwen4b_p2/blocks.json; repeat.json | energy uncalibrated |
| P2 Hotpot recall | 0.732 at k=4, 0.902 at k=8, 1.000 at k=10 | analysis/hotpot_qwen4b_p2_retrieval_recall.json | descriptive |
| Boundary probe | A 0.475/0.485/0.505 at k=32/48/64 | analysis/boundary_qwen4b_p2/report.md | diagnostic |
| 16k probe | A 0.475/0.485/0.500 at k=32/48/64; 4k control A(32)=0.475 | analysis/squad_qwen4b_ctx16k_p2/report.md | diagnostic |
| Llama 3B | peak A(4)=0.476; A(32)=0.426 | analysis/squad_llama3b_p2/report.md; C-036 | exploratory |
| Tax arms | fixed A→0.5867 at k=32; per-passage A→0.5733 at k=32 | analysis/fixed_a/report.md; analysis/per_passage_b/report.md; C-037–C-038 | inconclusive |
| P3 policy | test 0.380 at 66.38 J/correct vs static k=1 0.385 at 65.71 | analysis/policy/policy.json; C-039 | **G4 not supported** |
| P3 oracle | 41.28% gain, policy capture −2.48%; oracle accuracy 0.605 vs static 0.385 | analysis/policy/policy.json; C-040 | unconstrained oracle |

## 7. Claim-evidence map

| Claim | Status | Evidence | Promotion condition |
|---|---|---|---|
| The energy–depth tradeoff is steep under the pilot conditions. | Supported (pilot) | docs/PILOT_EVIDENCE.md; C-002–C-004 | None; pilot only |
| Energy is affine in depth with `R² ≥ 0.95`. | **Supported (P1): H1** | analysis/squad_qwen4b_p1/fit.json; C-027 | None; confirmed |
| At a 5 pp margin, `k = 4` is non-inferior to `k = 32` and saves ≥20%. | **Not supported (P1)** | analysis/squad_qwen4b_p1/noninferiority.json; C-025; docs/P1_RESULTS.md §2 | None; reported as a negative |
| At `k = 4` the calibrated saving is 58.17% [56.02, 60.14]. | Supported (descriptive) | C-026; estimates.csv | Not a certified saving |
| The optimal-depth identity holds at an interior depth and flags over-retrieval at `k = 32`. | **Not supported at `k=4`** (gap +0.2004, CI excludes 0); flags `k=32` (gap 0.703) | identity.csv; C-029 | Diagnostic only; no promotion |
| Absolute `J`, `E`, `N*`, `S(k)` for P1. | **Claimable**: all seven block factors passed | runs/squad_qwen4b_p1/blocks.json; prereg §4.1 | Calibrated, with the `k=0` 0.8089 caveat |
| A query-conditional policy captures ≥50% of a ≥20% oracle gap. | **Not supported (P3)**: oracle gain 41.28%, policy capture −2.48% | docs/P3_RESULTS.md; analysis/policy/policy.json; C-039–C-040 | No adaptive claim |
| H7 direction replicates on Qwen2.5-1.5B or HotpotQA. | **Mixed**: Qwen not supported (+2.00 pp), HotpotQA supported (−10.80 pp) | docs/P2_RESULTS.md; docs/P2_RESULTS_HOTPOT.md; C-030, C-033 | G5 satisfied via HotpotQA; Qwen arm does not replicate |
| Llama 3B / 16k context probe change H7 or G5. | No | prereg §2; D-012–D-013 | Prohibited post-outcome |
| H200 energy result. | No energy claim possible | prereg §2; MEASUREMENT §12 | Prohibited |
| P0 reproduces the pilot energy curve. | No: P0 FAIL | docs/P0_HARNESS_REPORT.md §4 | Not a paper claim |

## 8. Terminology lock

| Concept | Canonical name | Symbol | Do not use |
|---|---|---|---|
| Number of passages retrieved | retrieval depth | `k` | "top-k" for the depth, "number of docs" |
| Joules per correct answer | energy per correct answer | `E(k)` | "energy efficiency", "J/answer" without units |
| Joules per query | energy per query | `J(k)` | "query cost" |
| Accuracy | normalized exact-match accuracy | `A(k)` | "EM score" without "normalized" |
| Context-side energy share | context-side energy share | `S(k)` | "retrieval energy share" |
| Retrieval-only share (CPU proxy) | retrieval-only share | `S_r(k)` | "retrieval share" unqualified |
| Depth selected under margin `m` | selected depth under margin `m` | `k*(m)` | "optimal depth", bare `k*` |
| Relative energy saving | savings ratio | `1 − E(4)/E(32)` | "energy reduction" without depths |
| Break-even queries | certification cost | `N*` | "sample size" |
| Block correction | block calibration factor | `f_csv` | "correction factor" unqualified |
| Row that passed protocol checks | valid row | — | "valid question" (the unit is a question) |
| P0 run | P0 golden harness check | — | "P0 experiment", "pilot rerun" |
| Frozen analysis intent | preregistration (`prereg-freeze-v1`) | — | "pre-registration plan", "protocol v2" |
| Reader tags | `qwen3.5:4b`, Qwen2.5-1.5B-Instruct, Llama 3.2 3B Instruct | — | "Qwen 4B", "the 3B model" |

## 9. Conflicts between sources

| What | Where | Source trusted | Author decision needed |
|---|---|---|---|
| P1 registry notes retain an early `idle CV 0.2352 exceeds 0.20` warning, while the final run records 15.794 W at CV 1.23% and completed 7,000 rows | runs/registry.csv (P1 row) vs runs/squad_qwen4b_p1/blocks.json and analysis metadata | blocks.json and the analysis metadata for the final measurement | No: the note is stale; quote the final idle only, not the early warning |
| `P = .537` for the 5 pp selection | README.md §Claim boundary; ROADMAP.md §1.1; D-010 | Neither until resolved | Yes: selection probability or p-value? P1 supersedes its use, but the pilot wording still needs an answer |
| "P1 deferred" vs "P1 started" | D-021 vs D-022/D-023 | D-022/D-023 | No: supersession is logged; use D-022 wording |
| "The run is still invalid on the calibration failure and the 46.4% idle CV" | docs/P0_HARNESS_REPORT.md §2 | Read as the first run; `_r3` had 1.12% CV | No, but quote carefully: `_r3` is invalid for calibration, not for idle |
| "LaTeX and BibTeX arrive in P5" | old paper/README.md | Superseded | No: supplement exists; update is done |
| Paper author list: one author in CITATION.cff, four authors in the reference manuscript | CITATION.cff vs G:\HaluRISC\Journal_Paper\halurisc.tex | CITATION.cff is this project's record | Yes: confirm the author list, affiliations, corresponding author |

## 10. Venue and supervisor constraints

- **Template.** Elsevier CAS (`cas-sc`), copied from the reference manuscript. No venue is named
  in the repository. [paper/FORMAT.md]
- **Length, citation style, word limit.** Not stated. Numeric citations follow the reference
  (`elsarticle-num`). `[missing — author to confirm]`
- **AI-use policy and supervisor writing guide.** Not present in the repository. The authorship
  rung for this work is C (agent drafts from project evidence; the author verifies and revises),
  and disclosure may be required by the institution. See `writing-support/VOICE_PROFILE.md`.

## 11. Section status

| Section | Status | Main gaps |
|---|---|---|
| Abstract | Drafted | Lead with the negative 5 pp result and the mixed P2 replication |
| Introduction | Drafted | Gap statement needs citations |
| Related work | Blocked | `refs.bib` exists but the related-work keys and claims are not verified |
| Theory | Drafted | Theorem statements are described in `docs/IMPLEMENTATION_PLAN.md §10` |
| Method / protocol | Supplement S1–S4 drafted | — |
| Results | Drafted | P1 and P2 analysis complete; paper tables drafted |
| Replication, policy, taxes | P2 complete; P3 complete and negative | No remaining experimental phase before P4 |
| Limitations | Drafted in main text and supplement S5, S7.5 | — |
| Supplement | S1–S8 complete | Affiliation placeholder only |

## 12. Open questions

1. **Authorship.** Who are the co-authors, affiliations, corresponding author, and ORCID iDs?
   The supplement carries an affiliation placeholder.
2. **Venue.** Is the Elsevier CAS format final, or is another venue targeted? This fixes length
   and reference style.
3. **Framing the negative result.** The paper's headline is now a negative static-policy result
   with a strong descriptive energy result. Should the adaptive (P3) direction be presented as
   the main remaining contribution, or as future work?
4. **`P = .537`.** Selection probability or p-value? P1 supersedes its role, but the pilot
   sentence still needs a defensible reading.
5. **`k=0` calibration caveat.** The factor 0.8089 passed but is 1.1% above the floor. Report it
   in the main text, the supplement only, or both?
6. **Wall meter.** Keep the D-016 waiver for P2, or borrow a meter for a descriptive
   whole-system check?
7. **Raw-data backup.** D-020 leaves P0/P1 raw runs local-only. The reproducibility package is
   incomplete until an external copy exists; when will it be made?
