# Recall × precision decomposition

Descriptive mechanism analysis, 2026-11-19. No gate is changed.

Accuracy decomposes as `A(k) = R(k) · Q(k)`, where `R(k)` is the fraction of
questions whose answer evidence is in the top-`k` passages and `Q(k)` is the
conditional probability that the reader answers correctly given that evidence.
`analysis/recall_precision.json`.

| Arm | `R(1)` | `R(32)` | `Q(1)` | `Q(32)` | two-stage RMSE | one-stage RMSE |
|---|---:|---:|---:|---:|---:|---:|
| P1 Qwen4B | 0.590 | 0.892 | 0.663 | 0.553 | **0.017** | 0.137 |
| Qwen1.5B | 0.622 | 0.900 | 0.508 | 0.378 | **0.015** | 0.109 |
| Llama 3B | 0.622 | 0.900 | 0.669 | 0.473 | **0.021** | 0.149 |
| HotpotQA | 0.740 | 1.000 | 0.270 | 0.518 | **0.024** | 0.062 |

The one-stage coverage model is misspecified: it fits retrieval recall, not
accuracy. Recall rises with depth, while conditional reader precision falls on
SQuAD and Llama; their product produces the observed plateau. HotpotQA is the
opposite regime: both recall and precision rise because multi-hop questions
need the second supporting paragraph.

This explains three results at once. The SQuAD plateau is a precision decline,
not a retrieval ceiling. The Llama peak at `k=4` is a steeper precision decline.
The P3 policy fails because BM25 features predict `R`, not `Q`; the missing
signal is reader-side, not retrieval-side.

The two-stage model is descriptive and is not used for any decision. It is a
mechanism hypothesis, not a new gate.
