# P1 Confirmatory Results — `squad_qwen4b_p1`

**Status:** COMPLETE. The pre-registered 5 pp non-inferiority claim is **NOT SUPPORTED**.
**Run:** `squad_qwen4b_p1` (2026-11-15), commit `f73744c`, config `093521eb…`
**Prereg:** `prereg-freeze-v1`, hash `fb9e5bcf…`
**Design:** 1,000 SQuAD v1.1 dev questions × `k ∈ {0,1,2,4,8,16,32}`; qwen3.5:4b Q4;
BM25 top-32; RTX 3060 Laptop 6 GB; NVML 100 ms; 0.3 s post-query tail.
**Data:** 7,000/7,000 rows, 0 invalid, all 1,000 questions at all 7 depths.

This memo is the human-readable result. Every number traces to `runs/squad_qwen4b_p1/raw.csv`
or to a file under `analysis/squad_qwen4b_p1/`. No number here is hand-computed.

## 1. Measurement validity

| Check | Result |
|---|---|
| Idle baseline | 15.794 W, CV 1.23% (n=551) |
| Block calibration, all 7 depths | **PASS**; factors applied |
| Repeat CV at `k=8` | median 2.81%, max 18.44%, MDE 5.62% (threshold 20%) |
| Invalid rows | 0 / 7,000 |

Per-depth `factor_csv`:

| k | 0 | 1 | 2 | 4 | 8 | 16 | 32 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| factor | 0.8089 | 1.2506 | 1.2403 | 1.3111 | 1.2902 | 1.2143 | 1.0587 |

The `k=0` factor is only 1.1% above the fixed 0.8 floor; it passes, but it is the weakest
depth. The range is not widened and the factor is reported as measured.

## 2. Primary 5 pp result

Paired population: questions valid at both `k=4` and `k=32`, `n = 1,000`.

| Quantity | Value |
|---|---:|
| `A(4)` | 0.450 |
| `A(32)` | 0.493 |
| Mean difference `A(4) − A(32)` | **−4.30 pp** |
| One-sided 95% lower bound (analytic) | **−6.17 pp** |
| One-sided p (null `d ≤ −5 pp`) | 0.2691 |
| Two-sided 95% interval | **[−6.53, −2.07] pp** |
| Exact McNemar p (null `d = 0`) | **0.000216** |
| Discordant pairs `b / c` | 44 / 87 |
| Invalid rows at `k=4` / `k=32` | 0 / 0 |
| Energy savings `1 − E(4)/E(32)` | **58.17%** |
| Savings 95% interval | [56.02, 60.14]% |
| Decision | **NOT SUPPORTED** |

The point estimate is inside the 5 pp margin, but the one-sided lower bound is outside it.
The correct statement is: *non-inferiority is not established at 5 pp*; the data are also
compatible with a true loss larger than 5 pp. This is a precision failure at `n = 1,000`, not
proof that the true loss exceeds 5 pp. The 20% savings floor is met with a wide margin.

The same contrast is clearly nonzero: the two-sided 95% interval excludes zero and the exact
McNemar test gives p = 0.000216. The data therefore support a measurable accuracy cost from
depth reduction, while leaving the 5 pp bound unresolved.

The 2 pp secondary contrast has the same point estimate (−4.30 pp), lower bound −6.17 pp, and
p = 0.9785; it is estimation-only and is not a certification target.

## 3. Descriptive curve (calibrated)

| k | n | A(k) | J(k) J/query | E(k) J/correct | S(k) |
|---:|---:|---:|---:|---:|---:|
| 0 | 1,000 | 0.001 | 14.59 | 14,585.49 | 0.000 |
| 1 | 1,000 | 0.391 | 28.82 | 73.71 | 0.209 |
| 2 | 1,000 | 0.417 | 30.58 | 73.33 | 0.271 |
| 4 | 1,000 | 0.450 | 36.25 | 80.56 | 0.355 |
| 8 | 1,000 | 0.467 | 44.63 | 95.58 | 0.492 |
| 16 | 1,000 | 0.481 | 62.17 | 129.26 | 0.646 |
| 32 | 1,000 | 0.493 | 94.95 | 192.59 | 0.807 |

Affine fit: `J(k) = 24.0759 + 2.2772k`, `R² = 0.9714`; quadratic lack-of-fit
`F = 1.549`, `p = 0.2813`. **H1 is supported.**
Context share at the selected depth `k=4`: `S(4) = 0.355`, increasing with `k`. **H4 is supported.**

## 4. Hypothesis adjudication

| ID | Result | Evidence |
|---|---|---|
| H1 | **Supported** | `b = 2.277 > 0`, `R² = 0.971 ≥ 0.95`, lack-of-fit `p = 0.281 > 0.05` |
| H2 | **Not supported** | lower bound −6.17 pp < −5 pp; savings 58.17% ≥ 20% |
| H3 | **Not supported** | identity gap at `k=4` = +0.200, 95% CI [0.168, 0.232], excludes zero |
| H4 | **Supported** | `S(4) = 0.355` in [0.10, 0.70] and increasing |
| H5–H7 | Out of P1 scope | P3 policy, P2 replication |

H3 is a diagnostic failure, not a policy gate: the energy elasticity exceeds the accuracy
elasticity at `k=4`, so the identity's zero-gap condition does not hold at the selected depth.
The identity is reported as a diagnostic, not as proof of optimality.

## 5. Gates

| Gate | Value | Result |
|---|---|---|
| K1 relative energy effect | 1.613 (161%) | **PASS** |
| K2 boundary `k*` | `k=4` (interior) | **PASS** |
| K3 `P(k* optimal) ≥ 0.8` | 0.7244 | **FAIL** |
| K4 context share ≥ 5% | 0.355, not flat | **PASS** |
| K5 `k*` span ≤ 1 depth | 95% span 4 (`k=4`, `k=8`) | **FAIL** |
| K6 oracle gain | P3 analysis | not evaluated |
| K7 repeat CV ≤ 20% and MDE < effect | 18.44%, 5.62% < 161% | **PASS** |
| G1 5 pp non-inferiority + ≥20% savings | non-inferior false; savings 58.17% | **FAIL** |
| G2 loss upper bound ≤ 5 pp and `P(k*) ≥ 0.8` | 6.17 pp; 0.7244 | **FAIL** |
| G3 context share in [0.10, 0.70] and increasing | 0.355, increasing | **PASS** |
| G4 policy capture | P3 analysis | not evaluated |
| G5 replication | P2 analysis | not evaluated |

`P(k* optimal)` from the paired bootstrap: `k=2` 0.0237, `k=4` 0.7244, `k=8` 0.2433,
`k=16` 0.0086; all other depths 0.0. The 5 pp selection is not stable at the 0.8 threshold.

## 6. Certification cost

`N* = 6,189` queries (95% CI [5,697, 6,748]) at `k=4`, with `C_cert = 311,992 J` for the
sweep. This is a break-even calculation, not a deployment guarantee.

## 7. Sensitivity

Selected depth and savings by margin (EM):

| Margin | 2 pp | 3 pp | 4 pp | 5 pp | 6 pp | 8 pp | 10 pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| Depth | 16 | 8 | 8 | 4 | 4 | 2 | 2 |
| Savings | 32.9% | 50.4% | 50.4% | 58.2% | 58.2% | 61.9% | 61.9% |

At 5 pp, the selected depth is `k=4` under EM (58.2%), `k=8` under lenient span (49.9%), and
`k=8` under F1 ≥ 0.5 (50.6%). The qualitative statement "never the maximum depth" survives all
three rules, but the selected depth is rule-dependent.

## 8. Interpretation

- The pilot's 5 pp signal (69.3% savings, `P = .537`) did not replicate as a certifiable
  policy. The observed savings are 58.2%, and the accuracy point estimate is −4.3 pp, but the
  lower bound is −6.17 pp, so the 5 pp claim fails.
- The 2 pp claim remains dead. The 5 pp claim is now also not supported. There is no static
  depth that can be certified at either margin on this sample.
- The energy curve, affine fit, context share, calibration, and repeatability replicate. The
  static policy result is negative; the measurement and descriptive results are not.
- `K3` and `K5` fail: the selected depth is unstable between `k=4` and `k=8`, which is
  consistent with the flat accuracy region `k=4–16` seen in the pilot.
- `H3` fails: the identity gap at `k=4` is positive and excludes zero. The identity is a
  diagnostic; it does not certify an optimum.

## 9. What may and may not be claimed

**May be claimed:** the calibrated energy curve; the affine fit; the context-side share; the
measurement calibration and repeatability; the negative 5 pp result; the 58.2% savings as a
descriptive quantity.

**May not be claimed:** 5 pp non-inferiority; "certified" or "G1 passed"; a 2 pp optimum; a
universal `k*`; an adaptive-policy gain (P3 is untested); replication (P2 is untested).

## 10. What remains

- **P2:** Qwen2.5-1.5B replication and HotpotQA; boundary and 16k probes; energy taxes.
- **P3:** query-conditional policy; the static policy is dead, so the adaptive direction is
  the remaining route to a positive policy result.
- **P4:** theory validation, including the H3 failure.
- **P5/P6:** manuscript and release.

The raw run is local-only (D-020). The external backup should be made before P2 or any
machine change.
