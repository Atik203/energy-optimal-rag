# Phase 7 plan - Metrology identification (block estimator and falsified windows)

**Precondition:** Phase 6 complete (`docs/PHASE6_RESULTS.md`, D-029).
**Exit gate:** G7 in `ROADMAP.md` section 5.
**Budget:** 5-8 GPU-h on the local RTX 3060, batch 1, no concurrent jobs.
**New prereg required:** `prereg/measurement_hardening_prereg.md`, frozen and tagged before any
Phase 7 outcome is read. This is a new study; it cannot amend `prereg-freeze-v1`.

## 1. Why the phase is needed

The Q1 audit established that the per-query energy estimator is not a partition of the run:

- replay total `7,336.9 J`, constant-depth block sum `7,195.7 J` (ratio 1.020);
- **per-query window sum `5,996.7 J` = 81.7% of the replay total**;
- `k=0` energy depends on the preceding depth by +24% (P1), +48% (Qwen1.5B), +22% (HotpotQA),
  +82% (Llama);
- the calibration factor is not depth-common (`k=0` 0.8089, `k=32` 1.0587).

A single replay/block ratio is one equation for seven unknown per-depth biases, and a global
factor cancels in the savings ratio while leaving the depth-specific bias intact. Phase 7
therefore replaces the estimator instead of correcting it.

## 2. Estimand

For depth `k` with `B` blocks of `Q` questions:

```
E(k)   = sum_b J_block(k, b) / sum_b C(k, b)
Sav    = 1 - E(4) / E(32)
```

`J_block(k, b)` is the integrated GPU energy over the block window minus the idle baseline
measured over the same window. `C(k, b)` is the number correct in that block. The interval is a
cluster bootstrap over blocks, with questions resampled inside blocks for the accuracy term.

Per-query windows remain diagnostic only.

## 3. Design

| Item | Value |
|---|---|
| Depths | `0, 1, 2, 4, 8, 16, 32` |
| Blocks per depth `B` | 5 (minimum), 7 if time allows |
| Questions per block `Q` | 20, the same 20 questions in every block |
| Block order | Randomized, fixed by a recorded seed |
| Cooldown | 120 s at the start of every block, logged |
| Discard | First 2 queries of each block, pre-specified |
| Replays `R` | 10 (exact sweep permutation plus different permutations) |
| Sessions | At least 3 sessions on the `k in {1,4,32}` subset for an ICC estimate |

Total: 7 depths x 5 blocks x 20 queries = 700 queries for the block design, plus 10 replays over
the 140-query permutation, plus the session and meter subsets. Estimated 5-8 GPU-h including
cooldowns.

## 4. Steps, in order

1. **Manifest schema first (0 GPU-h).** Add driver, CUDA, power mode, clocks, Ollama
   version/digest, model digest, HF cache revision, ambient temperature, throttle reasons,
   screen/AC state, batch size, and concurrency to the run manifest. Backfill a P1 sidecar with
   `unknown` for fields that were never recorded. Never fabricate a value.
2. **Freeze the prereg.** Write `prereg/measurement_hardening_prereg.md` with the estimand,
   design, exclusions, stop rule, and decision rules below; tag it.
3. **Smoke block (2 min).** `--smoke` runs one block of 3 questions at the first depth in a
   separate `_smoke` run directory, with no cooldown. This executes the measurement path
   end-to-end (sampler, integrator, JSON, manifest) before committing GPU hours.
4. **Pilot block (0.5 GPU-h).** One depth, two blocks, confirm the harness writes block windows
   and idle baselines correctly.
5. **Block sweep (2-3 GPU-h).** 7 depths x 5 blocks, randomized order, cooldown, discard rule.
6. **Replays (1-1.5 GPU-h).** `R = 10`; report the distributions of `replay/block` and
   `per-query sum/replay` with 95% CIs. Do not apply a global factor.
7. **Carryover regression (0 GPU-h, existing rows).** Fit
   `J_i = a + b k_i + g k_{i-1} + d temp_i + e clock_i` with cluster-robust SEs by question;
   report `g`. Add a crossed subset varying the predecessor over `{0,4,32}` for one target depth.
8. **Session variance (1 GPU-h).** Three sessions on `n = 200`, `k in {1,4,32}`; report ICC.
   The wall meter is waived (D-031): no meter will be purchased, so only GPU energy is reported.
9. **Analysis and report.** Block estimator, convergence table, CV distributions, affine fit on
    `k >= 1`; write `analysis/measurement_hardening/`.

## 5. Decision rules (frozen before the run)

| Outcome | Action |
|---|---|
| Block estimator CI excludes 0 and clears 20% on the savings ratio | This becomes the primary energy result |
| Block estimator and replay disagree by more than the pre-specified tolerance (3 pp) | Report the disagreement; demote all absolute `J` to a range |
| Per-depth CV exceeds 20% at `k >= 4` | Report the depth as not measurable; do not gate the paper on it |
| `k=0` factor again within 2% of the 0.8 floor | Report `k=0` as a floor only; exclude from every fit |

## 6. What Phase 7 must not do

- Do not patch P1 or P2 rows.
- Do not re-threshold K7 or any frozen gate.
- Do not quote an absolute joule figure as a result until the convergence rule passes.
- Do not run the Phase 8 sweep on the old estimator; the Phase 8 sample must be measured with
  whatever estimator Phase 7 certifies.

## 7. Deliverables

1. `prereg/measurement_hardening_prereg.md` + freeze tag.
2. `runs/<block_run_id>/raw.csv`, `blocks.json`, `manifest.json`, registry row.
3. `runs/<replay_run_id>/` and `runs/<session_run_id>/`.
4. `analysis/measurement_hardening/` JSON + report; updated validity figure.
5. `docs/PHASE7_RESULTS.md`; `docs/DECISIONS.md` entry; claims rows.
6. `paper/main.tex` energy-language pass (the deferred 6b edits): every absolute `J/E/N*/S(k)/a`
   becomes a range or a diagnostic.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Thermal drift across a 3 h run | Randomized block order, cooldown, log clock/temperature, drop-first-2 rule, session ICC |
| NVML ~1 Hz update under 100 ms sampling | Blocks are 20 queries, far above the sensor period |
| Time overrun | Reduce `B` from 7 to 5 and replays from 10 to 6 before touching the design |
