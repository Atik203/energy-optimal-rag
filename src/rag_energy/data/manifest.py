"""Dataset manifest: provenance, licenses, and checksums.

The manifest is the only dataset file tracked in git. It records what was used,
where it came from, and how to verify it, without redistributing raw text.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = 1

REQUIRED_DATASET_FIELDS = (
    "id",
    "name",
    "version",
    "split",
    "source_url",
    "upstream_license",
    "n_questions_used",
    "status",
)

VALID_STATUS = ("not_prepared", "prepared", "verified")


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a manifest JSON file."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("manifest root must be a JSON object")
    return data


def validate_manifest(data: dict[str, Any]) -> list[str]:
    """Return a list of schema problems; empty means valid."""
    errors: list[str] = []
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append(f"schema_version must be {MANIFEST_SCHEMA_VERSION}")
    datasets = data.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        errors.append("datasets must be a non-empty list")
        return errors
    seen: set[str] = set()
    for index, dataset in enumerate(datasets):
        if not isinstance(dataset, dict):
            errors.append(f"datasets[{index}] must be an object")
            continue
        for field in REQUIRED_DATASET_FIELDS:
            if field not in dataset:
                errors.append(f"datasets[{index}] missing {field!r}")
        dataset_id = dataset.get("id")
        if dataset_id in seen:
            errors.append(f"duplicate dataset id: {dataset_id!r}")
        seen.add(dataset_id)
        if dataset.get("status") not in VALID_STATUS:
            errors.append(f"datasets[{index}].status must be one of {VALID_STATUS}")
        n_used = dataset.get("n_questions_used")
        if not isinstance(n_used, int) or n_used < 0:
            errors.append(f"datasets[{index}].n_questions_used must be a non-negative integer")
    return errors


def build_manifest(project: str, datasets: list[dict[str, Any]]) -> dict[str, Any]:
    """Assemble a manifest object without inventing provenance."""
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project": project,
        "policy": (
            "No raw text is stored in this repository. Only dataset identifiers, "
            "versions, licenses, checksums, and derived statistics are tracked."
        ),
        "datasets": datasets,
    }
