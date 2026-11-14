# Runbook

**Windows-first.** Commands assume the repository root `E:\PROJECT\energy-optimal-rag` and the
conda environment `energy-optimal-rag`. POSIX equivalents are in the `Makefile`.

## 0. One-time setup

```powershell
Set-Location E:\PROJECT\energy-optimal-rag
conda env create -f environment.yml
conda activate energy-optimal-rag
python -m pip install -e ".[dev]"
python -m rag_energy.cli validate
pytest -q
```

Expected: every config prints `OK`, then `All configs valid.` and the smoke tests pass.

If conda is not on PATH, use the interpreter directly:

```powershell
C:\ProgramData\anaconda3\python.exe -m pip install -e ".[dev]"
C:\ProgramData\anaconda3\python.exe -m pytest -q
```

## 1. Smoke test

```powershell
python scripts\01_smoke_test.py
```

Expected: `rag_energy 0.1.0`, a Python/OS line, `configs: OK`, `smoke test: PASS`.

A failure here blocks every experiment. Fix the config or the install first.

## 2. Prepare data (P0)

```powershell
python scripts\00_prepare_data.py `
  --raw data\raw\dev-v1.1.json `
  --corpus data\raw\train-v1.1.json
```

Inputs must be downloaded from the official SQuAD source; do not commit them. The `--corpus`
file is required for the pilot-shaped corpus: dev alone has roughly 2,067 paragraphs, while
the pilot used 20,958 unique train+dev contexts and 45,651 passages.

Outputs:

- `data/processed/squad_questions.parquet`
- `data/processed/squad_corpus.parquet`
- `data/processed/squad_splits.json`
- `data/splits/squad_splits.json` (tracked IDs only)
- populated `squad` checksums and `status = prepared` in `data/manifest.json`

Verify the manifest before a run. A schema-only check is not enough; inspect the status and
the non-null checksums:

```powershell
python -c "from pathlib import Path; from rag_energy.data.manifest import load_manifest, validate_manifest; d=load_manifest(Path('data/manifest.json')); print(validate_manifest(d) or 'manifest schema OK'); [print(x['id'], x['status'], x['checksums']) for x in d['datasets']]"
```

## 3. GPU and reader check

```powershell
nvidia-smi
ollama list
ollama ps
```

Record the driver, GPU name, and model digest in `runs/<run_id>/manifest.json`; the registry
stores the model digest, not the full environment. Confirm `qwen3.5:4b` is present and that no
other job is using the GPU.

## 4. Run a sweep (P0)

```powershell
python scripts\02_run_sweep.py --config configs\runs\squad_qwen4b_p0.toml
```

Before the run, confirm:

- AC power, screen off, batch size 1, no concurrent GPU job.
- The nonce is enabled in the config (`nonce_hex_chars = 10`).
- The idle baseline is 60 s and the block size is 20.

Planned output: `runs\golden_squad_qwen4b_p0\raw.csv` plus `blocks.json`. The run directory is
git-ignored; the registry row is committed.

Register the run before starting it:

```powershell
$cfg = (python -c "from pathlib import Path; from rag_energy.config import resolve_run_config; print(resolve_run_config(Path('configs/runs/squad_qwen4b_p0.toml')).config_sha256)").Trim()
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$row = "golden_squad_qwen4b_p0,$ts,P0,squad,qwen3.5:4b,bm25,0|1|2|4|8|16|32,200,20261115,nvml,planned,$(git rev-parse --short HEAD),configs/runs/squad_qwen4b_p0.toml,$cfg,,TBD,runs/golden_squad_qwen4b_p0/raw.csv,golden harness check"
Add-Content -Path runs\registry.csv -Value $row -Encoding utf8NoBOM
```

Use the exact column order in `runs/registry.csv`. A malformed row breaks the registry. After
the run, update `status` to `completed` and fill `model_digest` from the run manifest.

## 5. Block calibration (P0)

```powershell
python scripts\04_run_blocks.py --config configs\runs\squad_qwen4b_p0.toml
```

Expected: `runs\<run_id>\blocks.json` with one factor per depth, and rewritten
`j_gpu_calibrated` / `j_total` columns in `raw.csv`. The pilot factors were 1.041-1.188. A
factor outside [0.8, 1.4] means the sensor window is unreliable; stop and diagnose.

Repeat the noise block at `k = 8`:

```powershell
python scripts\04b_repeat_cv.py --config configs\runs\squad_qwen4b_p0.toml --cooldown 120
```

Expected: `runs\<run_id>\repeat.json` with per-query CV, median/max CV, and the K7 pass/fail.

## 6. Energy taxes (P2)

```powershell
python scripts\03_run_taxes.py --config configs\taxes\fixed_a.toml
python scripts\03_run_taxes.py --config configs\taxes\per_passage_b.toml
```

Expected: two raw CSVs and a sign test. Fixed tax should move `k*` up; per-passage tax should
move it down. If either sign is wrong, record it as a falsification, not as a null result.

## 7. Analysis (P0/P1)

```powershell
python scripts\05_analyze.py --run-id golden_squad_qwen4b_p0
python scripts\05_analyze.py --run-id squad_qwen4b_p1
```

P0 writes `analysis\golden_squad_qwen4b_p0\`: `estimates.csv`, `p0_check.json`, and
`report.md`. P1 adds the planned `bootstrap.json`, `identity.csv`, `noninferiority.json`, and
`certification.json` outputs under `analysis\squad_qwen4b_p1\`.

The script must refuse to run if the prereg hash in the registry does not match the frozen
hash.

## 8. Power and policy (P1/P3)

```powershell
python scripts\06_power.py --margin 0.05 --discordant-rate 0.08
python scripts\07_train_policy.py --run-id squad_qwen4b_p1
```

The power table is a planning artifact. The policy script trains on 600, tunes on 200, and
evaluates once on 200.

## 9. Tables and figures (P5)

```powershell
python scripts\08_make_tables.py --run-id squad_qwen4b_p1
python scripts\09_make_figures.py --run-id squad_qwen4b_p1
```

Every table and figure records the run ID and config hash. Do not edit generated output by
hand; edit the generator.

## 10. Backup and release

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
Copy-Item -Recurse runs "E:\backup\energy-optimal-rag\runs-$stamp"
Copy-Item -Recurse artifacts "E:\backup\energy-optimal-rag\artifacts-$stamp"
Get-FileHash -Algorithm SHA256 runs\*\raw.csv
```

For a release:

```powershell
git tag -a v0.1.0 -m "v0.1.0 - Project scaffold"
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0 - Project scaffold" --notes "Initial scaffold. No confirmatory results." --prerelease
```

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: rag_energy` | Package not installed | `python -m pip install -e .` |
| `validate` fails on a config | TOML syntax or a required key | Read the error; fix the config, not the validator |
| Prefill time drops at fixed depth | Prefix cache hit | Confirm the nonce is in the prompt and unique per request |
| GPU power is flat at 15 W | Reader on CPU or idle | Check `ollama ps`; confirm 100% GPU |
| Block factor > 1.4 | Sensor window or idle baseline wrong | Re-run idle and blocks; check for concurrent jobs |
| Repeat CV > 20% | Thermal drift or a background job | Cool, close other apps, re-run the repeat block |
| `tests` pass but analysis fails | Missing optional dependency | `pip install -e ".[dev]"` and re-check |
| Raw CSV has missing depths | Run aborted | Mark the run `aborted`; do not silently complete it |

## Stop conditions

Stop and report if: more than 2% of rows are invalid, the repeat CV exceeds 20%, the GPU clock
stays below 50% of its starting value, a nonce-bearing request shows a prefix-cache hit, or the
wall meter disagrees with the integration by more than 2×.
