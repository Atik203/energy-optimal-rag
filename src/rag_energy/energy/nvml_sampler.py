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

import contextlib
import threading
import time
from dataclasses import dataclass
from typing import Any


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
        self._handle: Any = None
        self._pynvml: Any = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._error: BaseException | None = None

    def _sample_once(self) -> None:
        pynvml = self._pynvml
        if pynvml is None or self._handle is None:
            raise RuntimeError("NVML sampler is not initialised")
        power_mw = pynvml.nvmlDeviceGetPowerUsage(self._handle)
        power_w = float(power_mw) / 1000.0

        def optional(read: Any) -> float | None:
            try:
                value = read()
            except pynvml.NVMLError:
                return None
            return None if value is None else float(value)

        utilization = optional(lambda: pynvml.nvmlDeviceGetUtilizationRates(self._handle).gpu)
        memory = optional(lambda: pynvml.nvmlDeviceGetMemoryInfo(self._handle).used / (1024 * 1024))
        temperature = optional(
            lambda: pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU)
        )
        clock = optional(lambda: pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_SM))
        sample = PowerSample(
            t_s=time.monotonic(),
            power_w=power_w,
            utilization_pct=utilization,
            memory_used_mb=memory,
            temperature_c=temperature,
            sm_clock_mhz=clock,
        )
        with self._lock:
            self.samples.append(sample)

    def _loop(self) -> None:
        interval_s = self.interval_ms / 1000.0
        while not self._stop_event.is_set():
            if self._stop_event.wait(interval_s):
                break
            try:
                self._sample_once()
            except BaseException as exc:  # noqa: BLE001 - surfaced by stop()
                self._error = exc
                self._stop_event.set()
                break

    def start(self) -> None:
        """Initialise NVML, take a boundary sample, and start the thread."""
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("NVML sampler is already running")
        import pynvml

        self._pynvml = pynvml
        try:
            pynvml.nvmlInit()
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
            with self._lock:
                self.samples.clear()
            self._error = None
            self._stop_event.clear()
            self._sample_once()
        except BaseException as exc:
            with contextlib.suppress(Exception):
                pynvml.nvmlShutdown()
            self._pynvml = None
            self._handle = None
            raise RuntimeError(f"NVML sampler failed: {exc}") from exc

        self._thread = threading.Thread(
            target=self._loop,
            name="nvml-sampler",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> list[PowerSample]:
        """Stop sampling, take an end-boundary sample, and return all samples."""
        if self._thread is None:
            raise RuntimeError("NVML sampler is not running")
        self._stop_event.set()
        self._thread.join(timeout=max(5.0, self.interval_ms / 1000.0 * 5))
        if self._thread.is_alive():
            self._error = RuntimeError("NVML sampler thread did not stop")
        self._thread = None

        if self._error is None:
            try:
                self._sample_once()
            except BaseException as exc:  # noqa: BLE001 - surfaced below
                self._error = exc

        pynvml = self._pynvml
        if pynvml is not None:
            try:
                pynvml.nvmlShutdown()
            finally:
                self._pynvml = None
                self._handle = None

        if self._error is not None:
            error = self._error
            self._error = None
            raise RuntimeError(f"NVML sampler failed: {error}") from error

        with self._lock:
            return list(self.samples)

    def __enter__(self) -> NvmlSampler:
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self.stop()
        except Exception:
            if exc_type is None:
                raise
