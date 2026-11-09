"""NVML power sampler.

Primary sensor: NVML ``power.draw`` sampled every 100 ms via ``pynvml`` (the
same sensor ``nvidia-smi --query-gpu=power.draw`` exposes).

Important caveat from the pilot: on the laptop 3060 the driver updates
``power.draw`` coarsely (approximately 1 Hz). The 100 ms cadence is a sampling
label, not a 100 ms precision claim. Absolute joules rely on 20-query block
calibration and repeat CV; per-query values are used for pairing and bootstrap,
not absolute precision.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PowerSample:
    """One NVML sample."""

    t_s: float
    power_w: float
    utilization_pct: float | None = None
    memory_used_mb: float | None = None
    temperature_c: float | None = None
    sm_clock_mhz: float | None = None


class NvmlSampler:
    """Context-managed NVML sampler.

    The sampler records samples in memory; the caller integrates them over the
    query window. ``pynvml`` is imported lazily so the package imports without
    the optional GPU dependency.
    """

    def __init__(self, interval_ms: int = 100, device_index: int = 0) -> None:
        if interval_ms <= 0:
            raise ValueError("interval_ms must be positive")
        self.interval_ms = interval_ms
        self.device_index = device_index
        self.samples: list[PowerSample] = []
        self._handle = None

    def start(self) -> None:
        """Initialize NVML and the device handle. Implemented in P0."""
        raise NotImplementedError("NvmlSampler.start is implemented in P0.")

    def stop(self) -> list[PowerSample]:
        """Stop sampling and return the recorded samples. Implemented in P0."""
        raise NotImplementedError("NvmlSampler.stop is implemented in P0.")

    def __enter__(self) -> NvmlSampler:
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
