# P2 Results — Llama 3.2 3B exploratory reader (SQuAD v1.1)

**Run:** `squad_llama3b_p2` (`n = 500`, seven depths, same IDs as the Qwen
replication arm). Reader: `llama3.2:3b` (Ollama Q4_K_M, 4096 context).
Exploratory only: no H7 or gate adjudication. Completed 3,500/3,500 rows,
0 invalid.

## Accuracy (peaks at k=4)

| k | A(k) |
|---:|---:|
| 0 | 0.0020 |
| 1 | 0.4160 |
| 2 | 0.4580 |
| 4 | 0.4760 |
| 8 | 0.4660 |
| 16 | 0.4380 |
| 32 | 0.4260 |

Accuracy rises to `k = 4` then declines; the weaker reader does not benefit from
depth beyond 4–8 on this corpus.

## Energy measurement: calibration FAILED

Block calibration: **3 of 7 depths passed** (`k = 4, 8, 32`); `k = 0, 1, 2, 16`
failed the `[0.8, 1.4]` gate. Repeat CV passed (median 3.43%, max 18.41%).
Energy is uncalibrated and uncertified.

Affine fit (uncalibrated): `J(k) = 18.35 + 1.36 k`, `R² = 0.9907`.

## Conclusion

Exploratory arm only. No H7, no certification, no universal `k*`. The weaker
reader's optimum is shallower (k ≈ 4), consistent with the hypothesis that
reader strength shifts the accuracy curve, but this is descriptive.
