# Zenodo deposit

**Status:** published. DOI: **`10.5281/zenodo.24352803`**
(https://doi.org/10.5281/zenodo.24352803).

## Files deposited

- `energy-optimal-rag-v0.2.1.zip` (tracked code, paper PDFs, supplemental PDF;
  no raw text)
- Raw runs, raw datasets, processed parquet, and analysis outputs remain in the
  external backup at `G:\energy-optimal-rag-backup\2026-11-18\`; they are not in
  the public deposit.

The v0.2.0 checksums are in `docs/BACKUP.md`.

## Metadata

- Use `.zenodo.json` at the repository root. It matches `CITATION.cff` and the
  release title.
- Version: `0.2.1`
- License: MIT for code; SQuAD and HotpotQA remain CC BY-SA 4.0 and are not
  redistributed.
- Do not add raw question/context text to the deposit. The archive contains the
  raw parquet files for internal reproducibility only; if the deposit must be
  public, replace the raw archive with the tracked IDs, checksums, configs,
  predictions, and aggregate outputs.

## Manual steps

1. Create a Zenodo deposit and upload the two archives.
2. Paste the DOI into `CITATION.cff`, `.zenodo.json`, and `README.md`.
3. Re-tag `v0.2.0` only after the DOI is recorded; the current tag is
   `v0.2.0-rc1`.

## v0.3.0 (pending DOI)

**Archive:** `energy-optimal-rag-v0.3.0.zip` (10,388,890 bytes)
**SHA-256:** `b65411cee708e2d88db57dad5cc74d6251e5d18bac7c9aa225aea85c8680d306`
**Contents:** 501 tracked files from `main` at the release commit (code, configs,
preregs including `prereg-qc-v1`, registered analysis outputs, paper sources) plus
`paper/out/main.pdf` (30 pages, built from the same commit). No raw SQuAD/HotpotQA
text, no `raw.csv` with predictions, no parquet, no checkpoints, no credentials.
**What's new since v0.2.1:** Phase 7 block estimator (65.25% saving, G7 failed by
construction), Phase 8 causal mechanism (dose curve, dense DiD null, padding token
result), Phase 9 token attribution (25 mJ/prefill-token), 30-page manuscript with
the replay correction.
**DOI:** pending (this section completed after publish).
