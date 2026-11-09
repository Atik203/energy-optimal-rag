# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
