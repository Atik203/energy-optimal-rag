# Pilot Evidence

**Status:** prior evidence · transcribed 2026-11-11 · not part of the confirmatory sample.

The pilot is prior evidence. It motivated the confirmatory design, and it is not part of the
confirmatory sample. The pilot raw CSVs are **not in this repository**. Every number below is
transcribed from the pilot report and the project documents cited in the source column; the
numbers are **not independently reproducible from this repository**. The confirmatory run will
produce registered raw CSVs under `runs/<run_id>/raw.csv`, and those rows — not these — will be
the evidence for the paper.

Nothing in this file is a confirmatory result. The 2 pp static claim is **dead**, the 5 pp
result is a **pilot signal, not certified**, and the 78.8% oracle gain is an **upper bound**.

## 1. Pilot design

| Item | Value | Source | Status |
|---|---|---|---|
| Questions | 200 SQuAD v1.1 dev questions, stratified over the seven wh-types | `README.md`; `ROADMAP.md` §1.1; `docs/IMPLEMENTATION_PLAN.md` §4 | pilot (design) |
| Depths | 7: `k ∈ {0,1,2,4,8,16,32}`; 1,400 generations | `README.md`; `ROADMAP.md` §1.1 | pilot (design) |
| Hardware | RTX 3060 Laptop 6 GB, batch 1, no concurrent jobs | `README.md`; `ROADMAP.md` §1.1 | pilot (design) |
| Reader | Ollama `qwen3.5:4b`, Q4, 4096 context, greedy, 24 new tokens | `README.md`; `docs/proposal.md` §8 | pilot (design) |
| Retriever | BM25 top-32 over 45,651 passages (70-word chunks, 256-word contexts) | `README.md`; `docs/IMPLEMENTATION_PLAN.md` §4 | pilot (design) |

## 2. Pilot measurements

| Claim | Value | Source document | Status |
|---|---|---|---|
| Energy per correct answer rises steeply with depth | `E(32) = 157.1` vs `E(1) = 45.5` J/correct = **3.45×** | `README.md`; `ROADMAP.md` §1.1; `docs/proposal.md` App. A | pilot |
| Energy is affine in depth | `J(k) = 15.74 + 2.283k` J, `R² = 0.9990` | `README.md`; `ROADMAP.md` §1.1; `docs/IMPLEMENTATION_PLAN.md` §1 | pilot |
| Accuracy rises then plateaus | `A_EM` 0.395 (`k=1`) → 0.570 (`k=32`); flat 0.520–0.535 at `k = 4–16` | `README.md`; `ROADMAP.md` §1.1; `docs/proposal.md` App. A | pilot |
| Context-side energy dominates and grows | share 36.3% (`k=2`) → **85.1%** (`k=32`) | `README.md`; `ROADMAP.md` §1.1; `docs/IMPLEMENTATION_PLAN.md` §7 | pilot |
| Retrieval-only share is small | 3.5% (`k=32`) – 17.3% (`k=1`), BM25 CPU proxy | `README.md`; `ROADMAP.md` §1.1; `docs/IMPLEMENTATION_PLAN.md` §7 | pilot |
| Optimal-depth identity holds at the interior optimum | gap +0.044 at `k=2`, 95% CI [−0.050, +0.128] | `README.md`; `ROADMAP.md` §1.1; `prereg/PREREGISTRATION.md` §1 | pilot |
| Identity flags over-retrieval at high `k` | gap +0.700 at `k=32` | `README.md`; `ROADMAP.md` §1.1; `prereg/analysis_plan.md` §6 | pilot |
| Measurement is repeatable | repeat CV (`k=8`) median 3.80%, max 9.24% | `README.md`; `ROADMAP.md` §1.1; `docs/IMPLEMENTATION_PLAN.md` §7 | pilot |
| Static 2 pp claim is dead | `k* = 32` (grid boundary); bootstrap `P(k* optimal) = 0.61 < 0.8` | `README.md`; `ROADMAP.md` §1.1; `docs/DECISIONS.md` D-003 | **dead** |
| 5 pp margin is a pilot signal | `k = 4`, **69.3%** savings, `N* = 876` queries; proposal reports `P = .537` for the 5 pp selection | `README.md`; `ROADMAP.md` §1.1; `docs/proposal.md` §1 and App. A | pilot signal, not certified |
| Query-conditional oracle gain | **78.8%** matched-accuracy oracle gain; no learned policy | `README.md`; `ROADMAP.md` §1.1; `docs/DECISIONS.md` D-007 | upper bound only |

### Reading the 5 pp row

The proposal reports `P = .537` for the 5 pp selection, alongside the 2 pp
`P(k* optimal) = .61`; the project record does not label the 5 pp quantity explicitly. If it is
the selection probability, it is below G2's 0.8 stability threshold. No pilot non-inferiority
test is reported. Either way, the pilot does not certify a 5 pp result. The rerun must report the
non-inferiority test and the selection probability separately; only the rerun, frozen in advance,
can support a certification claim.

## 3. What the pilot cannot establish

- **No universal `k*`.** The optimum is conditional on this reader, retriever, corpus, grid,
  and hardware.
- **No 2 pp optimum.** The static 2 pp claim is dead: `k*` landed on the grid boundary with
  `P(k* optimal) = 0.61 < 0.8`.
- **No 5 pp certification.** The pilot result is a signal, not a non-inferiority test; the
  proposal reports `P = .537` (if that is the selection probability, it is short of 0.8), and
  `n = 200` is underpowered for the accuracy side.
- **No learned-policy gain.** The 78.8% oracle gain uses hindsight; no policy was trained or
  evaluated on held-out questions.
- **No carbon-optimal claim.** Only constant-factor energy reporting is supported.
- **No generalization** to frontier/API readers, dense retrievers, other corpora, or the full
  NQ dataset.

## 4. Reproducibility status

| Question | Answer |
|---|---|
| Are the pilot raw CSVs in this repository? | No. |
| Can these numbers be regenerated from this repository alone? | No; they are transcribed. |
| What will replace them as evidence? | Registered confirmatory runs with `runs/<run_id>/raw.csv`. |
| Where are the transcribed claims indexed? | `artifacts/claims_evidence.csv`, rows with `run_id=pilot`. |

The repository ships the harness, configs, and protocol needed to re-run a pilot-shaped
experiment, but a re-run is new evidence, not a reproduction of these numbers. Until the
confirmatory run exists, every value in this file is labeled pilot and traces to the documents
cited above, not to a raw CSV in this repository.
