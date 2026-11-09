## Summary

<!-- What changes, and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Experiment config or run registration
- [ ] Tooling / CI / chore
- [ ] Refactor (no behavior change)

## Research-impact declaration (required)

- **Does this PR touch the preregistration, frozen data, or analysis code?** Yes / No

If **yes**, link the amendment in `prereg/amendments.md` and the entry in
`docs/DECISIONS.md`. If the prereg is frozen and there is no amendment, this PR cannot merge.

- [ ] No claim, gate, or margin is changed.
- [ ] No raw data, model weights, secrets, or `runs/<run_id>/` files are included.
- [ ] If a result is reported, it traces to `runs/<run_id>/raw.csv` and is mapped in
      `artifacts/claims_evidence.csv`.

## Checklist

- [ ] `pytest -q` passes.
- [ ] `python -m rag_energy.cli validate` passes.
- [ ] `ruff check .` passes (or the reason is stated).
- [ ] Tests added or updated for behavior changes.
- [ ] Docs updated for behavior, command, or claim changes.
- [ ] Commit messages follow `feat:`, `fix:`, `docs:`, `exp:`, `chore:`.
- [ ] I ran a secret scan and reviewed `git status`.

## How to test

<!-- Exact commands and expected output. -->

## Notes for reviewers

<!-- Limitations, follow-ups, or a negative result that should be reported. -->
