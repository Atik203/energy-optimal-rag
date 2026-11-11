# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Public research website under `web/` (Next.js App Router, React 19, Tailwind 4): home,
  research, method, pilot results, roadmap, and about pages plus a keyboard-driven slide deck.
- `docs/PILOT_EVIDENCE.md`: every pilot claim with its value, source document, and status, plus
  an explicit statement that the pilot raw CSVs are not in this repository.
- Stdlib-only unit tests for scoring, the ratio estimand and delta variance, affine fit,
  elasticity and identity gap, Holm, energy integration/idle/blocks/meter/nonce,
  chunking/splits/manifest, and BM25.
- `docs/DECISIONS.md` entries D-009–D-011, pilot claim rows in `artifacts/claims_evidence.csv`
  (`run_id=pilot`), and ledger row `A-0001` for `docs/PILOT_EVIDENCE.md`.

### Changed
- One analysis population and failure rule in README, implementation plan, protocol,
  preregistration, analysis plan, and proposal: failed or empty generations after a completed
  request are wrong answers and stay in; rows are invalid only for a protocol violation;
  descriptive statistics use valid rows at each depth; the paired test uses questions with valid
  rows at both `k = 4` and `k = 32`.
- 5 pp pilot language is now "pilot signal — not certified"; the proposal reports `P = .537` for
  the 5 pp selection, and the rerun must report the non-inferiority test and the selection
  probability separately.
- Policy split wording: 600/200/200 is a target; hashed per-question assignment can shift the
  realized counts, which are reported; there is no test-set tuning and the test split is
  evaluated once.
- Power planning default discordant rate is 0.08 in `scripts/06_power.py` and the `power.py`
  docstring; the stale 0.145 and 1.2 pp claim is removed.
- `delta_method_variance` now rejects negative energy and non-binary correctness, matching
  `ratio_of_expectations`; regression tests cover both cases.
- Configs: the boundary probe retrieves top-64; HotpotQA uses whole-paragraph retrieval; the
  analysis config validates the policy split against `n_questions = 1000`; Hugging Face
  replication dependencies are an optional `hf` extra.
- `prereg/PREREGISTRATION.md` and `prereg/analysis_plan.md` status lines record the 2026-11-11
  pre-freeze revision.

### Planned
- P0 golden reproduction of the 200-question pilot curve.
- P1 powered SQuAD run (`n = 1,000`, 7 depths, 5 pp non-inferiority primary).
- P2 1.5B replication, HotpotQA distractor, boundary probe, energy taxes.
- P3 query-conditional policy with a 600/200/200 split.

## [0.1.0] - 2026-11-09

### Added
- Initial public research-repository scaffold.
- Governance: README, ROADMAP, AGENTS, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT,
  CITATION.cff, MIT and CC BY 4.0 licenses, data-license policy.
- Installable `rag_energy` package with a standard-library-only config validator and CLI.
- TOML configs for base settings, SQuAD and HotpotQA runs, depth grids, energy taxes, and
  preregistration parameters.
- Data policy, manifest schema placeholder, run registry, artifacts ledger, and
  claims-evidence map.
- Documentation drafts: implementation plan, protocol, measurement, data card, risks,
  runbook, and decision log.
- Preregistration draft, detailed analysis plan, and amendment log.
- CI workflow for Python 3.12, issue templates, and pull-request template.
- Smoke tests that pass without numpy, pandas, torch, or a GPU.

### Notes
- No confirmatory results. The pilot is reported as MARGINAL.
- The static 2 pp claim is dead; 5 pp non-inferiority is the primary direction and has not
  been certified.
- The 78.8% oracle gain is an upper bound, not a learned-policy result.
