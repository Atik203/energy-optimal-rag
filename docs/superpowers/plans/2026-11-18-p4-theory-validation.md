# P4 Theory Validation and Sensitivity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the optimal-depth identity, coverage model, certification-cost curve, and margin/scoring sensitivity across the P1, P2 Qwen, HotpotQA, and Llama arms, and document where the theory fails.

**Architecture:** Add a pure-Python `stats/p4.py` that reads registered raw CSVs through the existing loader, recomputes per-depth summaries, and emits one JSON/CSV/report bundle under `analysis/p4/`. Implement the missing `coverage_fit` in `stats/models.py`. Add a thin CLI script and tests for the model and the cross-arm summaries. No new GPU runs.

**Tech Stack:** Python 3.12, stdlib, existing `rag_energy.stats` modules, pytest.

**Spec:** `ROADMAP.md` P4; `docs/IMPLEMENTATION_PLAN.md` §10–§11.

## Global Constraints

- Energy is joules; accuracy is a proportion in `[0,1]`; depths are integers.
- Every number must trace to a registered `runs/<run_id>/raw.csv` or a derived `analysis/` file.
- Do not re-threshold gates or promote exploratory arms into H7/G5.
- P4 is descriptive/theory validation; it does not create a new confirmatory claim.
- Use `C:\ProgramData\anaconda3\python.exe`; `python -m rag_energy.cli validate` must pass.
- Do not commit `runs/<run_id>/` raw data.

## Review Focus

- A non-monotone accuracy curve (distractor counterexample) must be detected and reported, not forced into the coverage model.
- `coverage_fit` must be deterministic and bounded; it must not return a negative `p` or `a0 >= 1`.
- Identity gaps at grid edges must not be reported as interior optima.
- Margin sensitivity must use the observed `A(k)` and `E(k)`, not a refit that hides non-monotonicity.
- Scoring sensitivity must use the same rows and paired structure for each scoring rule.

---

### Task 1: Implement `coverage_fit`

**Files:**
- Modify: `src/rag_energy/stats/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: `coverage_accuracy(a0, p, k)`.
- Produces: `coverage_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]`, returning `(a0, p, r_squared)`.

- [ ] **Step 1: Write the failing test**

```python
def test_coverage_fit_recovers_a_known_curve():
    xs = [0, 1, 2, 4, 8, 16, 32]
    ys = [coverage_accuracy(0.3, 0.1, int(k)) for k in xs]
    a0, p, r2 = coverage_fit(xs, ys)
    assert abs(a0 - 0.3) < 0.05
    assert abs(p - 0.1) < 0.02
    assert r2 > 0.99
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\ProgramData\anaconda3\python.exe -m pytest tests/test_models.py::test_coverage_fit_recovers_a_known_curve -q`
Expected: FAIL with `NotImplementedError`.

- [ ] **Step 3: Implement `coverage_fit`**

Grid-search `a0` in `[0, 0.95]` and `p` in `(0, 1]` on a fixed grid, choose the pair minimizing squared error, then report `R²` against the mean of `ys`. Keep the grid deterministic (e.g. 0.01 steps for `a0`, 0.001 steps for `p`). Reject empty or mismatched inputs.

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\ProgramData\anaconda3\python.exe -m pytest tests/test_models.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/rag_energy/stats/models.py tests/test_models.py
git commit -m "feat: implement coverage model fit for P4"
```

---

### Task 2: Add cross-arm P4 summaries

**Files:**
- Create: `src/rag_energy/stats/p4.py`
- Test: `tests/test_stats_p4.py`

**Interfaces:**
- Consumes: `load_rows`, `summarize`, `affine_lack_of_fit`, `margin_sensitivity`, `scoring_sensitivity`, `certification_cost` from `rag_energy.stats.p1`; `coverage_fit` from `rag_energy.stats.models`.
- Produces: `write_p4_analysis(raw_paths: dict[str, Path], out_dir: Path) -> Path`, writing `p4.json`, `identity.csv`, `margin.csv`, `scoring.csv`, and `report.md`.

- [ ] **Step 1: Write the failing test**

```python
def test_p4_flags_non_monotone_accuracy(tmp_path):
    # synthetic raw CSV with A = 0.6, 0.9, 0.7, 1.0 at k = 0,1,2,4
    # write rows, call write_p4_analysis, assert monotone == False
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\ProgramData\anaconda3\python.exe -m pytest tests/test_stats_p4.py -q`
Expected: FAIL with `ImportError` or missing function.

- [ ] **Step 3: Implement `p4.py`**

For each arm: summarize rows, fit affine energy, fit coverage model to `A(k)`, compute identity gap at each interior depth using central differences, run margin sensitivity at `[0.02,0.03,0.04,0.05,0.06,0.08,0.10]`, run scoring sensitivity over `em`, `lenient`, `f1>=0.5`, and compute `N*` for each feasible margin. Record `monotone` as `all(A[k+1] >= A[k])`. Do not raise on a non-monotone curve.

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\ProgramData\anaconda3\python.exe -m pytest tests/test_stats_p4.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/rag_energy/stats/p4.py tests/test_stats_p4.py
git commit -m "feat: add P4 cross-arm theory validation"
```

---

### Task 3: Add the CLI runner and produce `analysis/p4/`

**Files:**
- Create: `scripts/11_p4_analysis.py`

**Interfaces:**
- Consumes: `write_p4_analysis`.
- Produces: `analysis/p4/` for `squad_qwen4b_p1`, `squad_qwen15b_p2`, `hotpot_qwen4b_p2`, `squad_llama3b_p2`.

- [ ] **Step 1: Add the script**

Parse `--root` and `--out`; map arm names to `runs/<run_id>/raw.csv`; call `write_p4_analysis`; print the output path.

- [ ] **Step 2: Run it**

Run: `C:\ProgramData\anaconda3\python.exe scripts\11_p4_analysis.py`
Expected: writes `analysis/p4/` and prints the path.

- [ ] **Step 3: Inspect and record**

Read `analysis/p4/report.md`; confirm the distractor counterexample status and any identity failures are explicit. Commit the analysis outputs.

- [ ] **Step 4: Commit**

```bash
git add scripts/11_p4_analysis.py analysis/p4
git commit -m "exp: produce P4 theory validation outputs"
```

---

### Task 4: Documentation, paper, and claim boundary

**Files:**
- Create: `docs/P4_RESULTS.md`
- Modify: `README.md`, `ROADMAP.md`, `paper/main.tex`, `paper/supplement.tex`, `paper/writing-support/PROJECT_BRIEF.md`, `artifacts/ledger.csv`, `artifacts/claims_evidence.csv`

- [ ] **Step 1: Write `docs/P4_RESULTS.md`** with the identity table, coverage fit and R², monotonicity status, margin/scoring sensitivity, and certification curves. Mark all P4 results descriptive.
- [ ] **Step 2: Update README/ROADMAP** with P4 status and a one-line result.
- [ ] **Step 3: Add a short P4 paragraph/table to the paper and supplement.** Do not change the claim boundary: P4 validates or limits the theory; it does not rescue the 5 pp or adaptive claims.
- [ ] **Step 4: Add ledger/claims rows** for `analysis/p4` and `docs/P4_RESULTS.md`.
- [ ] **Step 5: Verify and commit**

Run: `C:\ProgramData\anaconda3\python.exe -m pytest -q`; `C:\ProgramData\anaconda3\python.exe -m rag_energy.cli validate`; compile paper. Commit and push.

---

### Task 5: Final verification

- [ ] **Step 1: Run the full suite** (`pytest -q`) and config validation.
- [ ] **Step 2: Confirm `git status` is clean** except ignored run data.
- [ ] **Step 3: Push the branch and update PR #2** with the P4 bullet.
