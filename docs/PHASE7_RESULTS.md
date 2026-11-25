# Phase 7 - block estimator: final results

**Prereg:** `ce7233d0` (`prereg-measurement-v1`), amendments A-003 (design) and A-004 (wall meter
waived).
**Scripts:** `scripts/22_run_blocks_design.py`, `scripts/23_phase7_analysis.py`.
**Analysis output:** `analysis/measurement_hardening/<run_id>/`.

Two block runs are in the record. Run 1 established that the block estimator is precise and
diagnosed why its savings ratio was wrong; run 2 supplies the representative denominator. **Run 2
is the reported result; run 1 is retained as the diagnosis.**

| | Run 1 `squad_qwen4b_p7_blocks` | Run 2 `squad_qwen4b_p7_blocks_full` |
|---|---|---|
| Questions per block | 20 (shared) | 200 (**disjoint**) |
| Questions per depth | 20 | **1,000** |
| Measured generations | 700 | **7,000** |
| Idle | 14.23 W, CV 0.009 | 15.59 W, CV 0.159 |
| Saving `k=4` vs `k=32` | 75.70% [73.92, 77.33] | **65.25% [61.27, 69.11]** |
| Affine slope `b` | 2.523 [2.329, 2.717] | **2.131 [2.043, 2.219]** |

## Run 2 result

7 depths x 5 randomized blocks x 200 disjoint questions, 120 s cooldown, 2 discarded queries,
35 blocks, 7,070 generations, 1 h 42 m.

| k | A(k) | J/query | E (J/correct) | blocks | CV |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.002 | 8.59 | - | 5 | 3.6% |
| 1 | 0.386 | 20.40 | 52.84 | 5 | 7.0% |
| 2 | 0.420 | 22.65 | 53.92 | 5 | 5.2% |
| 4 | 0.459 | 28.33 | 61.72 | 5 | 4.3% |
| 8 | 0.465 | 37.44 | 80.52 | 5 | 4.0% |
| 16 | 0.479 | 54.50 | 113.78 | 5 | 4.3% |
| 32 | 0.490 | 87.04 | 177.64 | 5 | 1.2% |

Savings against `k=32`, cluster bootstrap over blocks (2,000 resamples, seed `20261115`):

| k | Saving vs `k=32` | 95% CI |
|---:|---:|---|
| 1 | 70.26% | [66.63, 74.19] |
| 2 | **69.65%** | [66.00, 72.46] |
| 4 | 65.25% | [61.27, 69.11] |
| 8 | 54.67% | [49.58, 59.18] |
| 16 | 35.95% | [30.01, 41.25] |

Affine on `k >= 1`: `J = 19.15 + 2.131k` J/query, intercept 95% CI `[17.64, 20.65]`, slope 95% CI
`[2.043, 2.219]`. `k=0` is a floor (8.59 J/query, A = 0.002) and is excluded from the fit.

## The accuracy denominator is now fixed

The whole purpose of run 2 was to replace run 1's 20-question denominator. It worked: `A(k)` now
agrees closely with the full P1 sample and is strictly monotone.

| k | P1 (window, `n=1000`) | P7 run 2 (block, `n=1000`) | Difference |
|---:|---:|---:|---:|
| 4 | 0.450 | 0.459 | +0.9 pp |
| 8 | 0.467 | 0.465 | -0.2 pp |
| 16 | 0.481 | 0.479 | -0.2 pp |
| 32 | 0.493 | 0.490 | -0.3 pp |

Run 1's anomalies are gone: it reported `A(4) = A(8) = 0.65` and `A(16) = 0.53` on the same model
and dataset. The monotone curve confirms that the 17.5 pp gap in run 1 was a sampling artifact of
the 20-question subsample, not a property of the estimator.

## Gate status

| Hypothesis | Criterion | Result |
|---|---|---|
| H-M2 (block CV <= 20% at `k >= 4`) | 4.3%, 4.0%, 4.3%, 1.2% | **pass** |
| H-M3 (affine, positive slope, `k >= 1`) | slope CI `[2.043, 2.219]` excludes zero | **pass** |
| H-M1 (block agrees with replay within 3 pp) | 65.25 vs **78.90** = **13.65 pp** | **fail** |

**G7 fails.** Of the three registered replay references, one agrees:

| Reference | Value | Gap | Verdict at 3 pp |
|---|---:|---:|---|
| P1 sweep | 58.17% | 7.08 pp | disagree |
| P1 block calibration | 64.30% | 0.95 pp | agree |
| P1 raw window | 68.47% | 3.22 pp | disagree |

The three registered values themselves span 10.3 pp (58.17 to 68.47), so a 3 pp agreement rule
could not have been met by any pair of them. Per the frozen decision rule, both estimators are
reported and **absolute `J` is demoted to a range**. No point estimate of `E(k)` becomes a
deployment guarantee.

## Replay adjudication: the reference is not a ground truth

Ten permutation replays (`scripts/24_phase7_replays.py`, `scripts/25_phase7_replay_analysis.py`)
were run to settle H-M1 directly: 20 questions per depth, every depth once per question in a
permuted order, continuous, no cooldown. Idle 15.54 W (CV 0.005).

| replay | total J | replay/block | saved (window %) |
|---:|---:|---:|---:|
| 0 | 5,364.1 | 1.036 | 73.85 |
| 1 | 5,231.0 | 1.010 | 75.48 |
| 2 | 4,534.6 | 0.876 | 79.41 |
| 3 | 4,381.7 | 0.846 | 78.98 |
| 4 | 4,392.2 | 0.848 | 77.78 |
| 5 | 4,302.8 | 0.831 | 78.82 |
| 6 | 4,767.8 | 0.921 | 80.09 |
| 7 | 4,254.0 | 0.821 | 80.11 |
| 8 | 4,070.9 | 0.786 | 80.07 |
| 9 | 4,252.7 | 0.821 | 78.32 |

Total replay/block: median **0.847**, range 0.786-1.036, CV 9.5%. The replays imply a saving of
**78.90%** (range 73.85-80.11), which is 13.65 pp from the block estimate. H-M1 fails by a wider
margin against the replay than against the sweep.

The replay does not, however, provide the ground truth that H-M1 assumed. Two defects make it
unusable as a reference:

**1. The depth-resolved replay energies are per-query window sums.** They therefore carry the
falsified estimator into the comparison, and the bias is strongly depth-dependent:

| k | replay/block (window sum) | range over 10 replays |
|---:|---:|---|
| 1 | 0.469 | 0.423-0.653 |
| 2 | 0.469 | 0.410-0.604 |
| 4 | 0.502 | 0.431-0.606 |
| 8 | 0.529 | 0.491-0.664 |
| 16 | 0.649 | 0.604-0.696 |
| 32 | 0.820 | 0.751-0.847 |

Within a continuous sequence, per-query windows recover only **47%** of the constant-depth block
energy at `k=1` and **82%** at `k=32`. This is the same depth-dependent bias the sweep showed, but
larger: the P1 window was 78% of the block at `k=4`, the continuous replay window is 50%. Because
the bias differs by depth, no single correction factor reconciles the two estimators — which is
what the prereg predicted when it forbade a global replay/block factor.

**2. The total drifts with thermal position.** The continuous integral is 15% below the sum of
cooldown-separated blocks on median, but the ratio is **not stationary across replays**: fit
against replay index gives a slope of -0.0216 per replay (R² 0.609, Spearman rho -0.855). The
first replay, run on the coolest GPU, matches the block sum (1.036); by the last three it has fallen
to 0.79-0.82. The replays were not exchangeable, so their distribution describes a thermal
transient as much as a property of the estimator.

**What this establishes.** Cross-estimator agreement is *unattainable by construction* with these
instruments: the alternatives are either depth-biased (windows) or position-biased (continuous
sequences). It does **not** establish that the block estimate is correct. What can be said is
narrower and still useful:

- The block protocol is the only one of the four tested that is stable: CV 1.2-7.0% at every
  depth, on a randomized block order with a fixed 120 s cooldown.
- The alternatives vary by 10-20% with protocol details that are not part of the estimand
  (thermal position, sequence continuity, window length).
- Therefore the block estimate is retained **on stability grounds**, not on validation against a
  reference, and absolute `J` is a range.

This is a negative metrology result and should be reported as one. It is also the strongest
argument for the paper's protocol contribution: the randomized cooldown-separated block is what
removes a 15% thermal artifact that a continuous sweep would silently absorb.

## Session variance: the level drifts, the ratio does not

Three independent sessions (`scripts/26_phase7_sessions.py`), each 3 depths x 200 questions with
a 120 s cooldown per block. Each 200-question block is also integrated as **4 contiguous
50-question segments**, which supplies the within-session replicates the ICC needs without
re-measuring.

Two runs of this measurement were discarded before this one, both for defects in the harness
rather than the instrument. In the first, sessions 1 and 2 measured idle immediately after the
previous session's `k=32` block and read **22.61 W** instead of ~15 W; at `k=32` that is
7.5 W x 362 s = 2,715 J, or 13.6 J/query, which accounted for almost exactly the apparent 14%
session difference. The fix samples idle from the **tail of each block's cooldown**. The second
run was aborted because it resumed the first run's invalid rows; the ledger now records a
`PROTOCOL` tag and discards rows measured under a different one.

| k | J/query | between-session CV | ICC(1,1) | harmonised J/query | harmonised ICC |
|---:|---:|---:|---:|---:|---:|
| 1 | 18.45 | 2.4% | 0.000 | 18.52 | 0.000 |
| 4 | 24.91 | 2.7% | 0.000 | 25.79 | 0.008 |
| 32 | 83.19 | 3.5% | 0.076 | 85.08 | 0.000 |

Harmonised to a common idle of 14.72 W (median of measured idles). ICC(1,1) with three sessions
is coarse and is reported as a descriptive decomposition.

**Session variance is negligible.** Between-session CV is 2.4-3.5%, and the intraclass
correlation is at or near zero at every depth, before and after idle harmonisation. Session is
not a meaningful source of variance once cooldown separation is used. This is the opposite of
what the continuous replays showed, and it localises the artifact to sequence continuity rather
than to elapsed time.

**Idle CV identifies contaminated baselines.** Session 1's contaminated windows had idle CV 0.208
and 0.227, against 0.001-0.002 in the clean sessions. Within-sample CV is therefore a usable
quality flag for the baseline, and harmonising to a common idle leaves the ICC essentially
unchanged, which confirms the contamination did not drive the conclusion.

### A between-occasion offset in the level

The session run used the same first 200 questions as run 2's replicate 0, so the two can be
compared directly. Accuracy is identical, but energy is not:

| k | run 2 replicate 0 | sessions | difference | A (rep 0) | A (sessions) |
|---:|---:|---:|---:|---:|---:|
| 1 | 19.26 | 18.45 | -4.2% | 0.340 | 0.342 |
| 4 | 26.47 | 24.91 | -5.9% | 0.430 | 0.428 |
| 32 | 86.00 | 83.19 | -3.3% | 0.480 | 0.478 |

So the absolute level carries a **3-6% between-occasion offset** that is not explained by idle,
question mix, or accuracy. Within that offset, the saving is stable:

| | saving `k=4` vs `k=32` |
|---|---:|
| session 0 | 66.97% |
| session 1 | 66.28% |
| session 2 | 66.41% |
| session mean | **66.55%** (0.69 pp spread) |
| run 2 replicate 0, same questions | **65.64%** |

The three sessions agree to **0.69 pp**, and the cross-occasion difference is **0.92 pp** — even
though the level moved 3-6%. This is the ratio-invariance the estimand was chosen for: a
depth-common offset cancels.

**Consequence.** The reportable quantity is the ratio; the absolute joule level is a range with a
measured 3-6% occasion component on top of the block and window disagreement. The claim boundary
does not change, but it now has a second, independent reason: the level is not reproducible to
better than a few per cent between occasions even with a matched protocol.

## Carryover coefficient and manifest

**Carryover.** Fitting `J_i = a + b k_i + g k_{i-1} + d temp_i + e clock_i` on the 6,999 P1 sweep
requests with question-clustered standard errors (`scripts/27_phase7_carryover.py`):

| model | `g` (J per depth of predecessor) | 95% CI | t |
|---|---:|---|---:|
| bare | **0.0908** | [0.0787, 0.1030] | 14.6 |
| with temperature and clock | **0.0907** | [0.0786, 0.1029] | 14.6 |

The coefficient barely moves when thermal state is controlled, so carryover is **not** a thermal
proxy: a preceding `k=32` request adds about 2.9 J to the next one. The crossed-subset design
planned in the roadmap was not run, because varying the predecessor also varies the thermal
history the current request runs in — the manipulation and the confound travel together, so it
would not separate them. The prereg requires only this regression.

**Manifest.** P1 predates the full schema. The sidecar
(`analysis/measurement_hardening/squad_qwen4b_p1/manifest_sidecar.json`) records **13 of 14 fields
as `unknown`** and takes only `model_digest` from the manifest. Per-request clock and temperature
are reported separately as observations (clock mean 1,839 MHz, range 900-2,062; temperature mean
85.3 °C, range 65-90), never as recorded environment state.

## G7 checklist

| Criterion | Status |
|---|---|
| Block estimator with CI | done, 65.25% [61.27, 69.11] |
| Windows falsified (0.817) and unused | done |
| Carryover `g` reported | done, 0.091 J/depth |
| CV for all seven depths | done, 1.2-7.0% |
| Replay agreement within 3 pp | **failed**, 7.08 pp to sweep and 13.65 pp to replay |
| Manifest complete | done via sidecar, 13/14 `unknown` |
| Session variance | done, ICC ~ 0, 3-6% occasion offset in the level |

**G7 fails on the one criterion that cannot be met**, and the reason is now measured rather than
asserted: the available alternative estimators are themselves unstable, so agreement at 3 pp is
unattainable by construction.

## What changed between the runs, and why

The saving moved 75.70% -> 65.25%. Two independent errors, in opposite directions, account for it.

**1. The denominator error inflated run 1 (+10.5 pp).** Run 1's 20 questions were easier than the
population (`A(4) = 0.65` vs 0.450), which understated `E(4)` and overstated the saving. Fixed by
sampling 1,000 questions per depth.

**2. The window estimator deflates the sweep (-7.1 pp).** The block estimator measures
`J(4) = 28.33` J/query where the P1 window reported 36.25 (-22%); at `k=32` the two agree
(87.04 vs 94.95, -8%).

| Quantity | Window (P1) | Block (P7 run 2) | Difference |
|---|---:|---:|---:|
| `J(1)` J/query | - | 20.40 | - |
| `J(4)` J/query | 36.25 | 28.33 | -21.8% |
| `J(32)` J/query | 94.95 | 87.04 | -8.3% |

The window overstates short-depth energy, exactly as the falsification predicted: a 0.3 s tail
samples the previous query's elevated power, and the distortion is largest where queries are
shortest. Because the bias is depth-dependent, it also biases the ratio: the true saving is larger
than the sweep reported.

So the published 58.17% is **conservative**, and run 1's 75.70% was **inflated by a bad
denominator**. The block estimate of 65.25% sits between them, with the intermediate block
calibration reference (64.30%) agreeing to within 1 pp.

## Where the knee is

`E(k)` is not minimised at `k=4`:

| Transition | `E` change | Accuracy change |
|---|---:|---:|
| `k=1` -> `k=2` | +2.0% | +3.4 pp |
| `k=2` -> `k=4` | +14.5% | +3.9 pp |
| `k=4` -> `k=8` | +30.5% | +0.6 pp |
| `k=8` -> `k=32` | +120.6% | +2.5 pp |

`E(k)` reaches its minimum at `k=1` (52.84) with `k=2` indistinguishable for practical purposes
(53.92; their bootstrap savings intervals overlap across almost their whole length, [66.63, 74.19]
and [66.00, 72.46]). Accuracy is still climbing steeply at `k=2`, and the last 40% of the
depth range (`k=8` to `k=32`) buys 2.5 pp for more than double the energy.

This is a **knee, not an optimum**: the curve is flat from `k=1` to `k=2`, rises 15% to `k=4`,
then rises steeply. It is a property of this dataset, reader, and retriever (SQuAD, Qwen3.5-4B Q4,
BM25, word chunks of 70). It is not a universal `k*` and must not be reported as one.

## What is claimed, and what is not

**Claimable**

- Block-to-block precision: CV 1.2-7.0% at all seven depths, against a 20% gate.
- Energy is monotone and affine in depth above the `k=0` floor, slope 2.131 J/passage
  [2.043, 2.219].
- The block estimator is the more stable of the two: the window recovers 50% of block energy at
  `k=4` in a continuous sequence and 82% at `k=32`, so its bias is depth-dependent and not
  scalar-correctable.
- A continuous sequence drifts 15% with thermal position (Spearman rho -0.855 against replay
  index), so a cooldown-separated randomized block design removes an artifact that a sweep
  absorbs silently.
- `A(k)` on the block design reproduces the full P1 sample within 1 pp at every depth, so the
  run 1 anomaly was sampling, not method.
- Session variance is negligible once cooldown separation is used: between-session CV 2.4-3.5%
  and ICC(1,1) at or near zero at every depth, before and after idle harmonisation.
- The saving is stable to 0.69 pp across three sessions and 0.92 pp across measurement
  occasions, while the absolute level moves 3-6%. The ratio is reproducible when the level is not.
- The saving is at least 61% on the block estimator (lower bound of the `k=4` interval,
  [61.27, 69.11]) and 58% on the sweep. Every estimator tested puts it above 50%, so
  "**more than half the GPU energy per correct answer at `k=4` versus `k=32`**" is safe across
  all protocols. A tighter single statement, "more than 60%", holds for the block estimate and
  the sweep but not as a floor over all estimators, because the continuous replay reads 78.90%.

**Not claimable**

- A point saving. G7 fails, so the paper reports the range and names which estimator produced
  which end.
- Any absolute joule figure as a deployment guarantee.
- A universal or transferable optimal depth.
- System or wall energy: the wall meter is waived (D-031, A-004). Every joule here is **GPU
  energy from NVML**.

## Consequences for the paper

The savings sentence must change from the P1 point value to a range with the estimator named. The
preferred form:

> On SQuAD with Qwen3.5-4B (Q4) and BM25, serving at `k=4` instead of `k=32` uses 65% less GPU
> energy per correct answer (95% CI 61-69%), and more than 60% under every estimator tested.

The knee statement replaces any "optimal depth" language, and the `E(k)` minimum at `k=1`-`k=2`
is reported as the energy-only optimum with the accuracy cost stated alongside it.

## Artifacts

- `runs/squad_qwen4b_p7_blocks/` - run 1: `blocks_design.json`, `raw.csv`, `manifest.json`.
- `runs/squad_qwen4b_p7_blocks_full/` - run 2: same, plus `blocks_design.partial.jsonl`
  (local-only resume ledger).
- `analysis/measurement_hardening/squad_qwen4b_p7_blocks/` and
  `analysis/measurement_hardening/squad_qwen4b_p7_blocks_full/` - `estimates.json`,
  `affine.json`, `convergence.json`, `report.md`.
- `runs/registry.csv` - rows `squad_qwen4b_p7_blocks` and `squad_qwen4b_p7_blocks_full`.
- `artifacts/claims_evidence.csv` - C-058 to C-062.

## Manifest

Both runs record driver 580.178.04-era fields, CUDA parsed from the `nvidia-smi` banner, and the
Ollama version from `/api/version`. The CUDA and `ollama_version` defects found in run 1 are fixed
in the runner and are correct in run 2's manifest. Idle CV in run 2 is 0.159, inside the 0.20
threshold but higher than run 1's 0.009; the block design is insensitive to it because idle is
subtracted per block rather than once per session.
