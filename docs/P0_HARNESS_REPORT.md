# P0 Harness Report — first golden run

**Date:** 2026-11-15
**Run:** `golden_squad_qwen4b_p0`
**Status:** **FAIL — P1 is blocked.**
**Purpose:** harness check only. This run is not confirmatory evidence and produces no
`claims_evidence.csv` claim.

## 1. What passed

| Check | Result |
|---|---|
| SQuAD preparation | **10,570 questions, 20,958 contexts, 45,651 passages** — exact pilot counts |
| Manifest | `status = verified`; source, questions, corpus, and split SHA-256 all rechecked |
| Split design | 200 P0 / 1,000 P1 / 500 replication / 200 boundary / 200 context / 150 tax; P0 disjoint from P1; nested arms disjoint |
| Sweep rows | **1,400 / 1,400** (200 questions x 7 depths) |
| Invalid rows | **0** |
| Nonces | **1,400 unique** 10-hex nonces |
| Depths | 200 rows at each of `k = 0,1,2,4,8,16,32` |
| Model reloads | 0 |
| Prompt ceiling | maximum 3,532 prompt tokens, below the 4,096 context |
| Registry | row recorded, then marked `invalid` because calibration failed |
| Run manifest | config hash, model digest, interpreter, idle, counts, and environment recorded |

Data checksums:

| File | SHA-256 |
|---|---|
| `data/raw/dev-v1.1.json` | `95aa6a52d5d6a735563366753ca50492a658031da74f301ac5238b03966972c9` |
| `data/raw/train-v1.1.json` | `3527663986b8295af4f7fcdff1ba1ff3f72d07d61a20f487cb238a6ef92fd955` |
| `data/processed/squad_questions.parquet` | `2e90a63a170a0b4d58a377be753ca8575ab41bdb4dabb9034152bb716a55b71e` |
| `data/processed/squad_corpus.parquet` | `43b1f3a099a950a7f18cf709cc7426d18e6a6e9c3485fcd6a85c71cdd3ce43b7` |
| `data/splits/squad_splits.json` | `e53de4eb2a1de06759f0683be148e9a2430ee45f34e21b0256b101fccfc337f6` |

## 2. Sweep measurements

Run window: 2026-11-14T18:30:04Z to 2026-11-14T18:49:31Z (19m27s). Reader
`qwen3.5:4b`, Q4, 4096 context; BM25 top-32; 45,651 passages; one RTX 3060 Laptop 6 GB.

| k | valid | invalid | correct | A(k) | J(k) J/query | E(k) J/correct |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 200 | 0 | 0 | 0.000 | 7.77 | inf |
| 1 | 200 | 0 | 90 | 0.450 | 15.18 | 33.73 |
| 2 | 200 | 0 | 96 | 0.480 | 16.69 | 34.77 |
| 4 | 200 | 0 | 101 | 0.505 | 19.80 | 39.21 |
| 8 | 200 | 0 | 103 | 0.515 | 27.13 | 52.68 |
| 16 | 200 | 0 | 111 | 0.555 | 42.41 | 76.41 |
| 32 | 200 | 0 | 105 | 0.525 | 76.15 | 145.05 |

`J(k)` is the ratio of sums over `j_total` (GPU + CPU retrieval proxy). `E(k)` uses the same
denominator as the preregistration: total joules over total correct answers.

Affine fit: `J(k) = 11.1023 + 2.0225 k`, `R² = 0.9941`.

### P0 anchor check

| Check | Observed | Pilot | Relative error | Tolerance | Result |
|---|---:|---:|---:|---:|---|
| `J(1)` | 15.18 | 17.98 | 15.6% | 10% | **FAIL** |
| `J(4)` | 19.80 | 25.10 | 21.1% | 10% | **FAIL** |
| `J(32)` | 76.15 | 89.55 | 15.0% | 10% | **FAIL** |
| `fit.a` | 11.102 | 15.74 | 29.5% | 10% | **FAIL** |
| `fit.b` | 2.022 | 2.283 | 11.4% | 10% | **FAIL** |
| `fit.R²` | 0.9941 | ≥0.95 | — | — | PASS |

The E anchors are also low: 33.73 vs 45.5, 39.21 vs 48.3, and 145.05 vs 157.1 J/correct.
Accuracy is lower at the top depth (0.525 vs 0.570) but higher at `k=1` (0.450 vs 0.395);
the P0 question draw is disjoint from the unavailable pilot IDs, so this is reported, not
gated.

## 3. Why the run failed

### 3.1 Block calibration

The first block run (cold, after a 120 s cooldown) stopped at `k=0`:

```
k=0 block factor 0.732 outside [0.8, 1.4]
```

A focused diagnostic then measured, with the same reader and sampler:

- stable idle: 14.924 W, CV 0.9%, n=276;
- per-query k=0 sum: 121.22 J (20 queries);
- warm back-to-back block: 169.69 J;
- warm block factor: **1.400**.

A second block run with a 20-query global warm-up and two discarded warm-ups per depth passed
`k=0` but stopped at `k=1`:

```
k=1 block factor 1.676 outside [0.8, 1.4]
```

The factor is therefore **bimodal**: 0.732 when the first short block starts cold, 1.400–1.676
when it runs warm. This is a thermal/window-state mismatch, not a threshold accident. The
pre-registered [0.8, 1.4] range is unchanged.

### 3.2 Idle baseline and thermal state

The sweep measured idle **after** warm-up: 17.027 W, SD 7.896 W, **CV 46.4%**, n=551. The
protocol expects a stable pre-run baseline and the pilot's CV was 10.4%. The diagnostic idle
before warm-up was 14.924 W, CV 0.9%. The code has since been changed to measure idle before
warm-up; this run predates that fix.

The GPU reached **90 °C** and **900 MHz**; the pilot reached 88.4 °C and 1003 MHz. Mean power
was 60.94 W. The sweep is therefore in a more throttled state than the pilot, while the block
diagnostic ran after cooling; the two states cannot be compared directly.

### 3.3 What this means

The 15–21% low `J` values are not explained by a slow reader: mean latency was 0.59 s and the
affine fit is excellent (`R² = 0.994`). The failure is in the **energy calibration**, not row
collection. Short queries (`k=0,1`) are the hardest: the 100 ms sampler and per-query window
miss a larger fraction of the power ramp/tail, and the back-to-back block runs at a different
thermal state. The block correction is supposed to absorb that difference, but it is outside the
pre-set range.

## 4. Decision

- **P0 FAIL. P1 does not start.** No confirmatory GPU hours are spent.
- The registry row is `invalid`; the raw run remains git-ignored.
- The block-factor range is **not** widened after seeing the outcome.
- The P0 analysis is uncalibrated and is retained only as failure evidence.

## 5. Required fix before a rerun

The next attempt must be a **new run ID** (`_r2`) after a documented measurement-protocol
amendment. Candidate fixes, to be pre-specified before the rerun:

1. Measure idle before warm-up (code fixed; not used by this run).
2. Run block calibration at the **same thermal steady state** as the sweep, or record the
   block temperature/clock and match the sweep window.
3. Extend the per-query window with a **measured post-query tail** (or a minimum window) so
   short depths capture the ramp; validate against the block before the full run.
4. Keep the block size and the [0.8, 1.4] factor range fixed unless a pre-run amendment
   justifies a change on measurement grounds.
5. Repeat the 5-question dry run and a one-depth block check before the 200-question run.

Until those checks pass, the honest status is: **the harness measures rows reliably, but it
does not yet reproduce the pilot's absolute energy calibration.**
