# P3 predictability audit

- OOF AUC for correct@1: **0.733** (n=1000).
- Learning curve: 50->0.707, 100->0.717, 200->0.695, 400->0.727, 608->0.724
- Answer-presence oracle: accuracy 0.4032, E/c 51.42, k=1 coverage 57.0%.
- Static k=1: accuracy 0.4194, E/c 59.57.
- Matched oracle: E/c 42.51.
- Answer-presence capture: 47.8%.

Exploratory only; the confirmatory G4 result is in analysis/policy.
