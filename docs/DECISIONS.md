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
