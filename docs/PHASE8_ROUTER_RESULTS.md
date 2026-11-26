# Phase 8 router - confirmatory result (max-reuse design)

**Prereg:** `prereg/qc_router_prereg.md`, SHA-256 `ba14c2f2…`, tag `prereg-qc-router-v1`
(frozen 2026-11-27, before any eval outcome existed).
**Run:** `squad_qwen4b_qc_router` - 10 blocks, 2,000 generations, 0 invalid rows,
idle 14.72 W (CV 0.008). **Analysis:** `analysis/qc_router/{train,select,eval,eval_ci}.json`.
**Decision:** D-039.

## Result

H-route is **not supported**. A pre-generation router over `k in {1,4}` captures
**0.54%** of the matched oracle gap (95% CI [-1.99, +3.29]), at an accuracy difference of
**+0.00 pp** (95% CI [-0.30, +0.30]).

| Quantity | Value | 95% CI |
|---|---:|---|
| Fresh oracle gap `A_oracle{1,4} - A(4)` | **3.80 pp** | [2.70, 5.00] |
| Policy capture of matched gap | **0.54%** | [-1.99, +3.29] |
| Accuracy difference vs static `k=4` | **+0.00 pp** | [-0.30, +0.30] |
| Policy energy saving vs `k=4` | 13.29% | - |
| Matched-gap energy headroom | 24.74% | - |
| AUC, correct@1 | 0.739 | - |
| AUC, correct@4 | 0.664 | - |

## Why it is a null

The depth histogram explains it before any statistic does: **995 of 1,000 questions were
routed to `k=4`**, five to `k=1`. At the frozen threshold the model almost never saw a
question it believed would be answered correctly from one passage, so the policy collapsed
onto the static baseline. A policy that reproduces `k=4` for 99.5% of queries cannot save
energy, and its accuracy is static accuracy by construction.

The stop rule fired as written: the eval gap of 3.80 pp is below the preregistered 10%
headroom threshold, so the headroom this router had to work with was thin before the model
was even applied.

This is consistent with the Phase 6 finding that **BM25 features predict `R`, not `Q`**.
Recall is partly predictable from retrieval scores; the sign of the depth effect is set by
reader precision, which retrieval scores do not observe. Selecting depth from BM25 scores
therefore cannot separate the questions that would benefit from fewer passages.

## Method notes

- **Max-reuse split, as preregistered.** Train on P1 (1,000 questions, existing rows),
  freeze the threshold on `qc_fresh` (1,000, existing rows), evaluate once on
  `qc_router_eval` (1,000 fresh qids, sha256 `4c16b6a6…`, disjoint from P0/P1 and every
  `qc_*` frame). No training label came from the eval frame.
- **Threshold frozen before the eval run existed.** `0.80`, chosen on `qc_fresh` to match
  static `k=4` accuracy (0.4550 vs 0.4550). It was read from `select.json`, never searched
  again.
- **Fixed per-depth costs.** Energy uses one block mean `J` per depth (20.52 and 27.94
  J/query), the R5 correction. Per-query windows are never used as costs.
- **One correction to the analysis script.** The first version re-ran sklearn
  `predict_proba` inside each of 10,000 bootstrap resamples (20M calls) and had burned
  89 minutes of CPU without finishing. Decisions are now computed once and the bootstrap
  resamples precomputed vectors; the same numbers complete in seconds. No threshold, frame,
  or estimand changed - this was a performance bug in the analysis, not a design change.

## What this does and does not establish

**Establishes:** on this reader (Qwen3.5-4B Q4), retriever (BM25), corpus (SQuAD), and
feature set (BM25 scores + question shape), a two-depth router gains nothing against static
`k=4`. Combined with the earlier P3 result (`-9.8%` capture on a 7-depth policy at `n=186`),
the negative now rests on two independent designs and two separate fresh samples.

**Does not establish:** that routing is impossible. The tested action set is `{1,4}` on
features that carry no precision signal. A policy with a reader-side probe is priced out
(about 34.8 J/correct against roughly 7.3 J/correct of headroom), and this run does not test
a wider depth grid, a different feature family, or a weaker baseline than `k=4`.

## G8-router checklist

| Criterion | Status |
|---|---|
| Eval gap reported | done, 3.80 pp [2.70, 5.00] |
| Capture >= 30% with CI lower bound > 0 | **not met**, 0.54% [-1.99, +3.29] |
| Accuracy-loss CI lower bound > -2 pp | met, +0.00 pp [-0.30, +0.30] |
| Depth histogram + AUC + calibration reported | done |
| Stop rule applied as written | done, gap < 10% |

**G8-router fires.** Per the frozen rule the outcome is a documented null, not a failure to
report.

## Artifacts

- `runs/squad_qwen4b_qc_router/` - `blocks_design.json`, `raw.csv`, `manifest.json`
  (local-only), registry row.
- `analysis/qc_router/` - `train.json`, `select.json`, `eval.json`, `eval_ci.json`.
- `scripts/39_qc_router_frames.py`, `40_qc_router_policy.py`, `41_qc_router_eval.py`.
- `configs/runs/squad_qwen4b_qc_router.toml`.
- Claims C-081, C-082.
