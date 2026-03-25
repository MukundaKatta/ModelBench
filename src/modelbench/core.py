"""Core benchmarking engine for ModelBench.

Provides the ``ModelBench`` class for registering model inference functions,
running latency / throughput benchmarks, comparing models side-by-side, and
exporting results.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Sequence

from pydantic import BaseModel, Field

from modelbench.config import BenchmarkConfig
from modelbench.utils import (
    compute_throughput,
    format_duration,
    format_table,
    format_throughput,
    latency_stats,
    measure_call,
)


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

class BenchmarkResult(BaseModel):
    """Structured result of a single model benchmark run."""

    model_name: str
    iterations: int
    p50_latency: float = Field(description="50th-percentile latency (seconds)")
    p95_latency: float = Field(description="95th-percentile latency (seconds)")
    p99_latency: float = Field(description="99th-percentile latency (seconds)")
    mean_latency: float = Field(description="Mean latency (seconds)")
    median_latency: float = Field(description="Median latency (seconds)")
    min_latency: float = Field(description="Minimum latency (seconds)")
    max_latency: float = Field(description="Maximum latency (seconds)")
    stdev_latency: float = Field(description="Latency standard deviation (seconds)")
    throughput_rps: float = Field(description="Throughput in requests per second")
    total_duration: float = Field(description="Total benchmark wall-clock time (seconds)")

    def summary(self) -> str:
        """Return a one-line human-readable summary."""
        return (
            f"{self.model_name}: p50={format_duration(self.p50_latency)}, "
            f"p95={format_duration(self.p95_latency)}, "
            f"p99={format_duration(self.p99_latency)}, "
            f"throughput={format_throughput(self.throughput_rps)}"
        )


# ---------------------------------------------------------------------------
# Main benchmarking class
# ---------------------------------------------------------------------------

class ModelBench:
    """Registry and runner for model inference benchmarks.

    Usage::

        bench = ModelBench()
        bench.register_model("my_model", my_inference_fn)
        result = bench.benchmark("my_model", sample_inputs)
        print(result.summary())
    """

    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        self.config = config or BenchmarkConfig()
        self._models: dict[str, Callable] = {}

    # -- registration -------------------------------------------------------

    def register_model(self, name: str, inference_fn: Callable) -> None:
        """Register a model inference function under *name*.

        Parameters
        ----------
        name:
            Unique identifier for the model / serving configuration.
        inference_fn:
            A callable that accepts a single input and returns a prediction.
        """
        if not callable(inference_fn):
            raise TypeError(f"inference_fn must be callable, got {type(inference_fn)}")
        self._models[name] = inference_fn

    @property
    def registered_models(self) -> list[str]:
        """Return names of all registered models."""
        return list(self._models.keys())

    # -- core measurements --------------------------------------------------

    def measure_latency(
        self,
        fn: Callable,
        inputs: Sequence[Any],
        iterations: int | None = None,
    ) -> list[float]:
        """Measure per-call latency of *fn* over *inputs* for *iterations* rounds.

        Returns a list of latency values in seconds.
        """
        iterations = iterations or self.config.iterations

        # Warmup phase
        for inp in inputs[: self.config.warmup_iterations]:
            fn(inp)

        latencies: list[float] = []
        for i in range(iterations):
            inp = inputs[i % len(inputs)]
            elapsed, _ = measure_call(fn, inp)
            latencies.append(elapsed)
        return latencies

    def measure_throughput(
        self,
        fn: Callable,
        inputs: Sequence[Any],
        duration: float | None = None,
    ) -> tuple[int, float]:
        """Run *fn* continuously for *duration* seconds and count completions.

        Returns ``(count, actual_duration)``.
        """
        duration = duration or self.config.throughput_duration
        count = 0
        idx = 0
        n = len(inputs)
        start = time.perf_counter()
        deadline = start + duration
        while time.perf_counter() < deadline:
            fn(inputs[idx % n])
            count += 1
            idx += 1
        actual = time.perf_counter() - start
        return count, actual

    # -- high-level API -----------------------------------------------------

    def benchmark(
        self,
        model_name: str,
        inputs: Sequence[Any],
        iterations: int | None = None,
        throughput_duration: float | None = None,
    ) -> BenchmarkResult:
        """Run a full benchmark (latency + throughput) for a registered model.

        Parameters
        ----------
        model_name:
            Name previously passed to :meth:`register_model`.
        inputs:
            A sequence of sample inputs to feed the inference function.
        iterations:
            Override the default iteration count for latency measurement.
        throughput_duration:
            Override the default duration for throughput measurement.

        Returns
        -------
        BenchmarkResult
            Structured result with percentile latencies and throughput.
        """
        if model_name not in self._models:
            raise KeyError(f"Model '{model_name}' not registered. Available: {self.registered_models}")

        fn = self._models[model_name]
        wall_start = time.perf_counter()

        # Latency measurement
        latencies = self.measure_latency(fn, inputs, iterations=iterations)
        stats = latency_stats(latencies)

        # Throughput measurement
        count, dur = self.measure_throughput(fn, inputs, duration=throughput_duration)
        rps = compute_throughput(count, dur)

        wall_end = time.perf_counter()

        return BenchmarkResult(
            model_name=model_name,
            iterations=len(latencies),
            p50_latency=stats["p50"],
            p95_latency=stats["p95"],
            p99_latency=stats["p99"],
            mean_latency=stats["mean"],
            median_latency=stats["median"],
            min_latency=stats["min"],
            max_latency=stats["max"],
            stdev_latency=stats["stdev"],
            throughput_rps=rps,
            total_duration=wall_end - wall_start,
        )

    def compare_models(
        self,
        model_names: Sequence[str],
        inputs: Sequence[Any],
        iterations: int | None = None,
        throughput_duration: float | None = None,
    ) -> list[BenchmarkResult]:
        """Benchmark multiple models and return results sorted by p50 latency."""
        results = [
            self.benchmark(name, inputs, iterations=iterations, throughput_duration=throughput_duration)
            for name in model_names
        ]
        results.sort(key=lambda r: r.p50_latency)
        return results

    # -- reporting & export -------------------------------------------------

    @staticmethod
    def generate_report(results: Sequence[BenchmarkResult]) -> str:
        """Generate a human-readable comparison report from benchmark results."""
        if not results:
            return "No results to report."

        rows: list[dict[str, str]] = []
        for r in results:
            rows.append(
                {
                    "Model": r.model_name,
                    "p50": format_duration(r.p50_latency),
                    "p95": format_duration(r.p95_latency),
                    "p99": format_duration(r.p99_latency),
                    "Mean": format_duration(r.mean_latency),
                    "Throughput": format_throughput(r.throughput_rps),
                }
            )
        headers = ["Model", "p50", "p95", "p99", "Mean", "Throughput"]
        title = "ModelBench Comparison Report"
        lines = [
            title,
            "=" * len(title),
            "",
            format_table(rows, headers),
            "",
            f"Benchmarked {len(results)} model(s).",
        ]
        return "\n".join(lines)

    @staticmethod
    def export_results(
        results: Sequence[BenchmarkResult],
        format: str = "json",
        path: str | Path | None = None,
    ) -> str:
        """Export benchmark results to a file or return as a string.

        Parameters
        ----------
        results:
            List of BenchmarkResult objects.
        format:
            Output format — ``"json"`` or ``"csv"``.
        path:
            Optional file path. If provided the output is written to disk.

        Returns
        -------
        str
            The serialised results.
        """
        if format == "json":
            data = [r.model_dump() for r in results]
            output = json.dumps(data, indent=2)
        elif format == "csv":
            if not results:
                return ""
            fields = list(results[0].model_dump().keys())
            lines = [",".join(fields)]
            for r in results:
                d = r.model_dump()
                lines.append(",".join(str(d[f]) for f in fields))
            output = "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format!r}. Use 'json' or 'csv'.")

        if path is not None:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(output)
        return output
