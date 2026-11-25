# Phase 8 - causal mechanism: dose-response + dense 2x2 (no router)

**Prereg:** `prereg-qc-v1` (`a501d7e3`), amendment A-005 (McNemar substitute).
**Design:** `docs/PHASE8_PLAN.md`. **Decisions:** D-034 (freeze), D-035 (Step 1 HALT),
D-036 (Step 2), D-037 (Steps 3b/4). Router dropped by owner decision 2026-11-26.

## Step 1 - fresh gap (gating)

`squad_qwen4b_qc_fresh`, 10 blocks, same 1,000 fresh qids at `k=1,4`:

| | A | J/query |
|---|---:|---:|
| k=1 | 0.389 | 19.04 |
| k=4 | 0.455 | 26.80 |
| oracle{1,4} | 0.485 | - |

Gap = **3.00 pp [2.00, 4.10]** (paired bootstrap): below the 10% stop threshold, so the
distractor position conditions were HALTED. Saving k=1 vs k=4 is 16.90% [-2.24, 32.28],
covering zero with 10 blocks — reported as measured. Fresh accuracy reproduces run 2
within 0.4 pp on disjoint questions.

## Step 2 - distractor dose-response (THE causal test)

`squad_qwen4b_qc_distractor`, 500 questions, gold held first:

| dose | k-equiv | accuracy [95% CI] | J/query |
|---:|---:|---|---:|
| 0 | 1 | 0.382 [0.340, 0.425] | 19.64 |
| 1 | 2 | 0.408 [0.366, 0.452] | 21.95 |
| 3 | 4 | 0.462 [0.419, 0.506] | 26.63 |
| 7 | 8 | 0.490 [0.446, 0.534] | 33.68 |
| 15 | 16 | 0.512 [0.468, 0.556] | 50.75 |
| 31 | 32 | 0.528 [0.484, 0.571] | 84.72 |

Repeated-measures trend: **+3.06 pp per doubling [1.43, 4.69]** (t at df=3).
**H-overload is REJECTED**: at fixed gold rank 1, distractors raise accuracy. The P1
precision collapse comes from gold displacement, not reader overload (bounded inference;
position tests were halted).

## Step 3 - dense 2x2

Frozen MiniLM rankings (`1110a243`, 45,651 passages), 1,000 fresh qids x `k in {4,32}`,
BM25 arm reused from run 2:

| arm | R(4) | R(32) | Q(4) | Q(32) | A(4) | A(32) |
|---|---|---|---|---|---|---|
| BM25 | 0.775 | 0.892 | 0.592 | 0.549 | 0.459 | 0.490 |
| dense | 0.711 | 0.884 | 0.620 | 0.559 | 0.441 | 0.494 |

**DiD = -2.20 pp [-5.40, +1.00]**: includes zero and exceeds the +-2 pp TOST band —
an inconclusive null, reported as a finding. MiniLM recall trails BM25 at both depths,
yet both arms rise with depth: **the knee does not travel with the retriever**.

## Step 4 - padding (token test)

200 fresh qids x 3 conditions:

| condition | accuracy | J/query |
|---|---:|---:|
| k=4 | 0.445 | 26.22 |
| k=4 padded to k=32 length | 0.485 | **75.93** |
| k=32 | 0.525 | 87.22 |

Padding recovers 87% of the k=32 energy cost: **energy follows prompt tokens, not
passage count**. The H1 affine fit is a token cost, hardware-grounded.

## What Phase 8 establishes

Three independent probes converge on a reader-side mechanism: gold-first distractors
help (+14.6 pp), the knee survives a retriever swap (DiD null), and length alone costs
nearly as much as real passages (87%). The reader handles extra context when the gold
is present early and pays per token regardless. No universal k*, no adaptive claim,
GPU energy only, absolute J a range.

## G8 checklist

| Criterion | Status |
|---|---|
| Fresh gap reported + stop rule applied | done, 3.00 pp, HALT |
| Causal contrast direction | done, trend +3.06 [1.43, 4.69], H-overload rejected |
| Dense DiD with CI and R/Q first | done, -2.20 [-5.40, +1.00], null finding |
| Padding contrast reported | done, 75.93 J/q |
| Router items | out by decision, not omission |

## Artifacts

- Runs: `squad_qwen4b_qc_fresh`, `squad_qwen4b_qc_distractor`, `squad_qwen4b_qc_dense`,
  `squad_qwen4b_qc_padding` (+ `distractor.json`/`padding.json` summaries).
- Analyses: `analysis/qc_fresh/`, `analysis/qc_distractor/`, `analysis/qc_dense/`.
- Frozen rankings: `data/processed/dense_minilm/` (manifest pinned to prereg rev).
- Claims C-070–C-078. Registry rows for all four runs.
