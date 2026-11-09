"""CPU retrieval energy proxy.

``pyRAPL`` is unavailable on the Windows/AMD pilot host, so BM25 time is
converted at a documented single-thread active-above-idle power. This is an
upper bound and must be labeled as a proxy, never as a measurement.
"""

from __future__ import annotations

DEFAULT_WATTS = 20.0


def cpu_retrieval_joules(seconds: float, watts: float = DEFAULT_WATTS) -> float:
    """Convert retrieval wall time to joules using a fixed power proxy.

    Args:
        seconds: Measured BM25 time for one query, in seconds.
        watts: Active-above-idle single-thread power. The pilot used 20 W.

    Returns:
        Joules, as an upper-bound proxy.
    """
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    if watts <= 0:
        raise ValueError("watts must be positive")
    return float(seconds) * float(watts)


def proxy_share(cpu_joules: float, gpu_joules: float) -> float:
    """Retrieval-only share of total energy under the proxy."""
    total = cpu_joules + gpu_joules
    if total <= 0:
        raise ValueError("total energy must be positive")
    return cpu_joules / total
