# Experimental Protocol

**Status:** draft for the P1 freeze · v0.1.0 · 2026-11-09
**Applies to:** SQuAD primary run, 1.5B replication, HotpotQA distractor run, boundary
probe, and energy-tax conditions.

This protocol is the operational companion to `docs/MEASUREMENT.md` and
`prereg/PREREGISTRATION.md`. Where they disagree, the preregistration wins for analysis and
this document wins for execution.

## 1. Design summary

| Condition | Dataset | n | Depths | Reader | Purpose |
|---|---|---:|---|---|---|
| Primary | SQuAD v1.1 dev | 1,000 | 0,1,2,4,8,16,32 | qwen3.5:4b | 5 pp non-inferiority |
| Replication | SQuAD v1.1 dev | 500 | 0,1,2,4,8,16,32 | Qwen2.5-1.5B-Instruct | Reader generalization |
| Distractor | HotpotQA distractor dev | 500 | 0,1,2,4,8,10 | qwen3.5:4b | Multi-hop/distractor stress |
| Boundary | SQuAD v1.1 dev | 200 | 32,48,64 | qwen3.5:4b | Resolve K2 |
| Fixed tax | SQuAD subset | 150 | full grid | qwen3.5:4b | `k*` increases |
| Per-passage tax | SQuAD subset | 150 | full grid | qwen3.5:4b | `k*` decreases |

The primary estimand is `E(k) = E[J_k] / E[C_k]`. The primary decision is 5 pp EM
non-inferiority at `k = 4` versus `k = 32`, with at least 20% energy savings. The 2 pp
margin is estimation-only.

## 2. Pre-run checklist

1. Confirm no other GPU job is running (`nvidia-smi`; no `DONE_*` flags from another run).
2. Confirm AC power, screen off, batch size 1, and the fixed power mode.
3. Record GPU model, driver, CUDA runtime, Ollama version, model digest, and Python version.
4. Record the prereg hash and the config hash in `runs/registry.csv`.
5. Build the BM25 index once and record its build time and passage count.
6. Run the 5-query smoke test; a failed smoke test aborts the run.
7. Measure the 60 s pre-run idle baseline.
8. Run 20 warm-up queries and discard them.
9. Check temperature and SM clock; if the GPU is already throttled, cool to the idle
   temperature before starting.

## 3. Run order and randomization

Questions are processed in a fixed order from the sampled ID list. Within each question, the
depth order is shuffled with the run seed. This makes thermal drift a within-question
nuisance rather than a between-depth confound.

Every request carries a unique 10-hex nonce at the start of the user message. The nonce is
generated per request, not per question. A request without a nonce is a protocol violation and
the row is marked invalid.

The run is split into two halves of 500 questions for the primary condition, with a forced
cooldown between halves. The halves are analyzed together; the split is an operational
break, not a design factor. If the GPU throttles, the block calibration runs at the throttled
steady state, which is the conservative deployment condition.

## 4. Per-query record

Each row in `runs/<run_id>/raw.csv` contains at minimum:

| Field | Meaning |
|---|---|
| `run_id` | Registered run identifier |
| `question_id` | Dataset question ID |
| `k` | Retrieval depth |
| `order_in_question` | Position after shuffling |
| `nonce` | Per-request nonce |
| `correct_em` | Normalized EM (0/1) |
| `correct_lenient` | Lenient span match (0/1) |
| `f1` | Token F1 |
| `prediction` | Model output |
| `gold` | Gold answer (git-ignored file only) |
| `j_gpu_raw` | Raw trapezoidal GPU integral, J |
| `j_gpu_calibrated` | Block-calibrated GPU integral, J |
| `j_retrieval_proxy` | CPU BM25 proxy, J |
| `j_total` | Calibrated GPU + proxy, J |
| `latency_s` | Wall time of the model call |
| `prompt_tokens` | Prompt tokens, if reported |
| `output_tokens` | Output tokens, if reported |
| `gpu_temp_c` | Temperature at call end |
| `sm_clock_mhz` | SM clock at call end |
| `power_mean_w` | Mean power over the call |
| `valid` | 0 if a protocol violation occurred |
| `invalid_reason` | Short code when `valid = 0` |

Raw predictions and gold answers stay in the git-ignored run directory. Aggregate rows go to
`artifacts/ledger.csv`.

## 5. Block calibration

After the main sweep, for each depth in ascending order:

1. Cool to a stable idle temperature.
2. Run 20 back-to-back queries using the first 20 question IDs at that depth.
3. Integrate the block as one window and subtract the pre-block idle baseline.
4. Compute the scale factor `block_total / sum(per_query_raw)`.
5. Write the factor, block duration, block energy, and pre/post idle power to `blocks.json`.

The calibrated per-query energy is `j_gpu_raw * factor`. Both raw and calibrated values are
retained. The analysis reports both; the calibrated value is primary.

## 6. Repeat and noise block

Three repetitions of 20 identical queries at `k = 8`, separated by short cooldowns. The
coefficient of variation is computed per query across repetitions (median and maximum). The
minimum detectable effect is approximated as `2 × CV`; if the observed energy effect is
smaller, the curve is reported as "not measurable" and K7 fires.

## 7. Energy-tax conditions

Each tax condition reuses the same questions and depths as the primary run's first 150
questions.

**Fixed tax.** A calibrated dummy matmul runs before generation, adding 20% of `a = 15.74 J`
(config: 3.148 J). It touches no prompt token and does not change the answer.

**Per-passage tax.** The same dummy work runs once per retrieved passage, adding 20% of
`b = 2.283 J` per passage (config: 0.457 J/passage).

Calibration is by repeated timing and energy integration until the target is within ±5%.
The tax is applied identically at every depth. The predicted direction is recorded before the
run: fixed tax increases `k*`, per-passage tax decreases it. The test is on the sign, with the
gated and unconstrained optima both reported.

## 8. Exclusions and invalidity

The unit is a question. A **valid row** requires a non-empty nonce, a completed request, and a
power window with no sampler error. A failed or empty generation after a completed request is a
**wrong answer** (`correct = 0`) and is retained, not invalidated; a row is **invalid** only for
a protocol violation: missing nonce, request/backend failure, or sampler error. Descriptive
`A(k)`, `J(k)`, and `E(k)` use every sampled question with a valid row at depth `k`, and
`n_valid(k)` and `n_invalid(k)` are reported at each depth. A question is not dropped from
depth `k` because it has no row at another depth. The primary paired test uses questions with
valid rows at both `k = 4` and `k = 32`; the paired `n`, the discordant counts, and the invalid
counts are reported. There are no outcome-based exclusions: no winsorizing, trimming, or
imputation, and wrong, slow, and throttled answers stay in.

- Do not exclude a slow or wrong answer. Wrongness is data.
- Do not exclude a throttled block. Throttling is recorded and analyzed as a covariate.
- A run aborted before completion is registered with status `aborted`; it is not deleted.

## 9. Stop rules

Stop the run and diagnose if:

- more than 2% of rows are invalid,
- the repeat CV exceeds 20%,
- the GPU clock drops below 50% of the starting clock and stays there,
- Ollama reports a prefix-cache hit on a nonce-bearing request,
- the block scale factor falls outside [0.8, 1.4],
- the wall meter disagrees with the integrated energy by more than 2×.

## 10. Post-run checklist

1. Confirm row counts: `n_questions × n_depths` plus repeats.
2. Confirm every depth has rows for every question, and record any missing rows with their
   invalidity reason.
3. Write `blocks.json`, `raw.csv`, and the run manifest.
4. Add the registry row with the config hash and git commit.
5. Copy the run directory to the USB backup.
6. Verify the checksums in `artifacts/ledger.csv`.
7. Only then run the analysis script.
