# Decision Log

**Format:** one entry per decision that changes the repository, the experiment, or the claim.
Newest last. Each entry is immutable; a reversal is a new entry, not an edit.

---

## D-001 — Repository name is `energy-optimal-rag`

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The project needs a public, descriptive repository name distinct from the
  exploratory `green-computing-ideas` export and from the internal short name G2.
- **Decision:** Use `Atik203/energy-optimal-rag`, package `rag_energy`, local root
  `E:\PROJECT\energy-optimal-rag`.
- **Consequences:** The repo name states the object (retrieval depth) and the objective
  (energy), not the method (certification). The package name is short and importable. The
  internal short name G2 remains only in prose.

---

## D-002 — All project storage stays on `E:`

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The research workspace lives on `E:`, the machine has limited free space on
  `C:`, and raw data must not be mixed with the source-ideas workspace.
- **Decision:** Code, data, runs, and artifacts live under `E:\PROJECT\energy-optimal-rag`.
  The USB backup is the only off-volume copy. Nothing is written to `G:\PROJECT\tool-observation`
  or `E:\PROJECT\Research-Ideas`.
- **Consequences:** All paths in configs are relative to the repo root. A second machine needs
  the repo plus the git-ignored `data/` and `runs/` directories restored from the USB backup.

---

## D-003 — The static 2 pp claim is dead

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The pilot selected `k* = 32` at the pre-registered 2 pp EM margin, the grid
  boundary, with bootstrap `P(k* optimal) = 0.61 < 0.8`. The paired accuracy CI for `k = 16`
  includes the 2 pp floor. This is a power/margin failure, not evidence for a boundary
  optimum.
- **Decision:** Do not claim a static 2 pp-optimal retrieval depth. Report the pilot failure
  in the paper's results. Retain the 2 pp margin only as an estimation target.
- **Consequences:** The paper's static claim must be margin-indexed. A reviewer asking for
  "the optimal k" gets a conditional answer, not a universal one.

---

## D-004 — 5 pp non-inferiority is the primary decision

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** Under a 5 pp EM margin the pilot selected `k = 4` with 69.3% energy savings and
  `N* = 876`. The effect is large enough to matter and the margin is defensible as a
  deployment tolerance. The 1,000-question rerun is powered for 5 pp, not 2 pp.
- **Decision:** The primary analysis is a one-sided 5 pp EM non-inferiority test at `k = 4`
  versus `k = 32`, requiring at least 20% savings. The 2 pp margin is secondary and
  estimation-only.
- **Consequences:** No "5 pp certified" language before the rerun completes and the freeze is
  respected. The 2 pp result may be reported with a CI but may not be used to certify a depth.

---

## D-005 — Compute is local-only

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The project has a local RTX 3060 6 GB, a 15–20 GPU-hour budget, and a cash cap
  of $47. The pilot ran at 0.68 s/query on the 4B reader, so the rerun fits locally.
- **Decision:** No GPU rental, no paid API, no cloud inference. The only cash costs are a wall
  meter, a USB backup drive, contingency, and roughly $2 of electricity.
- **Consequences:** The paper's external validity is bounded by one laptop GPU. The budget is
  a feature: it forces a small, auditable measurement rather than a benchmark sweep.

---

## D-006 — No raw data, model weights, or secrets in the repository

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** SQuAD and HotpotQA are CC BY-SA 4.0; their text cannot be redistributed without
  compliance. Model weights are large and licensed separately. A public repo is scanned by
  both humans and bots.
- **Decision:** Track only `data/manifest.json`, `data/README.md`, `runs/registry.csv`,
  `artifacts/ledger.csv`, and `artifacts/claims_evidence.csv`. Git-ignore raw/processed text,
  model weights, run directories, `.env`, and credentials.
- **Consequences:** Reproducibility depends on the manifest and checksums, not on bundled
  data. A clean-room reproduction must re-download the upstream data.

---

## D-007 — The 78.8% oracle gain is an upper bound, not a result

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The pilot computed the oracle by choosing the cheapest correct depth per query
  with hindsight. No policy was trained. Reporting 78.8% as a learned-policy gain would be a
  fabricated result.
- **Decision:** Label 78.8% as an oracle upper bound in every document. The policy result
  requires the P3 held-out evaluation and the G4 gate.
- **Consequences:** The abstract may mention the oracle gap as motivation, but the results
  section must separate the oracle from the learned policy.

---

## D-008 — `prereg-freeze-v1` precedes the P1 confirmatory analysis

- **Date:** 2026-11-09
- **Status:** accepted (pending freeze)
- **Context:** The pilot showed how easily a margin choice can flip the verdict. The rerun
  needs a freeze that predates the new accuracy data.
- **Decision:** Tag the prereg commit `prereg-freeze-v1`. Analysis code records the prereg hash
  and refuses to run on a mismatch. Any change goes through `prereg/amendments.md` and a new
  entry here.
- **Consequences:** Exploratory analyses are allowed but must be labeled. A gate may not be
  re-thresholded after the primary outcome is seen.

---

## D-009 — One analysis population and failure rule

- **Date:** 2026-11-11
- **Status:** accepted
- **Context:** The documents defined the analysis population three different ways. Some treated
  a failed or empty generation as an invalid row, others treated it as a wrong answer, and some
  required a row at every depth before a question entered the analysis. The three definitions
  give different denominators and different paired `n`, so the rerun could not have one
  pre-specified estimand.
- **Decision:** Adopt one rule everywhere. The unit is a question. A **valid row** requires a
  non-empty nonce, a completed request, and a power window with no sampler error. A failed or
  empty generation after a completed request is a **wrong answer** (`correct = 0`) and is
  retained, not invalidated; a row is **invalid** only for a protocol violation: missing nonce,
  request/backend failure, or sampler error. Descriptive `A(k)`, `J(k)`, and `E(k)` use every
  sampled question with a valid row at depth `k`, and `n_valid(k)` and `n_invalid(k)` are
  reported at each depth. A question is not dropped from depth `k` because it has no row at
  another depth. The primary paired test uses questions with valid rows at both `k = 4` and
  `k = 32`; the paired `n`, the discordant counts, and the invalid counts are reported. There
  are no outcome-based exclusions: no winsorizing, trimming, or imputation, and wrong, slow, and
  throttled answers stay in.
- **Consequences:** Every table reports its denominator. Descriptive tables report
  `n_valid(k)` and `n_invalid(k)`; the primary table reports the paired `n`, discordant counts,
  and invalid counts. No result may be recomputed on a "complete cases only" population after
  seeing outcomes. This is a pre-freeze revision of the preregistration, not an amendment.

---

## D-010 — 5 pp pilot is a signal, not a certification

- **Date:** 2026-11-11
- **Status:** accepted
- **Context:** `README.md` described the 5 pp pilot result as "Pilot PASS — needs powered
  rerun", `ROADMAP.md` said `k = 4` was non-inferior in the pilot, and `docs/proposal.md`
  reported `P = .537` and called it a signal, not certified. If `P = .537` is the selection
  probability, it is below the G2 threshold of 0.8; no pilot non-inferiority test is reported
  either way. "PASS" overstated the evidence.
- **Decision:** Use **"pilot signal — not certified"** for the 5 pp pilot result. State that the
  proposal reports `P = .537` for the 5 pp selection. The rerun must report the non-inferiority
  test and the selection probability separately. Do not assert that G2 passed.
- **Consequences:** No "5 pp certified" or "G2 passed" language before the powered rerun
  completes and the preregistration is frozen and respected. The 69.3% savings and `N* = 876`
  remain pilot/descriptive quantities, not certifications.

---

## D-011 — Pilot evidence is transcribed, not reproducible in-repo

- **Date:** 2026-11-11
- **Status:** accepted
- **Context:** The pilot raw CSVs are not in this repository. The pilot numbers appear in
  `README.md`, `ROADMAP.md`, `docs/proposal.md`, the implementation plan, and the prereg, but
  none of them trace to a tracked raw file. A reader cannot recompute them here, and a paper
  claim without traceable evidence violates the project's evidence policy.
- **Decision:** Record every pilot claim in `docs/PILOT_EVIDENCE.md` with its value, source
  document, and status, and index the claims in `artifacts/claims_evidence.csv` with
  `run_id=pilot` and `artifact_path=docs/PILOT_EVIDENCE.md`. Add a ledger row for the evidence
  file with a computed SHA-256 and byte count.
- **Consequences:** The pilot rows are explicitly transcribed prior evidence, not a substitute
  for registered runs. The confirmatory run must produce `runs/<run_id>/raw.csv` before any
  confirmatory claim is made. A re-run is new evidence, not a reproduction of the pilot
  numbers.

---

## D-012 - Third reader is exploratory; H7/G5 stay fixed

- **Date:** 2026-11-14
- **Status:** accepted
- **Context:** The proposal has one confirmatory replication reader (Qwen2.5-1.5B) plus
  HotpotQA. Adding Llama 3.2 3B to H7 or G5 would create winner-selection freedom across three
  replication arms and would not increase per-reader power at `n = 500`.
- **Decision:** Add Llama 3.2 3B Instruct as an **exploratory reader panel**, using the same
  500 SQuAD IDs as the 1.5B replication, 4k context, Q4 via Ollama. H7 remains Qwen2.5-1.5B
  or HotpotQA. G5 remains unchanged. The panel is direction-only, has no gate, and is reported
  reader-conditionally.
- **Consequences:** The reader panel can test family robustness without changing the
  confirmatory family. It cannot certify 5 pp on its own and must not be promoted after seeing
  its direction. All readers are reported in one table; no reader selection.

---

## D-013 - Boundary context fix and diagnostic context probe

- **Date:** 2026-11-14
- **Status:** accepted
- **Context:** The existing boundary grid allowed `k=64` while inheriting a 4096 context;
  at 70 words/passage, the `k=64` prompt can exceed 4096 tokens and truncate. A separate
  16k allocation on Qwen3.5-4B is feasible on the 6 GB card at 100% GPU, while 32k already
  offloads to CPU. Quantized Llama 3.2 lightweight models have an 8k validated context, so
  Llama is not the 16k vehicle.
- **Decision:** Set the boundary grid to `num_ctx=8192`. Add a separate 16k context-budget
  probe: Qwen3.5-4B Q4, `n=200`, `k=32/48/64`, plus a `k=32 @ 4096` control. Label it
  diagnostic, not a 16k-token prompt or a new `k*`. Require 100% GPU residency; report CPU
  offload as a hardware limit. The optional H200 64k check is accuracy-only with no energy
  claim.
- **Consequences:** The `k=64` boundary endpoint is no longer silently truncated. The context
  probe can separate context-budget effects from depth effects, but it cannot support a
  "16k-context saturation" or energy claim. H200 results never enter the energy ledger.

---

## D-014 - P0 gates on J anchors and the affine fit

- **Date:** 2026-11-15
- **Status:** accepted
- **Context:** The repository documents pilot `E(k)` only at `k = 1, 4, 32`; `E(0)` is
  undefined, and a fresh 200-question draw can shift `A(k)` enough to move `E(k)` by roughly
  10% even when the harness is correct. The original "E(k) within 10% at every depth" is not
  adjudicable from tracked evidence.
- **Decision:** The P0 energy gate is `J(1)`, `J(4)`, and `J(32)` within 10% of 17.98, 25.10,
  and 89.55 J; affine `a` and `b` within 10% of 15.74 J and 2.283 J/passage; and `R2 >= 0.95`.
  `E(k)` and `A(k)` are reported with intervals but are not gated. If the pilot IDs are
  recovered, the E anchors become a secondary check.
- **Consequences:** ROADMAP, proposal, and implementation-plan wording was updated before the
  golden run. This is a harness check, not a confirmatory gate; it produces no
  `claims_evidence.csv` supported row. Do not re-threshold after seeing the golden data.

---

## D-015 - Sampling frame and tracked SQuAD ID splits

- **Date:** 2026-11-15
- **Status:** accepted
- **Context:** The pilot question IDs are not in the repository. The pilot corpus has 20,958
  unique contexts, which requires the SQuAD train and dev files together; dev alone has about
  2,067 paragraphs. The early configs did not define whether the replication and boundary
  samples were nested.
- **Decision:** Build the retrieval corpus from unique train+dev contexts. Sample 200 P0
  questions disjoint from 1,000 P1 questions; nest 500 replication questions inside P1; draw
  200 boundary questions inside P1 and disjoint from replication; reuse those 200 IDs for the
  4k/16k context probe; draw 150 tax questions inside P1 and disjoint from the other nested
  arms. Track IDs and per-split SHA-256 in `data/splits/squad_splits.json`, never raw text.
- **Consequences:** Run manifests identify the split by name, and reruns are reproducible
  without redistributing data. If the pilot IDs remain unavailable, disclose the expected
  overlap of roughly 19 of 1,000 questions (1.9%) and run a sensitivity analysis excluding any
  IDs that are later recovered; do not claim the pilot was excluded.

---

## D-016 - Wall-meter cross-check waived for P0/P1

- **Date:** 2026-11-15
- **Status:** accepted
- **Context:** No AC wall meter is available. A basic 0.01 kWh plug meter cannot resolve a
  30-query subset, and a cheap meter would add more uncertainty than it removes. The wall
  meter is a secondary whole-system check; NVML `power.draw` is the primary sensor.
- **Decision:** Waive the wall-meter cross-check for P0/P1. Use NVML with 20-query block
  calibration and the 3x20 repeat CV. Report "wall meter: not measured (waiver)" in the
  measurement table. If a meter is borrowed later, use it over a full run and report the
  system/GPU factor descriptively, never as a per-query correction.
- **Consequences:** No whole-system factor is reported, but the GPU-energy claim is unchanged
  and remains conditional on NVML calibration. The waiver is recorded in the run manifest and
  the P0 report.

---

## D-017 - Local harness uses the existing Python 3.12 Anaconda base

- **Date:** 2026-11-15
- **Status:** accepted
- **Context:** The named conda environment `energy-optimal-rag` is not present on the local
  machine. Creating it writes outside the repository and needs explicit approval. The existing
  Anaconda base is Python 3.12, has the package editable-installed, and passes the suite.
- **Decision:** Use the existing `C:\ProgramData\anaconda3\python.exe` for local P0/P1
  harness work. Record the executable and Python version in every run manifest. Keep the named
  environment as the documented clean-room target; create it only with approval.
- **Consequences:** Local runs are reproducible from the manifest even though the named
  environment is absent. A clean-room rerun must still use the documented environment file.

---

## D-018 - P0 golden harness check failed; P1 is blocked

- **Date:** 2026-11-15
- **Status:** accepted
- **Context:** The first golden run collected 1,400/1,400 valid rows with 1,400 unique nonces
  and the exact pilot corpus counts, but the J anchors were 15–21% low, the affine intercept
  was 29.5% low, and the slope was 11.4% low. Block calibration stopped at `k=0` factor 0.732
  when cold, and at `k=1` factor 1.676 after a block warm-up. The sweep idle CV was 46.4%,
  measured after warm-up, and the GPU reached 90 °C / 900 MHz. The block factor is bimodal
  with thermal state, not a stable correction.
- **Decision:** Mark the run `invalid`, do not start P1, and do not widen the [0.8, 1.4]
  block-factor range after seeing the outcome. Diagnose and pre-specify a measurement-protocol
  amendment, then rerun P0 under a new `_r2` run ID. P0 remains a harness check with no
  confirmatory claim.
- **Consequences:** The first P0 run is failure evidence, not a result. The raw CSV stays
  git-ignored; the analysis and this report are tracked. P1 GPU hours are held. The next run
  must demonstrate stable idle before warm-up, a block factor inside the pre-set range, and
  the J anchors before any P1 work.

---

## D-019 - P0 measurement protocol revision for the clean `_r3` rerun

- **Date:** 2026-11-15
- **Status:** accepted
- **Context:** The post-P0 audits found that the paired-window factor was a gap/tail
  allocation, so it could hide the sweep/block mismatch. The protocol factor must remain
  `J_block / sum(j_gpu_raw)` over the sweep rows. The 20-question dry runs showed that a
  post-query tail was needed to capture the power ramp/tail: 0.1 s still missed at `k=4`
  (1.476), 0.2 s missed at `k=16` (1.428), and 0.3 s passed all seven depths (0.834–1.380).
  The first clean-run attempt (`_r2`) was stopped after 409 rows because it started from a
  tree with uncommitted fixes.
- **Decision:** The clean `_r3` protocol is: measure idle before warm-up and abort if its CV
  exceeds 0.20; add `post_query_tail_s = 0.3` to both the sweep and block per-query windows;
  gate on `factor_csv = J_block / raw_sum_csv` in [0.8, 1.4]; record `factor_block` and
  `consistency = factor_block / factor_csv`; warm each block before measurement; apply the
  repeat cooldown at the start of every block. `_r2` is `aborted`; `_r3` is the clean run.
- **Consequences:** No claim or confirmatory threshold changed; this is a harness measurement
  amendment before the confirmatory freeze. P0 remains a harness check. P1 stays blocked
  until `_r3` passes the block-factor and J-anchor checks.
