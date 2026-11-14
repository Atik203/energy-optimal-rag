# P0 calibration diagnostics

**Status:** historical failure evidence, not a result.
**Purpose:** archive the block-calibration numbers that motivated the P0 failure and the
subsequent harness fixes. These runs used the RTX 3060 Laptop and `qwen3.5:4b` Q4.

The first P0 run (`golden_squad_qwen4b_p0`, commit `7690bff`) is registered as `invalid`.
The raw CSV is git-ignored; this directory preserves the diagnostic numbers that are cited in
[`../../docs/P0_HARNESS_REPORT.md`](../../docs/P0_HARNESS_REPORT.md).

## Archived measurements

| Test | idle W | raw sum J | block energy J | factor | Notes |
|---|---:|---:|---:|---:|---|
| Cold first block, `k=0` | — | — | — | **0.732** | 120 s cooldown before the block; stopped by the [0.8, 1.4] guard |
| Warm-up rerun, `k=1` | — | — | — | **1.676** | 20-query global warm-up plus 2 discarded queries per depth |
| `diag_blocks.py`, `k=0` | 14.924 (CV 0.009, n=276) | 121.22 (per-query) | 169.69 | **1.400** | 20 back-to-back queries; no-gap per-query windows |
| `diag_blocks.py`, `k=0`, 0.2 s gap | 14.924 | 113.48 | 169.69 | **1.495** | A settle gap lowers the per-query sum and raises the factor |
| `diag_thermal_block.py`, `k=1` | 17.027 (sweep baseline) | 238.283 (first 20 sweep rows) | 381.75 | **1.602** | 120 warm `k=32` queries; hot block at 88 °C / 1732 MHz |
| Paired exact-window block, `k=1` | 14.892 | 179.687 (block windows) | 396.571 | **2.207** | Same-block windows; block duration 9.500 s |
| Tail 0.1 s, `k=4` | 15.597 | 403.158 (sweep) | 595.067 | **1.476** | `raw_sum_block=368.766`, `factor_block=1.6137`, consistency 1.0933 |
| Tail 0.2 s, `k=16` | 16.217 | 859.238 (sweep) | 1226.623 | **1.428** | `raw_sum_block=971.619`, `factor_block=1.2625`, consistency 0.8843 |
| Tail 0.3 s, all depths | 16.232 (CV 0.079, n=552) | — | — | **0.834–1.380** | Passed all seven depths; consistency 0.889–1.196; `_r3` candidate |

The 0.3 s tail passed the 20-question dry-run block calibration at every depth. The
[0.8, 1.4] range was not changed; 0.3 s is the pre-specified tail for the clean `_r3` run.

The `_r2` attempt was stopped after 409 rows because it started while the tail/factor fixes
were uncommitted. Its registry row is `aborted`; `_r3` is the clean rerun from a committed
HEAD.

## Reproduction

The two scripts in this directory reproduce the first two rows in the table:

```powershell
C:\ProgramData\anaconda3\python.exe analysis\p0_calibration_diagnostic\diag_blocks.py
C:\ProgramData\anaconda3\python.exe analysis\p0_calibration_diagnostic\diag_thermal_block.py
```

They are historical diagnostics, not the current runner. The block-command rows come from:

```powershell
python scripts\04_run_blocks.py --config configs\runs\squad_qwen4b_p0.toml --out runs\_diag4 --cooldown 0
python scripts\04_run_blocks.py --config configs\runs\squad_qwen4b_p0.toml --out runs\_dry2 --cooldown 0
python scripts\04_run_blocks.py --config configs\runs\squad_qwen4b_p0.toml --out runs\_dry3 --cooldown 0
```

The `_diag*` and `_dry*` directories are git-ignored working copies and are not evidence.
This README and the two scripts are the registered diagnostic artifacts (`artifacts/ledger.csv`
A-0006 through A-0008).

## What the table says

The factor is not stable under thermal/window changes: 0.732 when the first short block is
cold, 1.40–1.68 when warm, and 1.48–1.43 after adding 0.1–0.2 s of measured tail. That is why
P0 stopped: the [0.8, 1.4] block-factor guard is a real measurement check, not a formality.
The tail/paired-window fixes are protocol revisions to be validated on an `_r2` run; they are
not evidence that the first run passed.
