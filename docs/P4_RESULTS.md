# P4 Results — Theory validation and sensitivity

Descriptive only. P4 reuses registered raw CSVs; it does not re-adjudicate gates
and does not create a new confirmatory claim.

**Arms:** `squad_qwen4b_p1` (P1), `squad_qwen15b_p2` (Qwen2.5-1.5B),
`hotpot_qwen4b_p2` (HotpotQA), `squad_llama3b_p2` (Llama 3.2 3B, exploratory).
Outputs: `analysis/p4/p4.json`, `identity.csv`, `margin.csv`, `scoring.csv`.

## Coverage model

| Arm | `a0` | `p` | `R²` |
|---|---:|---:|---:|
| P1 SQuAD | 0.31 | 0.015 | 0.273 |
| Qwen2.5-1.5B | 0.25 | 0.007 | 0.151 |
| HotpotQA | 0.10 | 0.073 | 0.879 |
| Llama 3B | 0.34 | 0.008 | 0.097 |

The stylized coverage model `A(k) = 1 − (1 − a0)(1 − p)^k` fits poorly on three
of four arms and moderately on HotpotQA. The model is rejected as a general
description; the empirical curve remains the object.

## Monotonicity and the distractor counterexample

| Arm | Accuracy monotone? | Consequence |
|---|---|---|
| P1 SQuAD | Yes | Greedy search does not stop early on this curve |
| HotpotQA | Yes | No counterexample on this arm |
| Qwen2.5-1.5B | **No** | Greedy search can stop at a local optimum |
| Llama 3B | **No** | Greedy search can stop at a local optimum |

The Qwen and Llama arms are non-monotone, so the distractor counterexample is
present in the data. A greedy policy that stops at the first local minimum is
not safe; certification must search globally or test monotonicity first.

## Identity gaps

`Δ(k) = ε_J(k) − ε_A(k)` from the affine energy fit and the empirical accuracy
derivative. Positive gaps flag over-retrieval; the identity is local, so edge
depths use forward/backward differences.

| Arm | `Δ(2)` | `Δ(4)` | `Δ(8)` | `Δ(16)` | `Δ(max)` |
|---|---:|---:|---:|---:|---:|
| P1 SQuAD | +0.065 | +0.200 | +0.386 | +0.566 | +0.703 (32) |
| Qwen2.5-1.5B | +1.517 | +1.221 | +1.092 | +1.046 | +1.177 (32) |
| HotpotQA | −0.236 | +0.076 | +0.281 | — | +0.340 (10) |
| Llama 3B | +0.042 | +0.218 | +0.427 | +0.604 | +0.760 (32) |

P1, Qwen, and Llama show positive interior gaps at `k ≥ 4`, consistent with
over-retrieval. HotpotQA is negative at `k=2` and positive from `k=4`, so the
multi-hop arm has a different local structure. The identity does not establish a
global optimum on any arm.

## Margin and scoring sensitivity

`analysis/p4/margin.csv` reports the selected depth and savings at margins 2, 3,
4, 5, 6, 8, and 10 pp for each arm. `analysis/p4/scoring.csv` repeats the
selection under normalized EM, lenient span, and F1 ≥ 0.5. The selected depth is
rule-dependent on every arm, and no single scoring rule is treated as canonical.

## Certification curves

`analysis/p4/p4.json` contains `N*` for each feasible margin-selected depth. The
curves are descriptive break-evens, not deployment guarantees. On arms where
calibration failed (Qwen, HotpotQA, Llama), the energy side is uncalibrated, so
`N*` inherits that limitation.

## Recall × precision decomposition

A separate decomposition (`docs/RECALL_PRECISION.md`) shows `A(k)=R(k)Q(k)`.
Recall rises with depth while conditional reader precision falls on SQuAD and
Llama; the two-stage model RMSE is 0.015–0.024 versus 0.062–0.149 for the
one-stage coverage model. The one-stage model fits recall, not accuracy. This
explains the plateau and the Llama peak, and it explains why the P3 BM25 policy
fails: its features predict recall, not conditional reader precision.

## Conclusion

- The coverage model is not a general description of the accuracy curve.
- The distractor counterexample is present: two arms are non-monotone.
- The identity is a local diagnostic; it flags over-retrieval but cannot
  certify a global optimum.
- Conclusions do not depend on a single scoring rule, but the selected depth
  does.
