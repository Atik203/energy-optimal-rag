# Contributing

Thanks for your interest in the energy-optimal retrieval depth project. This repository is a
research scaffold: correctness, traceability, and claim discipline matter more than feature
velocity.

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## 1. Setup

Requires Python 3.12. The experiments require a CUDA GPU and Ollama, but most contributions
do not.

```bash
git clone https://github.com/Atik203/energy-optimal-rag.git
cd energy-optimal-rag
conda env create -f environment.yml
conda activate rag-energy
pip install -e ".[dev]"
pytest -q
python -m rag_energy.cli validate
```

Windows PowerShell:

```powershell
git clone https://github.com/Atik203/energy-optimal-rag.git
Set-Location energy-optimal-rag
conda env create -f environment.yml
conda activate rag-energy
pip install -e ".[dev]"
.\tasks.ps1 test
.\tasks.ps1 validate
```

`requirements-lock.txt` is a placeholder until the lock is generated on the target machine
(`pip freeze > requirements-lock.txt`). Do not hand-edit pins.

## 2. What to work on

- Open or claim an issue before a large change.
- Good first contributions: docs, tests that do not need a GPU, config validation, scoring
  utilities, figure/table scripts.
- Do not start a new experiment without a registered config and a registry row. See
  `runs/README.md`.
- Do not change the preregistration after the freeze. See section 5.

## 3. Branch and commit conventions

Branch names: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`,
`exp/<run-id>`, `chore/<short-name>`.

Commits use Conventional Commits:

```
feat: add per-passage energy tax config
fix: keep nonce in prompt before passages
docs: define the ratio estimand
exp: register hotpot_qwen4b sweep
chore: add ruff to CI
```

Keep commits focused. Do not mix a refactor with a behavior change. Do not commit raw run
outputs.

## 4. Pull request checklist

Every PR must state:

- [ ] What changed and why.
- [ ] **Does this PR touch the preregistration, frozen data, or analysis code?** (yes/no)
- [ ] If yes: link the amendment in `prereg/amendments.md` and the decision in
      `docs/DECISIONS.md`.
- [ ] Tests added or updated; `pytest -q` passes.
- [ ] `python -m rag_energy.cli validate` passes.
- [ ] `ruff check .` and `ruff format --check .` pass (or the reason they were skipped).
- [ ] Docs updated for any behavior, command, or claim change.
- [ ] No secrets, raw data, model weights, or `runs/<run_id>/` files staged.
- [ ] If a result is reported: a `runs/registry.csv` row and the raw CSV exist, and the
      number is mapped in `artifacts/claims_evidence.csv`.

PRs that change analysis code without a prereg/amendment statement are returned.

## 5. Data and preregistration rules

- Raw SQuAD/HotpotQA text is never committed. `data/processed/` is git-ignored.
- Dataset versions, licenses, and checksums go in `data/manifest.json`.
- The preregistration freezes before the P1 confirmatory analysis (`prereg-freeze-v1` tag).
  After the freeze, changes require an amendment entry and a decision-log entry.
- Never re-threshold a gate after seeing the primary outcome.
- A result that does not trace to `runs/<run_id>/raw.csv` is not a result.

## 6. Tests

- `pytest -q` runs the fast suite. It must pass without numpy, pandas, torch, or a GPU.
- GPU/measurement tests belong behind an explicit marker and must not run in CI.
- A bug fix needs a regression test. A new analysis function needs a unit test on a small
  synthetic input with a known answer.
- Do not weaken a test to make a change pass. If a test is wrong, fix the test in its own
  commit with an explanation.

## 7. Code style

- Python 3.12, `src/` layout, package `rag_energy`.
- `ruff check` and `ruff format`; line length 100.
- Type hints on public functions and a docstring that states units.
- No notebook-only logic. Promote analysis code into `src/rag_energy/` or `scripts/`.
- Keep `cli.py` and `config.py` standard-library only.
- Do not add a dependency without updating `pyproject.toml`, `environment.yml`, and the
  lock note.

## 8. Reporting issues

Use the issue templates. For bugs, include:

- the command and config path,
- the Python version and OS,
- the GPU/driver and Ollama version if relevant,
- the smallest reproduction,
- the full traceback.

For a result dispute, include the run ID and the row in `raw.csv`. "The number looks wrong"
is not actionable without a trace.

## 9. Security

Do not open a public issue for a vulnerability or a leaked secret. Follow
[`SECURITY.md`](SECURITY.md).

## 10. License

By contributing you agree that code contributions are licensed under MIT and documentation
contributions under CC BY 4.0, as described in [`DATA_LICENSE.md`](DATA_LICENSE.md).
