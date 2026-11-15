# Preregistration freeze — `prereg-freeze-v1`

**Frozen:** 2026-11-15
**Tag:** `prereg-freeze-v1` (annotated; applied to the commit containing this file)
**Hash algorithm:** SHA-256 over the bytes of `PREREGISTRATION.md` followed by `analysis_plan.md`
**Prereg hash:** `fb9e5bcfe8d93404f64bbf62e04cacc13fdcfbbcbfae02ec3212c6e12affc49f`
**Analysis config:** `configs/analysis/prereg.toml` (`frozen = true`)
**P0 status at freeze:** FAIL — clean `_r3` sweep valid, `k=0` `factor_csv = 0.7944` below the
fixed 0.8 floor. P1 starts under D-022 as a PI reversal, not a gate pass.

The analysis script recomputes this hash and refuses to analyze a run whose manifest records a
different value. After this tag, any edit to `PREREGISTRATION.md` or `analysis_plan.md` requires
an entry in `prereg/amendments.md` and a mirror entry in `docs/DECISIONS.md`.

Recompute:

```powershell
C:\ProgramData\anaconda3\python.exe -c "import sys; sys.path.insert(0,'src'); from pathlib import Path; from rag_energy.runner import _prereg_sha256; print(_prereg_sha256(Path('.')))"
```
