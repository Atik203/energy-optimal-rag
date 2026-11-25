# Phase 6 - inference repair

Derived from registered run rows; no new measurements, no gate changes.

## Cluster-robust contrast (A(4) - A(32))

- Mean -4.30 pp; iid SE 1.14 pp; cluster SE 1.13 pp.
- 1000 questions in 806 contexts; design effect 0.98.
- Cluster 95% CI [-6.51, -2.09] pp; one-sided lower -6.15 pp.

## Depth versus tokens

- Corr(k, prompt tokens) = 0.993.
- Depth model: R2 0.8878, BIC 30211.6.
- Token model: R2 0.9017, BIC 29290.0.

## Affine fit (k >= 1)

- a = 26.903 [25.854, 27.953] J; b = 2.149 [2.055, 2.243] J/passage.
- k=0 floor 14.59 J with 1/1000 correct.

## Cross-fitted selection

- Selected depths by fold: [4, 4, 4, 4, 4].
- Mean held-out savings 58.13% (SD 1.96); winner's curse 0.03 pp.

## Policy capture interval

- Capture -9.78% with 95% CI [-22.78, -1.75] on n=186; depths {'1': 182, '2': 3, '4': 1}.

## Gold-first subset

- 590 questions with gold at rank 1; A(1) = 0.6525, A(32) = 0.6153, diff 3.73 pp [0.73, 6.72].

## Three readers on identical questions

- Qwen3.5-4B (primary): A(4)-A(32) = -2.80 pp [-5.93, 0.33], n=500.
- Qwen2.5-1.5B: A(4)-A(32) = 2.00 pp [-1.46, 5.46], n=500.
- Llama-3.2-3B: A(4)-A(32) = 5.00 pp [1.63, 8.37], n=500.

