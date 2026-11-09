"""Plug-in wall-meter cross-check.

A wall meter (e.g. Kill A Watt) measures whole-system power on a 30-query subset
per condition. It is the honest answer to coarse laptop GPU telemetry. The
meter is read manually; this module defines the record format and the
calibration comparison.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WallMeterReading:
    """One manual wall-meter observation."""

    condition: str
    n_queries: int
    duration_s: float
    energy_wh: float

    @property
    def average_power_w(self) -> float:
        if self.duration_s <= 0:
            raise ValueError("duration_s must be positive")
        return self.energy_wh * 3600.0 / self.duration_s


def wall_meter_joules(energy_wh: float) -> float:
    """Convert watt-hours to joules."""
    if energy_wh < 0:
        raise ValueError("energy_wh must be non-negative")
    return float(energy_wh) * 3600.0


def calibration_factor(system_j: float, integrated_j: float) -> float:
    """Ratio of whole-system energy to GPU+CPU integration.

    A factor near 1.0 supports the integrated estimate; a factor far from 1.0
    means the integration omits a real system cost and must be reported.
    """
    if integrated_j <= 0:
        raise ValueError("integrated_j must be positive")
    return float(system_j) / float(integrated_j)
