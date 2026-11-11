# AGENTS.md — operating instructions for AI agents

This file is for any AI coding agent working in this repository. Read it before editing.
It is project-specific and overrides generic habits.

## 1. Read first

Before changing code or analysis, read:

1. `README.md` — claim boundary and current status.
2. `ROADMAP.md` — phases, gates, budget, out-of-scope items.
3. `docs/IMPLEMENTATION_PLAN.md` — the full design.
4. `docs/MEASUREMENT.md` — how energy is measured.
5. `prereg/PREREGISTRATION.md` — the analysis intent (draft until the P1 freeze).

If a request conflicts with the claim boundary, say so before implementing it. Do not
silently strengthen a claim, add a "certified" result, or introduce a universal `k*`.

## 2. Environment

- Python 3.12 at `C:\ProgramData\anaconda3\python.exe`.
- Conda environment: `energy-optimal-rag` (`conda activate energy-optimal-rag`).
- GPU: local RTX 3060 Laptop 6 GB. Single GPU, batch size 1, no concurrent jobs.
- Reader: Ollama `qwen3.5:4b` (Q4, 4096 context). Replication reader:
  `Qwen2.5-1.5B-Instruct` via Hugging Face.
- OS: Windows. Shell examples use PowerShell; `Makefile` is for POSIX/CI parity.
- Do not install CUDA toolkits, download model weights, or change the GPU power mode
  without asking.

## 3. Never commit

- `data/processed/` or any raw SQuAD/HotpotQA text.
- Model weights (`*.gguf`, `*.safetensors`, `*.bin`, `*.pt`, checkpoints).
- `.env`, tokens, API keys, credentials, Hugging Face tokens, GitHub tokens.
- Run directories `runs/<run_id>/` (raw CSVs, logs) except the documented registry.
- Large binary artifacts, parquet files, archives, or notebooks with outputs.

Tracked by design: `data/manifest.json`, `data/README.md`, `runs/registry.csv`,
`artifacts/ledger.csv`, `artifacts/claims_evidence.csv`. Do not git-ignore these.

Before any commit that touches data or configs, run a secret scan and `git status` to
confirm no raw data or model files are staged.

## 4. Preregistration discipline

- The preregistration is frozen before the P1 confirmatory analysis. After the freeze, do
  not edit `prereg/PREREGISTRATION.md` or `prereg/analysis_plan.md` directly.
- Any deviation goes in `prereg/amendments.md` with date, original text, replacement,
  reason, and whether outcome data had been seen.
- Mirror the deviation in `docs/DECISIONS.md`.
- Never re-threshold a gate after seeing the primary outcome. Label exploratory analyses as
  exploratory.
- The analysis script must record the prereg hash and config hash.

## 5. No fabricated results

Every number in a README, doc, table, figure, or paper must trace to a row in
`runs/<run_id>/raw.csv` or to a registered analysis output derived from it. If a number is
from the pilot and not yet reproduced, label it **pilot** and cite
`artifacts/claims_evidence.csv`.

Do not invent confidence intervals, p-values, effect sizes, run IDs, or dataset sizes. If a
result is missing, write `TBD` and open an issue.

## 6. Commands

```powershell
python -m rag_energy.cli validate
pytest -q
make test
.\tasks.ps1 test
.\tasks.ps1 validate
```

`validate` parses every TOML config with the standard library and checks required keys. It
must pass without numpy, pandas, or a GPU. The smoke test has the same constraint.

## 7. Code conventions

- Python 3.12, `from __future__ import annotations` where useful.
- `src/` layout; package `rag_energy`.
- Type hints on public functions; short docstrings that state units (J, J/correct, s).
- No hidden global state. Seeds come from config, not literals in functions.
- Energy values are joules; accuracy is a proportion in `[0,1]`; depths are integers.
- Prefer pure functions in `stats/` so they can be unit-tested without a GPU.
- Keep the CLI dependency-light: `cli.py` and `config.py` import stdlib only.
- Format with `ruff format`; lint with `ruff check`.

## 8. Commit conventions

Use Conventional Commits:

- `feat:` new capability
- `fix:` bug fix
- `docs:` documentation only
- `exp:` experiment config, run registration, or analysis output
- `chore:` tooling, CI, dependencies, scaffold

Examples:

```
feat: add block-calibrated NVML integrator
fix: subtract idle baseline before block scaling
docs: clarify 5pp non-inferiority estimand
exp: register squad_qwen4b_p1 sweep
chore: pin pytest in CI
```

Do not commit generated `runs/<run_id>/` data. Commit the registry row and the config.

## 9. Definition of done

A task is done only when all four hold:

1. **Code** — implemented, typed where public, and consistent with the config schema.
2. **Test** — a test that fails before and passes after, or a documented reason a test is
   impossible (e.g. GPU-only path) plus a manual check.
3. **Docs** — README/docs updated if behavior, claims, or commands changed.
4. **Ledger** — if the task produces a result, a row in `runs/registry.csv` and, where
   applicable, `artifacts/ledger.csv` and `artifacts/claims_evidence.csv`.

A PR that changes analysis code without a prereg/amendment check is not done.

## 10. When in doubt

- Preserve the claim boundary over adding features.
- Prefer a documented negative result over a tuned positive one.
- Ask before deleting or rewriting user work, especially under `prereg/`, `runs/`, and
  `artifacts/`.
- Stop and report if a command would download data, use a paid API, or write outside
  `E:\PROJECT\energy-optimal-rag`.
