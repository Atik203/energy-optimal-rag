# P2 Results — HotpotQA distractor (multi-hop)

**Run:** `hotpot_qwen4b_p2` (`n = 500`, `k ∈ {0,1,2,4,8,10}`, prereg
`prereg-freeze-v1`, hash `fb9e5bcf…`). Reader: `qwen3.5:4b` (Ollama Q4, 4096
context). Retrieval: per-question BM25 top-10 over the 10 provided paragraphs
(A-002: only questions with exactly 10 paragraphs). Completed 3,000/3,000 rows,
0 invalid. Supporting-fact recall: mean 0.732 at k=4, 0.902 at k=8, 1.000 at
k=10.

## H7 direction replication: SUPPORTED

P1 observed `A(4) − A(32) = −4.30 pp` on SQuAD. On HotpotQA the contrast is
`A(4) − A(10)`:

- `A(4) = 0.4100`, `A(10) = 0.5180`, mean difference **−10.80 pp**.
- Paired `n = 500`; discordant `b = 12`, `c = 66`;
  `p_direction ≈ 1.0` (null: contrast ≥ 0).
- One-sided 95% upper bound: **−8.00 pp**.
- Point direction matches P1: **True**.
- **H7 supported: True** (whole directional interval negative).

The 5 pp test is secondary and not powered on this arm: lower bound −13.60 pp,
`p = 0.9997`, `non_inferior = False`. This is not a certification and does not
revive the P1 5 pp policy claim.

## Accuracy curve (monotone, multi-hop)

| k | A(k) |
|---:|---:|
| 0 | 0.0080 |
| 1 | 0.2000 |
| 2 | 0.2860 |
| 4 | 0.4100 |
| 8 | 0.4880 |
| 10 | 0.5180 |

Accuracy rises steadily with depth; `P(k* optimal)` concentrates at `k = 8`
(0.938) and `k = 10` (0.062). More paragraphs help on multi-hop questions,
unlike the SQuAD plateau.

## Energy measurement: calibration FAILED (k=0 only)

Block calibration: **6 of 7 depths passed** (`k = 1, 2, 4, 8, 10`); `k = 0`
failed (`factor_csv = 0.700`). Per protocol, no factor was applied, so
`j_gpu_calibrated = j_gpu_raw` and the energy table is **uncalibrated**.

Repeat CV: median 1.32%, max 6.77%, `passed = True` — a clean measurement
aside from the `k = 0` calibration miss.

Energy contrast (uncalibrated, not certified):

- `J(4) = 31.46` J/query, `J(10) = 51.65` J/query.
- Savings `1 − E(4)/E(10) = 23.03%` (95% CI 16.74–28.50%).
- Block-estimator bound: 31.4% (same accuracy).
- Affine fit `J(k) = 19.01 + 3.23 k`, `R² = 0.9992`, lack-of-fit
  `p = 0.0239`.

The savings point (23.03%) sits just above the 20% floor, but because calibration
failed on `k = 0` the contrast is not certified and must not be quoted as clean
energy. The measurement audit (D-028) gives a bounded range of **23.0–31.4%**;
both bounds clear the 20% floor, but the point value is not identified.

## Conclusion

- **H7 is supported on the HotpotQA arm.** The direction matches P1's negative
  contrast, with a strong effect (−10.80 pp, upper bound −8.00 pp).
- Together with the Qwen arm (H7 not supported), the P2 replication record is
  mixed: one arm supports H7, one does not. G5 (replication on the 1.5B reader
  **or** HotpotQA) is satisfied via HotpotQA.
- Energy on this arm is uncalibrated (`k = 0` miss) but repeat CV is clean.
- This does not change the P1 negative decision (D-024), does not certify 5 pp,
  and does not set a universal `k*`.

## Artifacts

- `analysis/hotpot_qwen4b_p2/` (estimates, fit, direction, bootstrap, metadata,
  p2, report).
- `runs/hotpot_qwen4b_p2/blocks.json` (`k=0` calibration miss documented).
- `runs/hotpot_qwen4b_p2/repeat.json` (repeat CV passed).
- `analysis/hotpot_qwen4b_p2_retrieval_recall.json` (supporting-fact recall).
