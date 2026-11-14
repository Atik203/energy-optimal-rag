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

import hashlib
import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRNAME = "configs"

# Required top-level keys by config category. Keep this list short and stable:
# a key belongs here only if an analysis or a run cannot start without it.
REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    "base": ("project", "seed", "paths", "reader", "retrieval"),
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


def _check_reader(data: dict[str, Any], path: Path, errors: list[str]) -> None:
    """Validate the reader block when a run or grid overrides it."""
    reader = data.get("reader")
    if reader is None:
        return
    if not isinstance(reader, dict):
        errors.append(f"{path}: reader must be a table")
        return
    backend = reader.get("backend")
    if backend is not None and backend not in {"ollama", "hf"}:
        errors.append(f"{path}: reader.backend must be 'ollama' or 'hf'")
    model = reader.get("model")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        errors.append(f"{path}: reader.model must be a non-empty string")
    num_ctx = reader.get("num_ctx")
    if num_ctx is not None and (not _is_int(num_ctx) or num_ctx <= 0):
        errors.append(f"{path}: reader.num_ctx must be a positive integer")


def _check_retrieval_depth(data: dict[str, Any], path: Path, errors: list[str]) -> None:
    """Reject a retrieval cap that cannot reach the deepest requested k."""
    retrieval = data.get("retrieval")
    if not isinstance(retrieval, dict):
        return
    top_k = retrieval.get("top_k")
    if top_k is None:
        return
    if not _is_int(top_k) or top_k <= 0:
        errors.append(f"{path}: retrieval.top_k must be a positive integer")
        return
    k_grid = data.get("k_grid")
    if (
        isinstance(k_grid, list)
        and k_grid
        and all(_is_int(value) and value >= 0 for value in k_grid)
        and top_k < max(k_grid)
    ):
        errors.append(f"{path}: retrieval.top_k={top_k} is below max(k_grid)={max(k_grid)}")


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


@dataclass(frozen=True)
class ResolvedRunConfig:
    """An effective run config after base, run, and optional grid merge."""

    run_id: str
    config_path: Path
    data: dict[str, Any]
    sources: tuple[Path, ...]
    config_sha256: str


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge tables recursively; later scalars and lists win."""
    merged = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def _normalise_sections(data: dict[str, Any]) -> dict[str, Any]:
    """Accept the legacy ``[retriever]`` spelling while standardising on ``[retrieval]``."""
    legacy = data.pop("retriever", None)
    if legacy is None:
        return data
    current = data.get("retrieval")
    if isinstance(current, dict) and isinstance(legacy, dict):
        data["retrieval"] = _deep_merge(legacy, current)
    else:
        data["retrieval"] = legacy
    return data


def _canonical_hash(data: dict[str, Any]) -> str:
    """SHA-256 of the effective config, stable across TOML formatting."""
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_run_config(
    config_path: Path,
    root: Path | None = None,
) -> ResolvedRunConfig:
    """Resolve a run config against ``base.toml`` and its optional named grid.

    Precedence is base < run < grid. The grid is selected by the run's
    ``grid_id``; its ``base_run`` must name the same run. The returned hash is
    computed from the effective merged data, not from the raw file text.
    """
    root = (root or REPO_ROOT).resolve()
    config_path = config_path.resolve()
    base_path = root / CONFIG_DIRNAME / "base.toml"
    if not base_path.is_file():
        raise ConfigError(f"required base config is missing: {base_path}")

    base = _normalise_sections(load_toml(base_path))
    run = _normalise_sections(load_toml(config_path))
    merged = _deep_merge(base, run)
    sources: list[Path] = [base_path, config_path]

    grid_id = run.get("grid_id")
    if grid_id is not None:
        if not isinstance(grid_id, str) or not grid_id.strip() or Path(grid_id).name != grid_id:
            raise ConfigError(f"{config_path}: grid_id must be a simple non-empty name")
        grid_path = root / CONFIG_DIRNAME / "grid" / f"{grid_id}.toml"
        if not grid_path.is_file():
            raise ConfigError(f"{config_path}: grid {grid_id!r} not found at {grid_path}")
        grid = _normalise_sections(load_toml(grid_path))
        if grid.get("base_run") != run.get("run_id"):
            raise ConfigError(
                f"{grid_path}: base_run={grid.get('base_run')!r} does not match "
                f"run_id={run.get('run_id')!r}"
            )
        merged = _deep_merge(merged, grid)
        sources.append(grid_path)

    # Identity and category belong to the run, not to the grid.
    merged["kind"] = "run"
    for key in ("run_id", "dataset", "phase"):
        if key in run:
            merged[key] = run[key]

    problems = _validate_data(merged, "run", config_path)
    if problems:
        raise ConfigError("; ".join(problems))

    return ResolvedRunConfig(
        run_id=str(merged["run_id"]),
        config_path=config_path,
        data=merged,
        sources=tuple(sources),
        config_sha256=_canonical_hash(merged),
    )


def validate_config(path: Path, root: Path | None = None) -> list[str]:
    """Validate one config file and return a list of human-readable errors."""
    root = (root or REPO_ROOT).resolve()
    category = category_for(path, root)
    if category == "unknown":
        return [f"{path}: cannot infer config category from its location"]

    try:
        data = load_toml(path)
    except ConfigError as exc:
        return [str(exc)]

    return _validate_data(data, category, path)


def _validate_data(data: dict[str, Any], category: str, path: Path) -> list[str]:
    """Validate an already-parsed config dict for a known category."""
    errors: list[str] = []
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
        _check_reader(data, path, errors)
        _check_retrieval_depth(data, path, errors)
        if category == "run":
            if not isinstance(data.get("run_id"), str) or not data.get("run_id"):
                errors.append(f"{path}: run_id must be a non-empty string")
            if not isinstance(data.get("dataset"), str) or not data.get("dataset"):
                errors.append(f"{path}: dataset must be a non-empty string")
            grid_id = data.get("grid_id")
            if grid_id is not None and (
                not isinstance(grid_id, str) or not grid_id.strip() or Path(grid_id).name != grid_id
            ):
                errors.append(f"{path}: grid_id must be a simple non-empty name")
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

    # Resolve every run so a missing or mismatched grid fails `validate`,
    # not the first GPU sweep.
    for path in report.files:
        rel = str(path.relative_to(root))
        if category_for(path, root) != "run" or rel in report.errors:
            continue
        try:
            resolve_run_config(path, root)
        except ConfigError as exc:
            report.errors[rel] = [str(exc)]

    return report
