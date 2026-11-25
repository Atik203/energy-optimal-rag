#!/usr/bin/env python
"""29 - P1 manifest sidecar backfill.

The P1 manifest predates the full environment schema, so several fields were never
recorded. This writes a sidecar that lists every required field and either takes it from
a traceable source or marks it ``unknown``.

Nothing is inferred into a claimed value. Where a quantity is visible in ``raw.csv`` it
is reported under ``derived_from_raw`` and labelled as an observation, not as a manifest
field. A field that the run never wrote stays ``unknown`` even when it is obvious from
the code, because an obvious value is still a reconstruction.

Writes ``artifacts/manifests/<run_id>.manifest.sidecar.json``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEFAULT_RUN_ID = "squad_qwen4b_p1"

REQUIRED_FIELDS = (
    "driver_version",
    "cuda_version",
    "power_mode",
    "gpu_clock_mhz",
    "ollama_version",
    "ollama_digest",
    "model_digest",
    "hf_cache_revision",
    "ambient_temperature_c",
    "throttle_reasons",
    "screen_state",
    "ac_state",
    "batch_size",
    "concurrent_jobs",
)


def _observed(raw: Path) -> dict[str, Any]:
    """Quantities the run did record per request, summarised as observations."""
    clocks: list[float] = []
    temps: list[float] = []
    with raw.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("valid", "1") != "1":
                continue
            try:
                clock = float(row["sm_clock_mhz"])
                temp = float(row["gpu_temp_c"])
            except (KeyError, TypeError, ValueError):
                continue
            if clock > 0:
                clocks.append(clock)
            if temp > 0:
                temps.append(temp)
    out: dict[str, Any] = {}
    if clocks:
        out["sm_clock_mhz"] = {
            "mean": sum(clocks) / len(clocks),
            "min": min(clocks),
            "max": max(clocks),
            "n": len(clocks),
        }
    if temps:
        out["gpu_temp_c"] = {
            "mean": sum(temps) / len(temps),
            "min": min(temps),
            "max": max(temps),
            "n": len(temps),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="P1 manifest sidecar backfill.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)
    run_dir = root / "runs" / args.run_id
    manifest_path = run_dir / "manifest.json"
    raw_path = run_dir / "raw.csv"
    if not manifest_path.is_file():
        raise SystemExit(f"missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    fields: dict[str, Any] = {}
    sources: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if name == "model_digest":
            value = manifest.get("model_digest", "unknown")
            source = "manifest.json"
        else:
            value = "unknown"
            source = "not recorded by the run"
        fields[name] = value
        sources[name] = source

    sidecar = {
        "schema_version": 1,
        "run_id": args.run_id,
        "kind": "manifest-sidecar",
        "purpose": (
            "Completes the Phase 7 manifest schema for a run that predates it, without "
            "inventing values."
        ),
        "fields": fields,
        "field_sources": sources,
        "derived_from_raw": _observed(raw_path) if raw_path.is_file() else {},
        "derived_note": (
            "derived_from_raw holds per-request observations the run did record. These are "
            "measurements, not manifest fields, and must not be quoted as recorded "
            "environment state."
        ),
        "unknown_count": sum(1 for value in fields.values() if value == "unknown"),
        "required_count": len(REQUIRED_FIELDS),
    }

    out_dir = root / "artifacts" / "manifests"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.run_id}.manifest.sidecar.json"
    out.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    print(f"unknown: {sidecar['unknown_count']} of {sidecar['required_count']}")
    for key, value in sidecar["derived_from_raw"].items():
        print(f"observed {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
