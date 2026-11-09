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
