# P2 Results — Qwen2.5-1.5B-Instruct replication (SQuAD v1.1)

**Run:** `squad_qwen15b_p2` (`n = 500`, seven depths, prereg `prereg-freeze-v1`,
hash `fb9e5bcf…`). Reader: `Qwen/Qwen2.5-1.5B-Instruct` (HF, Q4-equivalent,
revision `989aa798…`). Completed 3,500/3,500 rows, 0 invalid, 0 duplicate
`(question_id, k)` pairs.

## H7 direction replication: NOT supported

P1 observed a negative contrast `A(4) − A(32) = −4.30 pp`. On this arm:

- `A(4) = 0.3600`, `A(32) = 0.3400`, mean difference **+2.00 pp**.
- Paired `n = 500`; discordant `b = 44`, `c = 34`; `p_direction = 0.1287`.
- One-sided 95% upper bound on the contrast: **+4.90 pp**.
- Point direction matches P1's negative direction: **False**.
- **H7 supported: False.** The whole directional interval is not negative.

The 5 pp non-inferiority test is secondary and not powered on this arm:
lower bound −0.90 pp, `p = 3.68e-05`, `non_inferior = True`. Because the point
estimate is positive, this "non-inferiority" is not a replication of P1's
negative result and is not a certification.

## Accuracy curve (not monotone)

| k | A(k) |
|---:|---:|
| 0 | 0.0080 |
| 1 | 0.3160 |
| 2 | 0.3320 |
| 4 | 0.3600 |
| 8 | 0.3380 |
| 16 | 0.3660 |
| 32 | 0.3400 |

The curve peaks at `k = 16` (0.366) and does not show the P1 plateau; the
stronger reader does not flatten the curve in the predicted way.

## Energy measurement: calibration FAILED on this arm

Block calibration: **4 of 7 depths passed** (`k = 4, 8, 16, 32`); `k = 0, 1, 2`
failed the `[0.8, 1.4]` `factor_csv` gate (factors 0.261, 0.427, 0.537). Per
protocol, no factor was applied, so `j_gpu_calibrated = j_gpu_raw` and the
energy table is **uncalibrated**.

Repeat CV: median 3.03%, **max 80.15%** (threshold for a clean run is a max
well below the pilot's 18.44%); `passed = False`. The low-depth measurements are
dominated by sampling noise (queries shorter than the 100 ms NVML interval).

Consequently the energy contrast below is **not certified** and must not be
quoted as a clean energy result:

- `J(4) = 37.28` J/query, `J(32) = 401.83` J/query (uncalibrated).
- Savings `1 - E(4)/E(32) = 91.24%` (95% CI 89.93-92.36%).
- Block-estimator bound: 90.9% (same accuracy); the qualitative saving is robust.
- Affine fit `J(k) = −8.32 + 11.02 k`, `R² = 0.8507`, lack-of-fit
  `p = 0.0022` (poor fit, driven by the `k = 32` outlier).

## Conclusion

- **H7 is not supported on the Qwen2.5-1.5B arm.** The direction is opposite to
  P1's negative contrast.
- The energy measurement on this arm failed calibration and repeat CV, so no
  energy claim is made from it.
- This arm does not revive the P1 5 pp policy claim, does not set a universal
  `k*`, and does not change the P1 negative decision (D-024).
- The HotpotQA arm (`hotpot_qwen4b_p2`) is the remaining P2 confirmatory arm
  and has not yet been run.

## Artifacts

- `analysis/squad_qwen15b_p2/` (estimates, fit, direction, bootstrap, metadata,
  p2, report).
- `runs/squad_qwen15b_p2/blocks.json` (calibration failure documented).
- `runs/squad_qwen15b_p2/repeat.json` (repeat CV failure documented).
