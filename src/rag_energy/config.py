"""Configuration loading and validation.

Standard library only. This module must remain importable without numpy,
pandas, torch, or a GPU so that CI and the smoke test stay lightweight.

Config layout
-------------
``configs/base.toml``            shared project, reader, retriever, energy settings
``configs/runs/*.toml``          one experiment run (dataset, n, depth grid, reader)
``configs/grid/*.toml``          named depth grids used by runs
``configs/taxes/*.toml``         energy-tax manipulation conditions
``configs/analysis/*.toml``      frozen analysis parameters (margins, bootstrap, splits)
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRNAME = "configs"

# Required top-level keys by config category. Keep this list short and stable:
# a key belongs here only if an analysis or a run cannot start without it.
REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    "base": ("project", "seed", "paths", "reader", "retriever"),
    "run": (
        "run_id",
        "dataset",
        "n_questions",
        "k_grid",
        "seed",
        "reader",
        "retrieval",
        "energy",
    ),
    "grid": ("grid_id", "k_grid", "n_questions", "base_run"),
    "tax": (
        "tax_id",
        "tax_kind",
        "target_fraction",
        "baseline_a_j",
        "baseline_b_j_per_passage",
        "delta_a_j",
        "delta_b_j_per_passage",
    ),
    "analysis": ("primary", "secondary", "bootstrap", "policy_split", "gates"),
}


@dataclass
class ConfigReport:
    """Result of validating one or more TOML configs."""

    root: Path
    files: list[Path] = field(default_factory=list)
    errors: dict[str, list[str]] = field(default_factory=dict)
    warnings: dict[str, list[str]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def n_files(self) -> int:
        return len(self.files)


class ConfigError(ValueError):
    """Raised when a config is missing, unparseable, or semantically invalid."""


def category_for(path: Path, root: Path) -> str:
    """Return the config category implied by a file's location."""
    try:
        rel = path.resolve().relative_to((root / CONFIG_DIRNAME).resolve())
    except ValueError:
        return "unknown"
    parts = rel.parts
    if len(parts) == 1:
        return Path(parts[0]).stem if Path(parts[0]).stem == "base" else "unknown"
    folder = parts[0]
    return {
        "runs": "run",
        "grid": "grid",
        "taxes": "tax",
        "analysis": "analysis",
    }.get(folder, "unknown")


def load_toml(path: Path) -> dict[str, Any]:
    """Parse a TOML file, raising :class:`ConfigError` with context on failure."""
    if not path.is_file():
        raise ConfigError(f"config not found: {path}")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: invalid TOML: {exc}") from exc


def _is_int(value: Any) -> bool:
    # bool is a subclass of int; reject it explicitly.
    return isinstance(value, int) and not isinstance(value, bool)


def _check_depth_grid(values: Any, where: str, errors: list[str]) -> None:
    if not isinstance(values, list) or not values:
        errors.append(f"{where}: k_grid must be a non-empty list of integers")
        return
    if not all(_is_int(v) and v >= 0 for v in values):
        errors.append(f"{where}: k_grid must contain non-negative integers")
        return
    if len(set(values)) != len(values):
        errors.append(f"{where}: k_grid contains duplicates")
    if values != sorted(values):
        errors.append(f"{where}: k_grid must be strictly increasing")


def _check_positive_int(value: Any, where: str, errors: list[str]) -> None:
    if not _is_int(value) or value <= 0:
        errors.append(f"{where} must be a positive integer")


def _check_tax_delta(
    path: Path,
    label: str,
    baseline: Any,
    delta: Any,
    fraction: float,
    errors: list[str],
) -> None:
    """Check that a tax delta equals ``fraction * baseline`` within 2%."""
    if not isinstance(baseline, (int, float)) or not isinstance(delta, (int, float)):
        return
    if abs(float(delta) - float(fraction) * float(baseline)) > 0.02 * float(baseline):
        errors.append(f"{path}: {label} is inconsistent with target_fraction * baseline")


def validate_config(path: Path, root: Path | None = None) -> list[str]:
    """Validate one config file and return a list of human-readable errors."""
    root = (root or REPO_ROOT).resolve()
    errors: list[str] = []
    category = category_for(path, root)
    if category == "unknown":
        return [f"{path}: cannot infer config category from its location"]

    try:
        data = load_toml(path)
    except ConfigError as exc:
        return [str(exc)]

    declared_kind = data.get("kind")
    if declared_kind is not None and declared_kind != category:
        errors.append(
            f"{path}: kind={declared_kind!r} does not match directory category {category!r}"
        )

    for key in REQUIRED_KEYS[category]:
        if key not in data:
            errors.append(f"{path}: missing required key {key!r}")

    if "seed" in data and not _is_int(data["seed"]):
        errors.append(f"{path}: seed must be an integer")

    if category in {"run", "grid"}:
        if "k_grid" in data:
            _check_depth_grid(data["k_grid"], str(path), errors)
        if "n_questions" in data:
            _check_positive_int(data["n_questions"], f"{path}: n_questions", errors)
        if category == "run":
            if not isinstance(data.get("run_id"), str) or not data.get("run_id"):
                errors.append(f"{path}: run_id must be a non-empty string")
            if not isinstance(data.get("dataset"), str) or not data.get("dataset"):
                errors.append(f"{path}: dataset must be a non-empty string")
        if category == "grid":
            if not isinstance(data.get("grid_id"), str) or not data.get("grid_id"):
                errors.append(f"{path}: grid_id must be a non-empty string")
            if not isinstance(data.get("base_run"), str) or not data.get("base_run"):
                errors.append(f"{path}: base_run must be a non-empty string")

    if category == "tax":
        fraction = data.get("target_fraction")
        if not isinstance(fraction, (int, float)) or not 0.10 <= float(fraction) <= 0.30:
            errors.append(f"{path}: target_fraction must lie in [0.10, 0.30]")
        for name in ("baseline_a_j", "baseline_b_j_per_passage"):
            value = data.get(name)
            if not isinstance(value, (int, float)) or float(value) <= 0:
                errors.append(f"{path}: {name} must be a positive number")

        tax_kind = data.get("tax_kind")
        if tax_kind not in {"fixed", "per_passage", "both"}:
            errors.append(f"{path}: tax_kind must be 'fixed', 'per_passage', or 'both'")

        if isinstance(fraction, (int, float)):
            baseline_a = data.get("baseline_a_j")
            baseline_b = data.get("baseline_b_j_per_passage")
            delta_a = data.get("delta_a_j")
            delta_b = data.get("delta_b_j_per_passage")

            if tax_kind in {"fixed", "both"}:
                _check_tax_delta(path, "delta_a_j", baseline_a, delta_a, float(fraction), errors)
            elif (
                tax_kind == "per_passage"
                and isinstance(delta_a, (int, float))
                and float(delta_a) != 0.0
            ):
                errors.append(f"{path}: a per_passage tax must set delta_a_j = 0")

            if tax_kind in {"per_passage", "both"}:
                _check_tax_delta(
                    path,
                    "delta_b_j_per_passage",
                    baseline_b,
                    delta_b,
                    float(fraction),
                    errors,
                )
            elif (
                tax_kind == "fixed" and isinstance(delta_b, (int, float)) and float(delta_b) != 0.0
            ):
                errors.append(f"{path}: a fixed tax must set delta_b_j_per_passage = 0")

    if category == "analysis":
        primary = data.get("primary", {})
        secondary = data.get("secondary", {})
        bootstrap = data.get("bootstrap", {})
        policy = data.get("policy_split", {})
        # The split is a target over the analysed questions. Older analysis
        # configs without n_questions still assume the 1,000-question P1 design.
        target_n = data.get("n_questions", 1000)
        if not _is_int(target_n) or target_n <= 0:
            errors.append(f"{path}: n_questions must be a positive integer")
        if isinstance(primary, dict):
            margin = primary.get("margin_pp")
            if not isinstance(margin, (int, float)) or not 0 < float(margin) < 50:
                errors.append(f"{path}: primary.margin_pp must lie in (0, 50)")
            alpha = primary.get("alpha")
            if not isinstance(alpha, (int, float)) or not 0 < float(alpha) < 1:
                errors.append(f"{path}: primary.alpha must lie in (0, 1)")
        if isinstance(secondary, dict) and isinstance(primary, dict):
            pm, sm = primary.get("margin_pp"), secondary.get("margin_pp")
            if isinstance(pm, (int, float)) and isinstance(sm, (int, float)) and sm >= pm:
                errors.append(f"{path}: secondary.margin_pp must be smaller than primary.margin_pp")
        if isinstance(bootstrap, dict):
            resamples = bootstrap.get("resamples")
            if not _is_int(resamples) or resamples < 1000:
                errors.append(f"{path}: bootstrap.resamples must be an integer >= 1000")
        if isinstance(policy, dict):
            parts = [policy.get("train"), policy.get("validation"), policy.get("test")]
            if not all(_is_int(p) and p > 0 for p in parts):
                errors.append(f"{path}: policy_split values must be positive integers")
            elif _is_int(target_n) and target_n > 0 and sum(parts) != target_n:
                errors.append(
                    f"{path}: policy_split must sum to {target_n} questions, "
                    f"matching n_questions = {target_n}"
                )

    return errors


def validate_all(root: Path | None = None) -> ConfigReport:
    """Validate every TOML config under ``<root>/configs``."""
    root = (root or REPO_ROOT).resolve()
    configs_dir = root / CONFIG_DIRNAME
    report = ConfigReport(root=root)
    if not configs_dir.is_dir():
        report.errors[str(configs_dir)] = ["configs directory not found"]
        return report

    report.files = sorted(configs_dir.rglob("*.toml"))
    if not report.files:
        report.errors[str(configs_dir)] = ["no TOML configs found"]
        return report

    base = configs_dir / "base.toml"
    if not base.is_file():
        report.errors[str(base)] = ["required base config is missing"]

    for path in report.files:
        problems = validate_config(path, root)
        if problems:
            report.errors[str(path.relative_to(root))] = problems

    return report
