# Clean-room reproduction check

- **Date:** 2026-11-18 (initial), re-run 2026-11-26 on `exp/phase10-repro`.
- **Source:** `git archive HEAD` (tracked files only), extracted to a fresh
  temporary directory.
- **Data:** copied `runs/`, `data/raw/`, and `data/processed/` into the clean
  tree; no repository-relative state was reused. (On the 2026-11-26 re-run the
  first copy nested runs as `runs/runs/` and misplaced processed data; fixed
  before measuring.)
- **Environment:** Python 3.12, project venv, same package set.

## Checks (2026-11-26, `exp/phase10-repro`)

| Check | Result |
|---|---|
| `pytest -q` | 483 passed (matches working tree) |
| `python -m rag_energy.cli validate` | all configs valid |
| `scripts/38_qc_token_attribution.py` | identical: R2 0.9575, 25 mJ/token |
| `scripts/33_qc_fresh_analysis.py` | identical: gap 3.00pp, saving 16.90% |

## Checks (2026-11-18)

| Check | Result |
|---|---|
| `pytest -q` | 350 passed |
| `python -m rag_energy.cli validate` | all 20 configs valid |
| `05_analyze.py` for P1, Qwen, HotpotQA | outputs match committed analysis |
| `07_train_policy.py` | outputs match |
| `11_p4_analysis.py` | outputs match after line-ending normalization |

The P4 files differ only by CRLF/LF; normalized SHA-256 values match. No
substantive output changed.

## Limit

This is a same-machine clean-room check. A second physical machine and a
second-site data copy remain part of the final `v0.2.0` release.
