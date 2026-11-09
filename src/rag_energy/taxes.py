"""Energy-tax manipulation.

The causal test of Corollary 1. A calibrated dummy GPU computation adds energy
without changing the prompt, the passages, or the answer:

- a fixed tax raises ``a`` and should **increase** ``k*``;
- a per-passage tax raises ``b`` and should **decrease** ``k*``.

If the signs are wrong, the affine/split model is falsified and the paper must
revise the theory rather than report a null as support.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag_energy.config import load_toml, validate_config


@dataclass(frozen=True)
class TaxSpec:
    tax_id: str
    tax_kind: str
    target_fraction: float
    baseline_a_j: float
    baseline_b_j_per_passage: float
    delta_a_j: float
    delta_b_j_per_passage: float
    n_questions: int
    k_grid: list[int]
    prediction: str


def load_tax_spec(config_path: Path) -> TaxSpec:
    """Load and validate a tax config."""
    problems = validate_config(config_path)
    if problems:
        raise ValueError("; ".join(problems))
    data = load_toml(config_path)
    return TaxSpec(
        tax_id=str(data["tax_id"]),
        tax_kind=str(data["tax_kind"]),
        target_fraction=float(data["target_fraction"]),
        baseline_a_j=float(data["baseline_a_j"]),
        baseline_b_j_per_passage=float(data["baseline_b_j_per_passage"]),
        delta_a_j=float(data["delta_a_j"]),
        delta_b_j_per_passage=float(data["delta_b_j_per_passage"]),
        n_questions=int(data["n_questions"]),
        k_grid=[int(k) for k in data["k_grid"]],
        prediction=str(data["prediction"]),
    )


def expected_direction(tax_kind: str) -> str:
    """Predicted movement of ``k*`` under the tax."""
    if tax_kind == "fixed":
        return "increase"
    if tax_kind == "per_passage":
        return "decrease"
    raise ValueError(f"unknown tax_kind: {tax_kind!r}")


def calibrate_dummy_work(target_j: float, repeats: int = 20) -> float:
    """Calibrate a dummy computation to ``target_j`` joules. Implemented in P2."""
    raise NotImplementedError("calibrate_dummy_work is implemented in P2.")


def run_tax_condition(config_path: Path) -> Path:
    """Run one tax condition and return its raw CSV. Implemented in P2."""
    raise NotImplementedError("run_tax_condition is implemented in P2.")
