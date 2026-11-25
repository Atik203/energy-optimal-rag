# Phase 7 - session variance

Run `squad_qwen4b_p7_sessions`; 3 sessions, 200 questions per block, 4 segments of 50.

Idle across sessions: 14.64 W, 17.96 W, 14.60 W.

| k | J/query | between-session CV | ICC(1,1) | harmonised J/query | harmonised CV | harmonised ICC |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 18.45 | 2.4% | 0.000 | 18.52 | 3.4% | 0.000 |
| 4 | 24.91 | 2.7% | 0.000 | 25.79 | 3.8% | 0.008 |
| 32 | 83.19 | 3.5% | 0.076 | 85.08 | 1.1% | 0.000 |

Harmonised to a common idle of 14.72 W (median of measured idles).


ICC(1,1) with three sessions is coarse; it is reported as a descriptive decomposition, not as a precise variance component.
