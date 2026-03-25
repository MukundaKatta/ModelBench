"""Timing utilities, percentile calculation, statistics helpers, and formatting."""

from __future__ import annotations

import statistics
import time
from contextlib import contextmanager
from typing import Callable, Sequence


# ---------------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------------

@contextmanager
def timer():
    """Context manager that yields a callable returning elapsed seconds.

    Usage::

        with timer() as elapsed:
            do_work()
        print(f"Took {elapsed():.4f}s")
    """
    start = time.perf_counter()
    result: dict[str, float] = {}

    def _elapsed() -> float:
        return result.get("elapsed", time.perf_counter() - start)

    yield _elapsed
    result["elapsed"] = time.perf_counter() - start


def measure_call(fn: Callable, *args, **kwargs) -> tuple[float, object]:
    """Call *fn* and return ``(elapsed_seconds, return_value)``."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, result


# ---------------------------------------------------------------------------
# Percentile / statistics helpers
# ---------------------------------------------------------------------------

def percentile(data: Sequence[float], p: float) -> float:
    """Return the *p*-th percentile (0-100) of *data* using linear interpolation.

    Raises ``ValueError`` when *data* is empty.
    """
    if not data:
        raise ValueError("Cannot compute percentile of empty sequence")
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    k = (p / 100.0) * (n - 1)
    lower = int(k)
    upper = lower + 1
    if upper >= n:
        return sorted_data[-1]
    weight = k - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def latency_stats(latencies: Sequence[float]) -> dict[str, float]:
    """Compute common latency statistics from a list of latency values.

    Returns a dict with keys: mean, median, stdev, min, max, p50, p95, p99.
    """
    if not latencies:
        raise ValueError("Cannot compute stats on empty latency list")
    return {
        "mean": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
        "min": min(latencies),
        "max": max(latencies),
        "p50": percentile(latencies, 50),
        "p95": percentile(latencies, 95),
        "p99": percentile(latencies, 99),
    }


def compute_throughput(count: int, duration: float) -> float:
    """Return requests-per-second given a *count* and *duration* in seconds."""
    if duration <= 0:
        return 0.0
    return count / duration


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_duration(seconds: float) -> str:
    """Human-friendly duration string."""
    if seconds < 1e-3:
        return f"{seconds * 1e6:.1f} us"
    if seconds < 1.0:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds:.3f} s"


def format_throughput(rps: float) -> str:
    """Format requests-per-second."""
    if rps >= 1000:
        return f"{rps:,.0f} req/s"
    return f"{rps:.2f} req/s"


def format_table(rows: list[dict[str, str]], headers: list[str]) -> str:
    """Render a simple ASCII table from a list of row dicts and header keys."""
    col_widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(row.get(h, ""))))

    separator = "+-" + "-+-".join("-" * col_widths[h] for h in headers) + "-+"
    header_line = "| " + " | ".join(h.ljust(col_widths[h]) for h in headers) + " |"

    lines = [separator, header_line, separator]
    for row in rows:
        line = "| " + " | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers) + " |"
        lines.append(line)
    lines.append(separator)
    return "\n".join(lines)
