"""Tracked run registry.

The registry is a CSV under version control. Raw run directories are not. Every
row records the effective config hash, the prereg hash, and the model digest so
the analysis can refuse a mismatched or unknown run.
"""

from __future__ import annotations

import csv
import hashlib
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REGISTRY_FIELDS: tuple[str, ...] = (
    "run_id",
    "timestamp_utc",
    "phase",
    "dataset",
    "reader",
    "retriever",
    "k_grid",
    "n_questions",
    "seed",
    "energy_sampler",
    "status",
    "git_commit",
    "config_path",
    "config_sha256",
    "prereg_sha256",
    "model_digest",
    "raw_csv",
    "notes",
)

VALID_STATUSES = {"planned", "running", "completed", "aborted", "invalid"}


def _write_header(path: Path) -> None:
    """Create a header-only registry with LF endings and no BOM."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(",".join(REGISTRY_FIELDS) + "\n")


def ensure_registry(path: Path) -> None:
    """Create the registry header if the file is missing or empty."""
    if not path.exists() or path.stat().st_size == 0:
        _write_header(path)


def read_registry(path: Path) -> list[dict[str, str]]:
    """Read registry rows, validating the exact tracked header."""
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REGISTRY_FIELDS:
            raise ValueError(
                f"{path}: registry header does not match the tracked schema; "
                f"found {reader.fieldnames!r}"
            )
        return [dict(row) for row in reader]


def _format_k_grid(value: Any) -> str:
    """Render a depth sequence as the registry's pipe-separated field."""
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("k_grid must not be empty")
        return value
    if not isinstance(value, Sequence):
        raise ValueError("k_grid must be a sequence or a pipe-separated string")
    try:
        depths = [int(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ValueError("k_grid must contain integers") from exc
    if not depths:
        raise ValueError("k_grid must not be empty")
    return "|".join(str(depth) for depth in depths)


def _normalise_row(row: Mapping[str, Any]) -> dict[str, str]:
    """Validate and stringify one registry row."""
    missing = [field for field in REGISTRY_FIELDS if field not in row]
    if missing:
        raise ValueError(f"registry row is missing fields: {', '.join(missing)}")
    unknown = [field for field in row if field not in REGISTRY_FIELDS]
    if unknown:
        raise ValueError(f"registry row has unknown fields: {', '.join(unknown)}")
    status = str(row["status"])
    if status not in VALID_STATUSES:
        raise ValueError(f"registry status {status!r} is not one of {sorted(VALID_STATUSES)}")
    normalised = {field: "" if row[field] is None else str(row[field]) for field in REGISTRY_FIELDS}
    normalised["k_grid"] = _format_k_grid(row["k_grid"])
    return normalised


def append_registry_row(path: Path, row: Mapping[str, Any]) -> None:
    """Append one row, rejecting duplicates and schema drift."""
    ensure_registry(path)
    normalised = _normalise_row(row)
    existing = read_registry(path)
    if any(item["run_id"] == normalised["run_id"] for item in existing):
        raise ValueError(f"run_id {normalised['run_id']!r} is already registered")
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=REGISTRY_FIELDS,
            lineterminator="\n",
        )
        writer.writerow(normalised)
        handle.flush()
        os.fsync(handle.fileno())


def update_registry_status(
    path: Path,
    run_id: str,
    status: str,
    notes: str | None = None,
) -> None:
    """Update one run's status in place, preserving all other rows."""
    if status not in VALID_STATUSES:
        raise ValueError(f"registry status {status!r} is not one of {sorted(VALID_STATUSES)}")
    rows = read_registry(path)
    target = None
    for row in rows:
        if row["run_id"] == run_id:
            target = row
            break
    if target is None:
        raise ValueError(f"run_id {run_id!r} not found in {path}")
    target["status"] = status
    if notes is not None:
        target["notes"] = notes

    temp_path = path.with_name(path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=REGISTRY_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
