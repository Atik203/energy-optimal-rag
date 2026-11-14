"""NVML sampler tests with a fake pynvml module; no GPU required."""

from __future__ import annotations

import sys
import time
import types

import pytest

from rag_energy.energy.nvml_sampler import NvmlSampler


class _FakeNvmlError(Exception):
    pass


class _FakeNotSupported(_FakeNvmlError):
    pass


def _fake_module(*, temperature_error: bool = False, power_error: bool = False) -> types.ModuleType:
    module = types.ModuleType("pynvml")
    module.NVMLError = _FakeNvmlError
    module.NVMLError_NotSupported = _FakeNotSupported
    module.NVML_TEMPERATURE_GPU = 0
    module.NVML_CLOCK_SM = 1
    module.calls = {"init": 0, "shutdown": 0}

    class _Util:
        gpu = 55.0

    class _Memory:
        used = 100 * 1024 * 1024

    def nvmlInit() -> None:
        module.calls["init"] += 1

    def nvmlShutdown() -> None:
        module.calls["shutdown"] += 1

    def nvmlDeviceGetHandleByIndex(index: int) -> str:
        assert index == 0
        return "handle"

    def nvmlDeviceGetPowerUsage(handle: str) -> int:
        if power_error:
            raise _FakeNvmlError("power unavailable")
        return 15_000

    def nvmlDeviceGetUtilizationRates(handle: str) -> _Util:
        return _Util()

    def nvmlDeviceGetMemoryInfo(handle: str) -> _Memory:
        return _Memory()

    def nvmlDeviceGetTemperature(handle: str, sensor: int) -> int:
        if temperature_error:
            raise _FakeNotSupported("temperature unsupported")
        return 61

    def nvmlDeviceGetClockInfo(handle: str, clock: int) -> int:
        return 1500

    module.nvmlInit = nvmlInit
    module.nvmlShutdown = nvmlShutdown
    module.nvmlDeviceGetHandleByIndex = nvmlDeviceGetHandleByIndex
    module.nvmlDeviceGetPowerUsage = nvmlDeviceGetPowerUsage
    module.nvmlDeviceGetUtilizationRates = nvmlDeviceGetUtilizationRates
    module.nvmlDeviceGetMemoryInfo = nvmlDeviceGetMemoryInfo
    module.nvmlDeviceGetTemperature = nvmlDeviceGetTemperature
    module.nvmlDeviceGetClockInfo = nvmlDeviceGetClockInfo
    return module


def test_sampler_records_power_and_optional_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _fake_module()
    monkeypatch.setitem(sys.modules, "pynvml", fake)
    sampler = NvmlSampler(interval_ms=10)

    sampler.start()
    time.sleep(0.05)
    samples = sampler.stop()

    assert len(samples) >= 2
    assert samples[0].power_w == pytest.approx(15.0)
    assert samples[0].utilization_pct == pytest.approx(55.0)
    assert samples[0].memory_used_mb == pytest.approx(100.0)
    assert samples[0].temperature_c == pytest.approx(61.0)
    assert samples[0].sm_clock_mhz == pytest.approx(1500.0)
    assert fake.calls["init"] == 1
    assert fake.calls["shutdown"] == 1
    assert samples[0].t_s <= samples[-1].t_s


def test_sampler_tolerates_unsupported_optional_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _fake_module(temperature_error=True)
    monkeypatch.setitem(sys.modules, "pynvml", fake)
    sampler = NvmlSampler(interval_ms=10)

    sampler.start()
    time.sleep(0.03)
    samples = sampler.stop()

    assert samples
    assert samples[0].temperature_c is None
    assert samples[0].power_w == pytest.approx(15.0)


def test_sampler_raises_if_power_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _fake_module(power_error=True)
    monkeypatch.setitem(sys.modules, "pynvml", fake)
    sampler = NvmlSampler(interval_ms=10)

    with pytest.raises(RuntimeError, match="power"):
        sampler.start()
    assert fake.calls["shutdown"] == 1


def test_sampler_is_a_context_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _fake_module()
    monkeypatch.setitem(sys.modules, "pynvml", fake)

    with NvmlSampler(interval_ms=10) as sampler:
        time.sleep(0.03)

    assert sampler.samples
    assert fake.calls["shutdown"] == 1


def test_sampler_rejects_double_start(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _fake_module()
    monkeypatch.setitem(sys.modules, "pynvml", fake)
    sampler = NvmlSampler(interval_ms=10)
    sampler.start()
    try:
        with pytest.raises(RuntimeError, match="already running"):
            sampler.start()
    finally:
        sampler.stop()


def test_sampler_rejects_stop_before_start() -> None:
    with pytest.raises(RuntimeError, match="not running"):
        NvmlSampler().stop()
