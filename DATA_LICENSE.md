# Data and artifact licensing

This repository separates three layers. They are not interchangeable.

## 1. Code — MIT

All source code under `src/`, `scripts/`, `tests/`, and the build/config files are licensed
under the **MIT License**. See [`LICENSE`](LICENSE).

Copyright (c) 2026 Atikur Rahaman and contributors.

## 2. Documentation and derived artifacts — CC BY 4.0

Documentation, figures, tables, analysis reports, and derived data authored by this project
are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. See
[`LICENSE-DOCS`](LICENSE-DOCS).

This includes `docs/`, `prereg/`, `paper/`, `README.md`, `ROADMAP.md`, the aggregated
`artifacts/ledger.csv`, and `artifacts/claims_evidence.csv` where they contain only derived
values.

## 3. Upstream datasets — their own licenses remain in force

| Dataset | Version | Upstream license | Repository use |
|---|---|---|---|
| SQuAD | v1.1 dev | CC BY-SA 4.0 | Question IDs, retrieval configs, prompts, predictions, aggregate statistics |
| HotpotQA | distractor dev | CC BY-SA 4.0 | Question IDs, retrieval configs, prompts, predictions, aggregate statistics |

**CC BY-SA 4.0** includes a ShareAlike condition. If you redistribute adapted dataset text,
you must comply with that license. This repository does not redistribute raw SQuAD or
HotpotQA question/context text. It releases:

- dataset names, versions, splits, and source URLs;
- SHA-256 checksums of the files used;
- sampling seeds and question-ID lists where the upstream license permits;
- prompts, configs, and model predictions;
- aggregate counts, energy measurements, and derived statistics.

Raw text stays in `data/raw/` and `data/processed/`, both git-ignored. Do not add raw text to
a commit, a release asset, a Zenodo deposit, or a container image.

## 4. What we will not redistribute

- Full SQuAD or HotpotQA context/question text.
- Model weights (Ollama or Hugging Face).
- Credentials, tokens, `.env` files, or private query logs.
- Third-party figures or tables without permission.

## 5. Attribution

If you use the code:

> Atikur Rahaman and contributors, *Energy-Optimal Retrieval Depth in
> Retrieval-Augmented Generation*, MIT License,
> https://github.com/Atik203/energy-optimal-rag.

If you use the documentation or derived artifacts:

> Atikur Rahaman and contributors, *Energy-Optimal Retrieval Depth in
> Retrieval-Augmented Generation*, CC BY 4.0,
> https://github.com/Atik203/energy-optimal-rag.

If you use SQuAD or HotpotQA, cite the original dataset papers and follow their licenses.

## 6. Contact

Licensing questions: **atikurrahaman0305@gmail.com**. Security or leak reports: see
[`SECURITY.md`](SECURITY.md).
