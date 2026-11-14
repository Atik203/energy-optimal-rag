# Measurement Protocol

**Status:** draft · v0.1.0 · 2026-11-09
**Scope:** GPU energy is the primary measurement; CPU retrieval is a proxy; the wall meter is
a cross-check. Absolute joule claims are conditional on the calibration described here.

## 1. What is measured

For a query `q` at depth `k`:

```
J_k(q) = J_ret_k(q) + J_pre_k(q) + J_dec_k(q) + J_fix(q)
```

- `J_ret` — BM25 scoring, index lookup, and fetch.
- `J_pre` — prefill of the query plus `k` passages.
- `J_dec` — decoding of the answer.
- `J_fix` — amortized model load and fixed per-query overhead.

The GPU sensor captures prefill and decode directly, plus part of the fixed overhead. BM25
runs on the CPU and is not captured by NVML; it is estimated by a time-to-joules proxy and
reported as an upper bound.

## 2. Primary sensor: NVML

- Library: `pynvml` (`nvidia-ml-py`).
- Field: `power.draw`, in watts.
- Cadence: 100 ms.
- Also recorded: `utilization.gpu`, `memory.used`, `temperature.gpu`, `clocks.sm`.
- Cross-check: `nvidia-smi --query-gpu=power.draw.average --format=csv,noheader,nounits
  -lms 100` on a short window.

**Resolution caveat.** The 100 ms cadence is a sampling label. On the pilot laptop the driver
updates `power.draw` coarsely, approximately once per second. Treat per-query energy as a
paired observation, not as a 100 ms precision measurement. Absolute energy depends on block
calibration and the repeat CV.

**Integration.** For each query, take the samples between the start and end of the HTTP call,
plus the configured `post_query_tail_s` (0.3 s for the P0 `_r3` protocol), apply the
trapezoidal rule, and subtract `idle_power_w × duration_s`. Clip at zero. The tail captures the
post-decode power ramp/tail that a window ending at HTTP completion misses; the same tail is
used in the block windows. Measure idle before warm-up, not after it, and stop if its CV
exceeds `idle_max_cv` (0.20). The pilot used a 60 s pre-run idle baseline (15.56 W, CV 10.4%)
and a 20 s post-run baseline (17.63 W, CV 15.9%). Using the post-run baseline lowers every
energy by about 4% almost uniformly and changes E ratios by under 1%.

```
J_gpu_raw(q) = max(0, trapz(power, time) - idle_power_w * duration_s)
```

## 3. Block calibration

Per-query windows miss the approximately 100 ms power ramp, most at short depths. After the
sweep, run 20 back-to-back queries per depth and integrate the block as one window. The
scale factor is:

```
raw_sum_csv_k = sum_i J_gpu_raw(q_i, k)          # sweep rows
factor_csv_k = J_block_k / raw_sum_csv_k          # protocol factor; gate [0.8, 1.4]
factor_block_k = J_block_k / sum_i W_block_i      # same-block window diagnostic
consistency_k = factor_block_k / factor_csv_k
J_gpu_calibrated(q, k) = factor_csv_k * J_gpu_raw(q, k)
```

The gate is `factor_csv_k`, not the within-block factor. A within-block factor is structurally
close to one and can hide a cold/warm sweep/block mismatch. `factor_block_k` and
`consistency_k` are recorded so that mismatch cannot disappear. The block is warmed before
measurement and its temperature/clock are reported.

Pilot factors:

| k | 0 | 1 | 2 | 4 | 8 | 16 | 32 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| factor | 1.041 | 1.100 | 1.188 | 1.128 | 1.118 | 1.081 | 1.073 |

The largest correction was at `k = 2`, where the per-query window is shortest relative to the
ramp. Both raw and calibrated values are stored. The minimum moves between `k = 1` and `k = 2`
by less than 1.1%, and the separation from `k ≥ 8` is unchanged.

## 4. CPU retrieval proxy

`pyRAPL` is unavailable on the Windows/AMD host. BM25 time is measured per query and
converted at 20 W single-thread active-above-idle:

```
J_ret_proxy(q) = t_bm25(q) * 20 W
```

Pilot mean BM25 time was 0.149 s/query, giving 3.11 J/query. At 10–15 W the term would be
1.6–2.3 J, lowering E by under 1.5%. This is an upper bound, and the retrieval-only share is
reported as a proxy share, not a measured share.

## 5. Prefix-cache control

Ollama reuses KV prefixes. In the pilot, a `k = 32` request following `k = 16` reused the
first 16 passages and cut prefill from 710 ms to 247 ms. Every request therefore carries a
unique 10-hex nonce at the start of the user message. The nonce is generated per request with
`secrets.token_hex(5)`. A missing nonce invalidates the row.

Verification: prefill time at a fixed depth should not drop when the previous request had a
shorter prefix. A drop is a protocol failure, not a speedup.

## 6. Thermal and clock control

The pilot observed temperature rising from 71.9 °C to 88.4 °C, SM clock falling from 1657 to
1003 MHz, and mean power falling from 82.5 W to 54.2 W. Energy (power × time) was stable.

Controls:

- Randomize depth within each question.
- Log temperature, clock, and throttle fraction for every query.
- Run block calibration at the throttled steady state.
- Cool between halves of a long run.
- Report the throttle fraction and a sensitivity analysis excluding the first 50 queries.

## 7. Repeatability

Three repetitions of 20 identical queries at `k = 8`, separated by short cooldowns. Apply the
cooldown at the **start of every block**, including the first, so all three blocks are measured
at the same thermal state. Compute the coefficient of variation per query across repetitions.
The pilot's median was **3.80%** and maximum **9.24%**. The minimum detectable effect is
approximated as `2 × CV`. If the observed effect is smaller, report "not measurable" and fire
K7.

## 8. Wall-meter cross-check

A plug-in wall meter (Kill A Watt class) measures whole-system energy on a 30-query subset per
condition. The meter reads watt-hours over the subset; the calibration factor is
`system_J / (GPU_J + CPU_proxy_J)`. A factor near 1 supports the integration. A factor far
from 1 means the integration omits a real system cost and must be reported, not hidden.

The wall meter is a cross-check, not the primary sensor: it cannot separate retrieval from
generation and it is too coarse for per-query attribution.

## 9. Derived quantities

- `A(k) = mean(C_k)` with `C_k ∈ {0,1}`.
- `J(k) = mean(J_k)` in joules per query.
- `E(k) = J(k) / A(k)` in joules per correct answer, computed as a ratio of sums.
- `S(k) = (J_ret(k) + J_pre(k)) / J(k)`, the context-side share.
- `S_r(k) = J_ret(k) / J(k)`, the retrieval-only share.
- `ε_J(k) = k J'(k) / J(k)`, from the fitted affine model.
- `ε_A(k) = k A'(k) / A(k)`, from finite differences.
- `N* = C_cert / (A(k*) [E(k_0) − E(k*)])`.

The context-side share is estimated from the per-passage GPU slope `b = 2.283 J`; the
retrieval-only share uses the CPU proxy. Do not conflate them.

## 10. Uncertainty

- 10,000 paired bootstrap resamples over questions.
- Percentile 95% intervals for `E(k)`, `A(k)`, `S(k)`, `k*`, and the identity gap.
- Bootstrap probability that each depth is optimal under the gate.
- Paired non-inferiority test for the primary 5 pp decision.
- Report raw and calibrated energy; report the pre- and post-run idle variants.

## 11. Reporting checklist

Every energy table states: sensor, cadence, idle baseline and its CV, block factors, repeat
CV, CPU proxy watts, wall-meter factor, GPU model, driver, power mode, and the reader/model
digest. A table missing these is not reproducible.

## 12. Context-budget and shared-hardware caveats

- The 16k context-budget probe sets `num_ctx=16384`; at 70 words/passage and `k ≤ 64`, the
  actual prompt is roughly 6k tokens. It is not a 16k-token prompt and cannot support a
  “16k-context saturation” claim.
- Record `prompt_tokens` and invalidate a row when `prompt_tokens + num_predict > num_ctx`.
- Require `ollama ps` to report 100% GPU and >300 MB headroom. CPU offload voids the arm; report
  the hardware limit instead of analyzing the row.
- Report `recall@k` and gold-answer-in-context at every depth; high-`k` accuracy can rise because
  the retriever finally reaches the gold context, not because the reader handles a larger window.
- The optional H200 MIG check is accuracy-only. Per-instance power telemetry is unavailable
  (`power.draw = N/A`); no H200 joules or `E(k)` may enter the ledger or any energy table.
- Shared-server results are a separate hardware condition and are never pooled with RTX 3060
  measurements.
