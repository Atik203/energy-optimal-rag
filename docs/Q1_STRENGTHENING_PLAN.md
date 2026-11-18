# Q1 strengthening plan

Status: working plan, 2026-11-19. The experimental program is complete; this
plan strengthens the paper without changing the preregistered claim boundary.

## Already done

1. Reframed the P1 result as a **measurable accuracy cost** (two-sided 95% CI
   [-6.53, -2.07] pp; McNemar p = 0.0002) alongside the failed 5 pp bound.
2. Added the **margin-indexed certification frontier**: 5 pp needs ~7,100 pairs;
   only 10 pp clears at n = 1,000.
3. Added the **measurement-validity audit**: NVML per-query windows are
   sequence-dependent; replay is within 2% of constant-depth blocks; P2 energy is
   reported as a sweep/block range.
4. Released **sanitized per-query tables** (no text, gold answers, predictions,
   or nonces) so readers can rebuild the energy/accuracy tables.
5. Published the archive at DOI `10.5281/zenodo.24351059`; tag `v0.2.0`.

## Highest-value remaining work

### 1. Related work and framing (paper-only)

Add a Related Work section with verified citations for: adaptive/iterative
retrieval, context-length/distractor sensitivity, inference-time energy
measurement, GPU power-measurement methodology, preregistration/reproducibility
in ML, non-inferiority/equivalence, post-selection inference, selective
prediction/adaptive computation, and IR recall@k vs answer accuracy.

Rewrite the abstract to six moves and ~250 words; retitle away from
"Energy-Optimal" because the paper does not claim a universal optimum. Restructure
Results by claim (measurement validity, energy curve, decision, transportability,
adaptive bound, theory limits) rather than by project phase.

### 2. Theory: proofs and simulation

- State the identity and comparative statics as propositions with assumptions.
- Add a simulation study: synthetic `J(k)=a+bk` and `A(k)` curves, paired
  sampling, calibration bias, and selection; report coverage of the identity,
  bias of `E(k)`, and false-positive rate of the gate.
- Formalize the depth-common-factor invariance lemma: a multiplicative
  calibration error common to all depths cancels in `E(k)` and in depth ratios.

### 3. P3 diagnostic

Add per-depth AUC/calibration for the correctness model, a permutation baseline,
and one stronger policy class on identical features. If a fresh 500-question
SQuAD split is added, run a new sweep and use it as a clean P3 test; do not reuse
the existing test split.

### 4. Measurement follow-up

Run the probe/replay on P1, HotpotQA, and Llama to make the validity audit
multi-arm. Report the bounded savings table for every arm. Do not apply a
post-hoc factor to any registered run.

### 5. Optional new evidence

- Dense-retriever arm on the same 500 questions (needs explicit approval for a
  model download).
- Fresh 500-question SQuAD split for a clean adaptive-policy test.
- Larger-n replication (~7,100 pairs) is a registered follow-up, not this paper.

## Do not

- Do not re-threshold the 5 pp gate or promote exploratory margins.
- Do not apply a post-hoc calibration factor to registered runs.
- Do not reuse the P3 test split for a tuned policy.
- Do not claim a universal `k*`, adaptive gain, or 16k/H200 energy result.
