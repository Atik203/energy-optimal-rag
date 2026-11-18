# Clean-room reproduction check

- **Date:** 2026-11-18
- **Source:** `git archive HEAD` (tracked files only), extracted to a fresh
  temporary directory.
- **Data:** copied `runs/`, `data/raw/`, and `data/processed/` into the clean
  tree; no repository-relative state was reused.
- **Environment:** Python 3.12, project venv, same package set.

## Checks

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
