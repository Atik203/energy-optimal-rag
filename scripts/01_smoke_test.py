#!/usr/bin/env python
"""01 — Smoke test: version, config parse, and environment report.

Dependency-light by design. Safe to run before the environment is fully built.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy import __version__  # noqa: E402
from rag_energy.config import validate_all  # noqa: E402


def main() -> int:
    print(f"rag_energy {__version__}")
    print(f"python {sys.version.split()[0]} ({platform.platform()})")
    report = validate_all(ROOT)
    print(f"configs: {report.n_files} files")
    if not report.ok:
        for name, problems in report.errors.items():
            for problem in problems:
                print(f"FAIL {name}: {problem}")
        return 1
    print("configs: OK")
    print("smoke test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
