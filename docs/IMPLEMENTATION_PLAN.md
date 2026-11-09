# Implementation Plan

**Project:** Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation (G2)
**Version:** 0.1.0 · 2026-11-09
**Status:** post-pilot MARGINAL · scaffold
**Companion documents:** [`PROTOCOL.md`](PROTOCOL.md), [`MEASUREMENT.md`](MEASUREMENT.md),
[`DATA_CARD.md`](DATA_CARD.md), [`RISKS.md`](RISKS.md), [`RUNBOOK.md`](RUNBOOK.md),
[`../prereg/PREREGISTRATION.md`](../prereg/PREREGISTRATION.md)

## 1. Purpose and claim boundary

The project asks a decision question: at what retrieval depth `k` does a retrieval-augmented
generator minimize **joules per correct answer**, and is it worth the energy to find out? The
estimand is the ratio of expectations `E(k) = E[J_k] / E[C_k]` under a pre-registered accuracy
gate `A_min`.

The pilot changed the claim. A static "2 percentage-point optimal depth" was the original
target, and it is **dead**. On 200 SQuAD questions the 2 pp EM gate selected `k* = 32`, the grid
boundary, with bootstrap `P(k* optimal) = 0.61 < 0.8`. The accuracy floor sat inside the paired
confidence interval of `k = 16`, so this was a power failure, not a flat-curve failure. The
energy effect is large and precise: `E(32) = 157.1` versus `E(1) = 45.5` J/correct (3.45×), with
`J(k) = 15.74 + 2.283k` and `R² = 0.9990`.

What survives is narrower. At a **5 pp** EM non-inferiority margin the pilot selected `k = 4`
with **69.3%** savings and a descriptive `N* = 876`. That is a policy result contingent on a
margin, and it must be re-established at `n = 1,000` before it is called certified. The **2 pp**
margin is estimation-only. The **78.8%** adaptive-oracle gain is an upper bound computed with
hindsight; no learned policy exists. The paper may not claim a universal `k*`, a "2 pp optimal"
depth, or a "5 pp certified" result before the rerun. The implementation has two jobs: make the
measurement reproducible, and make the decision rule honest.

## 2. Repository and file layout

The repository uses a `src/` layout. `src/rag_energy/` is divided by concern. `config.py` and
`cli.py` are standard-library only.
`data/` handles SQuAD/HotpotQA preparation, 70-word chunking, the manifest, and deterministic
splits. `retrieval/` wraps BM25, computes query features, and converts CPU retrieval time to an
upper-bound energy proxy. `readers/` holds the fixed prompt and the Ollama and Hugging Face
backends. `energy/` holds the NVML sampler, integration, idle estimation, block calibration,
nonce generation, and the wall-meter record. `stats/` holds the ratio estimator, power, identity
test, curve models, policy scaffold, and multiplicity control.

`configs/` is the single source of run parameters: `base.toml` (seed `20261115`, paths, reader,
retriever, energy, statistics), `configs/runs/` (one file per experiment), `configs/grid/`
(named depth grids), `configs/taxes/` (two causal conditions), and
`configs/analysis/prereg.toml` (frozen margins and splits). `scripts/` is the numbered pipeline.
`prereg/` holds the frozen intent, analysis plan, and amendment log. `runs/` holds the registry
and git-ignored raw runs. `artifacts/` holds the ledger and claims-evidence map. `paper/` and
`docs/` are the writing surface.

The tracked data surface is deliberately small: `data/manifest.json`, `data/README.md`,
`runs/registry.csv`, `artifacts/ledger.csv`, and `artifacts/claims_evidence.csv`. Everything
else under `data/`, `runs/<run_id>/`, and generated analysis output is git-ignored. Raw text is
never committed.

## 3. Environment and harness reuse

The target is Python 3.12 at `C:\ProgramData\anaconda3\python.exe`, conda environment
`rag-energy`, a local RTX 3060 Laptop 6 GB, and Ollama `qwen3.5:4b` (Q4, 3.3 GB, 4096 context).
The replication reader is `Qwen/Qwen2.5-1.5B-Instruct` in float16.

The pilot harness is reused rather than rewritten: BM25 Okapi over lowercase alphanumeric
tokens, a fixed prompt, greedy decoding, a unique nonce at the start of every request, NVML
sampling with idle subtraction, 20-query block calibration, randomized depth order, and a repeat
block. These are not optional. The nonce exists because Ollama reused a `k = 32` prefix after a
`k = 16` request and cut prefill from 710 ms to 247 ms; without it the curve is confounded by
request order. Block calibration exists because per-query windows miss the ~100 ms power ramp,
most at short depths.

Optional dependencies are imported lazily inside the functions that need them (`rank_bm25`,
`pynvml`, `torch`, `transformers`), so the smoke test and `validate` run with only pytest.
`requirements-lock.txt` is an explicit placeholder; locks are generated on the target machine.

## 4. Data preparation

SQuAD v1.1 dev is primary: 10,570 questions, 20,958 unique dev contexts. The pilot truncated
contexts to 256 words and chunked them into 70-word passages (45,651 passages), and sampled 200
questions stratified over the seven wh-types. The powered run uses **1,000** questions with the
same corpus and chunking, drawn with seed `20261115`; the ID list is hashed into the manifest.
Gold answers are normalized for EM; raw text stays git-ignored.

HotpotQA distractor dev is the external-validity set: **500** questions, 10 paragraphs each
(2 gold, 8 distractors). The corpus is per-question, so the depth grid is `{0,1,2,4,8,10}`.
Pooling paragraphs across questions changes the task and is forbidden.

The manifest records ID, name, version, split, source URL, license, counts, SHA-256 checksums,
preparation seed, retrieval ceiling, and status. Both datasets are CC BY-SA 4.0; the repository
releases IDs, configs, prompts, predictions, and aggregates, not raw text.

## 5. Powered rerun and power

The pilot's accuracy side was underpowered: at `n = 200` the MDE was roughly 4–5 pp, so a 2 pp
margin could not be certified. The rerun is sized for a 5 pp non-inferiority decision.

The primary experiment is SQuAD, `n = 1,000`, seven depths, `qwen3.5:4b`. The primary comparison
is `k = 4` versus `k = 32` at one-sided 5%, margin 5 pp, requiring at least 20% savings. Under a
planning discordant rate of 0.08, the paired-difference SD is about 0.283 and the standard error
at `n = 1,000` is about 0.9 pp.

| n | MDE at 80% power | Power at 0 pp | 1 pp | 2 pp | 3 pp |
|---:|---:|---:|---:|---:|---:|
| 200 | 5.0 pp | 0.80 | 0.64 | 0.44 | 0.26 |
| 500 | 3.1 pp | 0.99 | 0.94 | 0.77 | 0.47 |
| 750 | 2.6 pp | >0.99 | 0.99 | 0.90 | 0.61 |
| 1,000 | 2.2 pp | >0.99 | 0.998 | 0.96 | 0.72 |
| 1,500 | 1.8 pp | >0.99 | >0.99 | 0.99 | 0.86 |

The table is a planning tool, not a result. It shows that `n = 1,000` is comfortably powered for
5 pp when the true difference is 0–2 pp, and still reasonable at 3 pp. A 2 pp margin remains
estimation-only: the 95% half-width at `n = 1,000` is about 1.8 pp, so the design can estimate a
2 pp difference but cannot certify it against a 2 pp boundary. The paper must say this and must
not promote the 2 pp result after seeing the data.

The 1.5B replication uses `n = 500`, seven depths. HotpotQA uses `n = 500`, six depths. The
boundary probe uses `n = 200` at `k ∈ {32,48,64}` and is diagnostic, not powered for accuracy.
A 16k-token context check tests whether the pilot boundary was a 4096-context artifact; if
the card cannot hold 16k, the limit is reported.
All three fit the 15–20 GPU-hour budget.

## 6. Estimand and correctness

The primary estimand is `E(k) = sum(J_k) / sum(C_k)` over the analysis population: total joules
divided by total correct answers, not the mean of per-query ratios. The ratio can be gamed by
failing cheaply, so every `E(k)` is reported with `A(k)` and the gate. The primary gate is 5 pp
below the reference depth's accuracy, with `k = 32` as reference. The 2 pp gate is a sensitivity
analysis and is never used for certification.

Correctness is primarily normalized EM: lowercase, strip punctuation and articles, collapse
whitespace. Secondary rules are lenient span match (normalized gold appears in a short
prediction) and token F1 ≥ 0.5. The pilot showed strict EM penalizes answers such as "Denver
linebacker Von Miller" for gold "Von Miller"; lenient/F1 gave an interior `k = 16` at 42.5%
savings where EM gave the boundary. The conclusion "never 32" was robust, but the location was
not. The rerun pre-registers EM and requires the qualitative conclusion to survive both
secondary rules; if it does not, the paper reports the dependence rather than picking the
favorable rule.

The analysis population is every question with a prepared gold answer and a completed generation
at every depth. A failed or empty generation is a wrong answer at that depth and is retained.
Per-query energy is used for pairing and bootstrap; absolute energy relies on block
calibration. Uncertainty uses 10,000 paired bootstrap resamples over questions, yielding
intervals for `E(k)`, `A(k)`, `S(k)`, and the identity gap, plus the probability that each depth
is optimal. The primary non-inferiority test is a paired one-sided test on correctness; the
bootstrap is the uncertainty layer, not a substitute.

## 7. Energy measurement

The primary sensor is NVML `power.draw` every 100 ms via `pynvml`, with utilization, memory,
temperature, and SM clock recorded. The 100 ms cadence is a sampling label, not a precision
claim: on this laptop the driver updates power coarsely, about 1 Hz. Absolute joules therefore
rely on 20-query block calibration and the repeat CV.

Each query is integrated by the trapezoidal rule over its HTTP call, then idle-subtracted using
the 60 s pre-run baseline (15.56 W, CV 10.4%; post-run 17.63 W). Using the post-run value lowers
every energy by ~4% almost uniformly and changes E ratios by under 1%. After the sweep, 20
back-to-back queries per depth are integrated as a block and the per-query integrals are scaled
to the block total. Pilot factors ranged from 1.041 to 1.188, largest at `k = 2`.

BM25 retrieval energy is a CPU proxy: measured wall time × 20 W single-thread active-above-idle,
about 3.11 J/query. It is an upper bound and is labeled as such. Retrieval is 3.5% of total at
`k = 32` and 17.3% at `k = 1`. The context-side share rises from 36.3% at `k = 2` to 85.1% at
`k = 32`; the green lever is prefill, not the BM25 fetch.

Controls: 20 warm-up queries discarded; depth randomized within question; unique 10-hex nonce
per request; batch size 1; no concurrent jobs; AC power; screen off; temperature, clock, and
throttle fraction logged. Three blocks of 20 identical queries at `k = 8` give the repeat CV;
the pilot median was 3.80%, max 9.24%. A wall meter measures whole-system energy on a 30-query
subset per condition, and the ratio to the integrated GPU+CPU value is reported.

## 8. Query-conditional policy

The static population optimum is the wrong object when queries are heterogeneous. Theorem 2
shows a static depth can be arbitrarily worse than a query-conditional policy at equal accuracy.
The policy experiment is the adaptive contribution; 78.8% is only its ceiling.

Features are pre-generation and cheap: BM25 top score, second score, gap, mean, standard
deviation, entropy, number of positive scores, question length, and question type. No gold
answer, post-generation signal, or depth label is used. The split is 600 train, 200 validation,
200 test, assigned by hashing `seed:question_id`, so it is stable and auditable.

The model is a cost-sensitive classifier or shallow decision tree predicting the cheapest depth
whose predicted correctness clears the gate. Validation selects the model and operating point;
test is touched once. Evaluation is at matched accuracy against the best static `k`: accuracy is
held at the static reference and energy per correct answer is compared. The headline is the
fraction of the oracle gap captured on the same test questions. A policy capturing at least 50%
of a ≥20% oracle gain passes G4. A policy that does not is a reported negative; the static 5 pp
result can stand without it.

## 9. Energy-tax manipulation

A fixed dummy GPU computation before generation adds 10–30% of `a = 15.74 J` (config: 3.148 J,
20%) without changing prompt, passages, or answer. A second condition runs dummy work once per
retrieved passage, adding 10–30% of `b = 2.283 J` per passage (config: 0.457 J, 20%).

Corollary 1 predicts `k*` increases with the fixed cost and decreases with the per-passage cost.
Each condition uses 150 questions and the same seven depths. The test is on the sign, not only
significance; gated and unconstrained optima are both reported. Wrong signs falsify the
affine/split model. Because a binding gate can mask movement, the taxes are also run at a
mid-accuracy gate where the optimum is interior; this is pre-registered, not post-hoc.

## 10. Theory validation

Theorem 1 gives the identity `kJ'(k)/J(k) = kA'(k)/A(k)`, unimodality under noisy coverage, and
comparative statics. The pilot validated the identity at `k = 2`: gap +0.044, 95% CI
[−0.050, +0.128], which includes zero. At `k = 32` the gap was +0.700, so the diagnostic flags
over-retrieval. The coverage model fit poorly (`A_0 = 0.324`, `p = 0.0218`, `R² = 0.332`). Global
unimodality is rejected; the identity remains a local diagnostic. The rerun tests it at the
selected interior depth on SQuAD, the 1.5B reader, and HotpotQA, with bootstrap intervals.

Theorem 2 is the price of static depth. For easy queries answerable at `k = 0` and hard queries
answerable only at `k = K`, the oracle costs `a + εbK` and the best static depth costs `a + bK`;
the ratio tends to `1 + bK/a` as `ε → 0`. This is why adaptivity is necessary at equal accuracy,
and why the oracle gap is reported even before a policy exists.

Theorem 3 gives the certification rate and `N* = C_cert / (A(k*) [E(k_0) − E(k*)])`. The pilot
sweep cost 49.6 kJ and gave `N* = 876` for `k = 4`, 1,000 for `k = 8`, and 1,489 for `k = 16`. At
10,000 deployment queries the `k = 4` saving is 566 kJ against 49.6 kJ of calibration (8.8%);
at 100,000 it is 0.9%. The certificate is cheap; the accuracy margin, not the certificate, is
binding. `N*` is reported descriptively as a break-even, not a deployment guarantee.

The distractor counterexample is required. With `a = 1`, `b = 0.02`, `K = {0,1,2,4}` and
`A = (0.6, 0.9, 0.7, 1.0)`, energies are 1.667, 1.133, 1.486, 1.080: a local minimum at `k = 1`
and a lower global minimum at `k = 4`. A greedy policy stops at 1 and misses 4. Certification
must search globally, or the method must test monotonicity and rerank/compress first. HotpotQA
is where this is most likely to appear.

## 11. Analysis

The pipeline is deterministic and reads only registered raw CSVs. It computes `A(k)`, `J(k)`,
`E(k)`, retrieval-only and context-side shares, and the affine fit with `R²`. It runs the 5 pp
paired non-inferiority test, the 2 pp estimation, and margin sensitivity at 2, 3, 4, 5, 6, 8,
10 pp. It bootstraps `E(k)`, `A(k)`, `S(k)`, and `k*` with 10,000 paired resamples and reports
`P(k* optimal)`. It computes the identity gap from the fitted energy model and the empirical
accuracy derivative, with a bootstrap interval. It computes `N*` and evaluates the policy on
the held-out 200 only.

Multiplicity is controlled by having exactly one primary test; everything else is labeled
exploratory. If a secondary family is promoted, Holm is the default. Analysis code records the
prereg hash and config hash in the registry. Tables and figures are generated, never
hand-edited, and each maps to a row in `artifacts/claims_evidence.csv`.

## 12. Gates and stop rules

K1–K7 are the kill/reframe gates. The pilot passed K1 (245% energy effect), K4 (context share
36–85%), K6 (78.8% oracle gain), and K7 (CV 3.80%); it failed K2 (boundary), K3 (`P = 0.61`),
and K5 (span 3). The rerun re-adjudicates each once, on the pre-specified population. K1–K4 and
K6 firing is a kill/reframe; K5 and K7 are fixable measurement or framing problems before they
are kills.

G1 requires 5 pp non-inferiority at an interior `k` with ≥20% savings. G2 requires an upper
confidence bound on the accuracy loss ≤5 pp and `P(k* optimal) ≥ 0.8` for the 5 pp selection. G3
requires the context share at the selected `k` in [0.10, 0.70] and varying with `k`. G4 requires
oracle gain ≥20% and a learned policy capturing ≥50% at matched accuracy. G5 requires
replication on the 1.5B reader or HotpotQA.

A fired gate is reported, not tuned away. A gate may not be added, removed, or re-thresholded
after the primary outcome is seen. The prereg freezes before P1 and is tagged
`prereg-freeze-v1`; any change goes through `prereg/amendments.md` and `docs/DECISIONS.md`.

## 13. Deliverables, budget, storage

Deliverables: open harness (MIT), frozen dataset IDs and manifest, raw energy ledger, analysis
scripts, prereg and amendments, paper draft and supplement, reproducibility package with
environment lock, model digests and checksums, Zenodo DOI, data card, measurement protocol, risk
log, and the claims-evidence map.

The budget is local-only: 15–20 GPU-hours, ~$2 electricity, $25 wall meter, $10 USB backup,
$10 contingency, total ≤$47. No rental, no paid API. Storage is ~5 GB on `E:` for raw data,
processed parquet, run CSVs, and figures; model weights stay in the Ollama store. The USB drive holds a second copy of `runs/`, `artifacts/`, and the
manifest.

## 14. Risks

Main risks: scoring-rule dependence, reader strength/SQuAD saturation, one corpus and retriever,
thermal throttling, coarse NVML resolution, Ollama prefix caching, energy noise, policy
overfitting, a binding gate that defeats the tax test, and data licensing. Mitigations are in
[`RISKS.md`](RISKS.md). The two that can change the thesis are scoring dependence (handled by
pre-registering EM and requiring survival under lenient/F1) and a binding gate (handled by the
mid-accuracy tax condition).

## 15. First sprint and definition of done

The first 10 days: scaffold and CI; environment and config validation; data preparation and BM25
index; energy-harness validation; golden reproduction of the 200-question pilot curve; prereg
freeze; power and sample-size lock; two halves of the P1 sweep; gate review. Acceptance checks
are in [`../ROADMAP.md`](../ROADMAP.md) section 3. The golden reproduction must land within 10%
of the pilot `E(k)` at every depth; otherwise P1 does not start.

A task is done when it has code, a test, a docs update, and a ledger entry where applicable. A
result is not a result until it traces to `runs/<run_id>/raw.csv` and is mapped in
`artifacts/claims_evidence.csv`. A claim is not a claim until it respects the boundary in
section 1.
