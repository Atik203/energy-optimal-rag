# Zenodo deposit

**Status:** metadata prepared; DOI not minted. No `ZENODO_TOKEN` is available in
the local environment, so the upload is a manual step.

## Files to deposit

- `energy-optimal-rag-code-v0.2.0.zip` (tracked code at the release tag)
- `energy-optimal-rag-raw-v0.2.0.tar.gz` (raw runs, raw datasets, processed
  parquet, analysis outputs; external backup at
  `G:\energy-optimal-rag-backup\2026-11-18\`)

Both checksums are in `docs/BACKUP.md`.

## Metadata

- Use `.zenodo.json` at the repository root. It matches `CITATION.cff` and the
  release title.
- Version: `0.2.0`
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
