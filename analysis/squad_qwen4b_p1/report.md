# P1 confirmatory analysis - squad_qwen4b_p1

Calibration: **applied** (all depths passed: True).

| k | n_valid | n_invalid | A(k) | J(k) J/query | E(k) J/correct | S(k) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1000 | 0 | 0.0010 | 14.59 | 14585.49 | 0.000 |
| 1 | 1000 | 0 | 0.3910 | 28.82 | 73.71 | 0.209 |
| 2 | 1000 | 0 | 0.4170 | 30.58 | 73.33 | 0.271 |
| 4 | 1000 | 0 | 0.4500 | 36.25 | 80.56 | 0.355 |
| 8 | 1000 | 0 | 0.4670 | 44.63 | 95.58 | 0.492 |
| 16 | 1000 | 0 | 0.4810 | 62.17 | 129.26 | 0.646 |
| 32 | 1000 | 0 | 0.4930 | 94.95 | 192.59 | 0.807 |

Affine fit: `J(k) = 24.0759 + 2.2772 k`, R² = 0.9714.
Quadratic lack-of-fit: F = 1.549, p = 0.2813; H1 supported: True.

## Primary 5 pp result

- Paired n = 1000; discordant b = 44, c = 87; invalid rows at k=4/k=32 = 0/0.
- Mean difference A(4) - A(32) = -4.30 pp (one-sided 95% lower bound -6.17 pp).
- McNemar exact p (no-difference null) = 0.0002158; continuity-corrected z p = 0.000243.
- One-sided p = 0.2691; non-inferior: False.
- Energy savings = 58.17% (pre-registered floor 20%).
- Decision: NOT SUPPORTED.

Selected depth at the 5 pp gate: k = 4.
Bootstrap P(k* optimal): {"0": 0.0, "1": 0.0, "2": 0.0237, "4": 0.7244, "8": 0.2433, "16": 0.0086, "32": 0.0, "none": 0.0}.
N* at the selected depth: {"selected_depth": 4, "reference_depth": 32, "total_sweep_j": 311992.064094, "delta_e_per_correct": 112.02238526640072, "n_star": 6189.0817298515, "note": "Break-even calculation, not a deployment guarantee.", "feasible": true, "interval": {"lower": 5697.140897034105, "upper": 6747.789380933609, "n_inf": 0, "n_missing": 0}}.

## Gates

| Gate | Value | Passed |
|---|---|---|
| K1 | {"value": 1.612912572095203, "passed": true} | True |
| K2 | {"selected_depth": 4, "boundary": false, "fired": false, "passed": true} | True |
| K3 | {"p_k_optimal": 0.7244, "passed": false} | False |
| K4 | {"context_share": 0.35464522104240853, "flat": false, "passed": true} | True |
| K5 | {"span_95": 4, "depths_95": [4, 8], "passed": false} | False |
| K6 | {"note": "oracle gain is a P3 analysis", "passed": null} | None |
| K7 | {"repeat_cv_max": 0.184353, "relative_effect": 1.612912572095203, "passed": true, "note": null} | True |
| G1 | {"non_inferior": false, "savings_pct": 58.16738530915217, "interior": true, "passed": false} | False |
| G2 | {"upper_bound_on_loss_pp": 6.170223024283287, "p_k_optimal": 0.7244, "passed": false} | False |
| G3 | {"context_share": 0.35464522104240853, "low": 0.1, "high": 0.7, "increasing": true, "passed": true} | True |
| G4 | {"note": "policy capture is a P3 analysis", "passed": null} | None |
| G5 | {"note": "replication is P2", "passed": null} | None |
