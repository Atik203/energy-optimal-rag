# Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation

[![CI](https://github.com/Atik203/energy-optimal-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/Atik203/energy-optimal-rag/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docs: CC BY 4.0](https://img.shields.io/badge/Docs-CC%20BY%204.0-lightgrey.svg)](LICENSE-DOCS)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

Measuring, certifying, and deciding the retrieval depth that minimizes **joules per correct
answer** — and deciding whether the energy spent finding that depth is worth it.

**Research status: post-pilot MARGINAL.** This repository is an initial public scaffold. It
contains no confirmatory results. The pilot evidence is reported below exactly as measured,
including the claim that failed.

---

## Status: what survived the pilot, and what did not

The 2-hour pilot ran 200 SQuAD v1.1 dev questions at seven depths
(`k ∈ {0,1,2,4,8,16,32}`), 1,400 generations, on a local RTX 3060 Laptop 6 GB with
`qwen3.5:4b` (Q4, Ollama) and BM25 top-32 over 45,651 passages.

| Claim | Status after pilot | Evidence |
|---|---|---|
| Energy per correct answer rises steeply with depth | **Supported** | `E(32) = 157.1` vs `E(1) = 45.5` J/correct = **3.45×** |
| Energy is affine in depth | **Supported** | `J(k) = 15.74 + 2.283k` J, `R² = 0.9990` |
| Accuracy rises then plateaus | **Supported** | `A_EM` 0.395 → 0.570; flat 0.520–0.535 for `k = 4–16` |
| Context-side energy dominates | **Supported** | share 36.3% (`k=2`) → **85.1%** (`k=32`); retrieval-only 3.5–17.3% |
| Optimal-depth identity holds at the interior optimum | **Supported at k=2** | elasticity gap +0.044, 95% CI [−0.050, +0.128] |
| Identity certifies high-k behaviour | **Rejected** | gap +0.700 at `k=32`; 32 passages is over-retrieval |
| Measurement is repeatable | **Supported** | repeat CV median 3.80%, max 9.24% |
| **Static 2pp-optimal depth** | **DEAD** | `k* = 32` (boundary), bootstrap `P(k* optimal) = 0.61 < 0.8` |
| **5pp non-inferiority at k=4** | **Pilot signal — not certified** | 69.3% energy savings, `N* = 876` descriptive; proposal reports `P = .537` for the 5 pp selection |
| Query-conditional oracle gain | **Upper bound only** | 78.8% matched-accuracy oracle gain; no learned policy yet |

### Claim boundary

We do **not** claim a universal `k*`. We do **not** claim a "2pp-optimal" retrieval depth.
We do **not** claim a "5pp certified" result before the powered rerun. The 5 pp pilot result
is a signal, not a certification. The Llama 3.2 3B reader and the 16k context-budget probe are
exploratory/diagnostic and do not change H7 or G5. The optional H200 check is accuracy-only and
cannot support an energy claim. The proposal reports `P = .537` for the 5 pp selection; if
that is the selection probability, it is below G2's 0.8 stability threshold. In any case, no
pilot non-inferiority test is reported, so G2 is not claimed. The rerun must report the
non-inferiority test and the selection probability separately. The 78.8% oracle gain
is an upper bound computed with hindsight, not a result from a learned policy. The pilot's
static claim is dead; the surviving object is the decision problem around the accuracy margin.

The defensible next claim, if the rerun supports it, is narrow:

> At a pre-specified 5 percentage-point EM non-inferiority margin, an interior depth
> (`k = 4`) retains accuracy while saving roughly 69% of GPU energy per correct answer
> relative to `k = 32`, and a query-conditional policy captures a material fraction of the
> adaptive oracle gap at matched accuracy.

That is a policy result, not a universal optimum.

---

## The powered rerun

The pilot was sized for the energy curve, which is precise. The accuracy side was
underpowered: the minimum detectable effect was roughly 4–5 pp, so a 2 pp margin could not
be certified at `n = 200`. The rerun is designed around that failure.

| Component | Design |
|---|---|
| Primary experiment | SQuAD v1.1 dev, `n = 1,000`, `k ∈ {0,1,2,4,8,16,32}` |
| Primary decision | 5 pp EM **non-inferiority** at an interior `k`, with ≥20% energy savings |
| Secondary | 2 pp margin, **estimation only** — reported with CI, never used as a certification claim |
| Reader replication | Qwen2.5-1.5B-Instruct, `n = 500`, same grid |
| Third reader (exploratory) | Llama 3.2 3B Instruct, Q4, 4k context, `n = 500`, same 500 IDs as the 1.5B arm; no gate |
| Multi-hop / distractor | HotpotQA distractor, `n = 500`, `k ∈ {0,1,2,4,8,10}` |
| Boundary probe | `k ∈ {32,48,64}`, `n = 200`, 8k context budget for `k=64`; grid-artifact test |
| Context-budget probe (diagnostic) | Qwen3.5-4B Q4, `n = 200`, `k ∈ {32,48,64}` at 16k allocation plus a `k=32 @ 4k` control; not a 16k-token prompt and not a new `k*` |
| Optional H200 accuracy check | Qwen3.5-4B at 64k, accuracy-only; **not run; no energy claim** |
| Causal test | Fixed energy tax `Δa` and per-passage tax `Δb` at 10–30% of `a ≈ 15.74 J`, `b ≈ 2.283 J/passage` |
| Learned policy | Query features → depth, split 600/200/200, evaluated at matched accuracy against the best static `k` |
| Certification | `N* = C_cert / (A(k*)[E(k0) − E(k*)])`, reported descriptively per dataset and reader |

The Llama reader, context-budget probe, and optional H200 check are exploratory/diagnostic.
H7 remains Qwen2.5-1.5B-Instruct **or** HotpotQA; Llama does not satisfy H7 or G5. H200 results
are accuracy-only and are never pooled with RTX 3060 energy results. The local additions are
estimated at roughly 1.2–1.7 GPU-hours, within the 15–20 GPU-hour cap.

**Primary analysis population:** The unit is a question. A **valid row** requires a non-empty
nonce, a completed request, and a power window with no sampler error. A failed or empty
generation after a completed request is a **wrong answer** (`correct = 0`) and is retained, not
invalidated; a row is **invalid** only for a protocol violation: missing nonce,
request/backend failure, or sampler error. Descriptive `A(k)`, `J(k)`, and `E(k)` use every
sampled question with a valid row at depth `k`, and `n_valid(k)` and `n_invalid(k)` are
reported at each depth. A question is not dropped from depth `k` because it has no row at
another depth. The primary paired test uses questions with valid rows at both `k = 4` and
`k = 32`; the paired `n`, the discordant counts, and the invalid counts are reported. There
are no outcome-based exclusions: no winsorizing, trimming, or imputation, and wrong, slow, and
throttled answers stay in.

**Primary estimand:** the ratio of expectations `E(k) = E[J_k]/E[C_k]`, not the mean of
per-query ratios. **Primary test:** one-sided 5% non-inferiority on paired correctness at the
pre-specified interior depth, with a question-level bootstrap (10,000 resamples) for energy
and the ratio.

Full design, power table, gates, and stop rules: [`ROADMAP.md`](ROADMAP.md) and
[`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md). Draft analysis intent, frozen at
P1: [`prereg/PREREGISTRATION.md`](prereg/PREREGISTRATION.md).

---

## Repository map

```
.
├─ configs/            TOML configs: base, runs, grids, energy taxes, prereg parameters
├─ data/               data policy, manifest schema; no raw text is stored here
├─ src/rag_energy/     installable Python package (src layout)
│  ├─ data/            SQuAD/HotpotQA prep, chunking, manifest, splits
│  ├─ retrieval/       BM25, query features, CPU proxy energy
│  ├─ readers/         Ollama and HF readers, fixed prompts
│  ├─ energy/          NVML sampler, integration, idle, blocks, nonce, meter
│  └─ stats/           ratio estimands, power, identity, models, policy, multiplicity
├─ scripts/            numbered pipeline: prepare → smoke → sweep → taxes → analyze
├─ tests/              smoke tests that run without numpy/pandas
├─ prereg/             preregistration, analysis plan, amendment log
├─ runs/               run registry and per-run raw outputs (raw outputs git-ignored)
├─ analysis/           analysis outputs and notebooks (outputs git-ignored)
├─ artifacts/          energy ledger, claims-evidence map, checksummed artifacts
├─ paper/              manuscript workspace
└─ docs/               implementation plan, protocol, measurement, data card, risks, runbook
```

## Quick start

Requires Python 3.12 and (for experiments) a CUDA GPU with Ollama.

```bash
conda env create -f environment.yml
conda activate energy-optimal-rag
pip install -e .
pytest -q
python -m rag_energy.cli validate
```

Windows PowerShell equivalents:

```powershell
.\tasks.ps1 setup
.\tasks.ps1 test
.\tasks.ps1 validate
```

The smoke test and `validate` command use only the Python standard library. They do not
require numpy, pandas, torch, or a GPU.

## Data policy

- Raw SQuAD and HotpotQA text is **never** committed. `data/processed/` is git-ignored.
- The repository tracks only `data/manifest.json` (dataset IDs, versions, licenses,
  checksums) and `data/README.md`.
- Run-level CSVs live under `runs/<run_id>/` and are git-ignored. The aggregated,
  documented energy ledger is tracked at `artifacts/ledger.csv`.
- Model weights are never committed. Record model names, quantization, and digests in the
  manifest and run registry.
- Upstream SQuAD and HotpotQA licenses (CC BY-SA 4.0) remain in force. See
  [`DATA_LICENSE.md`](DATA_LICENSE.md).

## Roadmap

Phases P0–P6, sprint plan, gates K1–K7 / G1–G5, budget, deliverables, and risks:
[`ROADMAP.md`](ROADMAP.md).

Supervisor proposal: [`docs/proposal.md`](docs/proposal.md).

## Website

**Live site:** <https://energy-optimal-rag-web.vercel.app>

The public research site is in [`web/`](web/README.md): a Next.js app with the project
overview, research question, method, pilot evidence, roadmap, and a keyboard-driven slide
deck. Build and run instructions, including the offline install command, are in
[`web/README.md`](web/README.md).

## Citation

If you use this scaffold, cite the repository (see [`CITATION.cff`](CITATION.cff)). The
paper citation will be added when a manuscript is posted.

## License

- Code: [MIT](LICENSE), © 2026 Atikur Rahaman and contributors.
- Documentation and derived data: [CC BY 4.0](LICENSE-DOCS).
- Upstream datasets: their own licenses, which remain in force. See
  [`DATA_LICENSE.md`](DATA_LICENSE.md).
