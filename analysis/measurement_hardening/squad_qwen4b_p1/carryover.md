# Phase 7 - carryover regression

Run `squad_qwen4b_p1`; 6999 requests, 1000 question clusters.

| model | gamma J per depth of predecessor | 95% CI | t |
|---|---:|---|---:|
| bare | 0.0908 | [0.0787, 0.1030] | 14.62 |
| with temp + clock | 0.0907 | [0.0786, 0.1029] | 14.64 |

R2: bare 0.9238, controlled 0.9242.

The predecessor sets the thermal state the current request runs in, so g is partly confounded with thermal history even with the controls. This bounds the carryover; it does not identify a pure effect.
