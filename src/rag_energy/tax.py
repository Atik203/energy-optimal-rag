"""Energy-tax experiment support.

A tax arm raises the fixed cost ``a`` (fixed_a) or the per-passage cost ``b``
(per_passage_b) of the affine energy model by a calibrated dummy GPU workload.
The dummy work runs inside the per-query NVML measurement window, so its
energy is captured exactly like reader energy; no synthetic numbers are added.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import torch

from rag_energy.runner import (
    NvmlSampler,
    _default_reader,
    _integrate,
    _measure_idle,
)


def _measure_idle_power(sampler_factory: Any, interval_ms: int, seconds: float) -> float:
    stats = _measure_idle(sampler_factory, interval_ms, seconds)
    return float(stats.mean_w)


def _calibrate_dummy(
    target_j: float,
    *,
    device: str = "cuda",
    dtype: torch.dtype = torch.float16,
    size: int = 2048,
    repeats: int = 5,
    idle_power_w: float | None = None,
) -> tuple[Callable[[], None], int, float]:
    """Calibrate a matmul dummy workload to ``target_j`` joules per call.

    Returns ``(dummy_fn, iters, measured_j)``.
    """
    if idle_power_w is None:
        idle_power_w = _measure_idle_power(NvmlSampler, 100, 10.0)

    a = torch.randn(size, size, device=device, dtype=dtype)
    b = torch.randn(size, size, device=device, dtype=dtype)

    def make(iters: int) -> Callable[[], None]:
        def run() -> None:
            for _ in range(iters):
                _ = a @ b
            torch.cuda.synchronize()

        return run

    def measure(iters: int) -> float:
        fn = make(iters)
        sampler = NvmlSampler(100)
        sampler.start()
        for _ in range(repeats):
            fn()
        samples = sampler.stop()
        energy, _avg, _dur = _integrate(samples, idle_power_w)
        return energy / repeats

    # Binary search over iteration counts.
    lo, hi = 1, 1
    # Find an upper bound.
    while measure(hi) < target_j and hi < 100_000:
        hi *= 2
    best_iters = hi
    best_energy = measure(hi)
    for _ in range(12):
        mid = (lo + hi) // 2
        if mid == 0:
            break
        e = measure(mid)
        if abs(e - target_j) < abs(best_energy - target_j):
            best_iters, best_energy = mid, e
        if e < target_j:
            lo = mid + 1
        else:
            hi = mid - 1
        if lo > hi:
            break
    return make(best_iters), best_iters, best_energy


class TaxedReader:
    """Reader wrapper that injects a calibrated dummy GPU workload."""

    def __init__(
        self,
        base: Any,
        tax_kind: str,
        dummy_fn: Callable[[], None],
    ) -> None:
        if tax_kind not in {"fixed", "per_passage"}:
            raise ValueError(f"unknown tax_kind: {tax_kind!r}")
        self.base = base
        self.tax_kind = tax_kind
        self.dummy_fn = dummy_fn

    def generate(self, question: str, passages: list[Any], nonce: str) -> Any:
        if self.tax_kind == "fixed":
            self.dummy_fn()
        else:
            for _ in passages:
                self.dummy_fn()
        return self.base.generate(question, passages, nonce)
