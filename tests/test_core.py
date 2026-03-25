"""Tests for ModelBench core benchmarking engine."""

from __future__ import annotations

import time

import pytest

from modelbench.core import BenchmarkResult, ModelBench
from modelbench.config import BenchmarkConfig
from modelbench.utils import latency_stats, percentile, format_duration


# ---------------------------------------------------------------------------
# Mock inference functions
# ---------------------------------------------------------------------------

def fast_model(x):
    """Simulates a fast inference (~0.1 ms)."""
    return x * 2


def slow_model(x):
    """Simulates a slower inference (~1 ms)."""
    time.sleep(0.001)
    return x * 3


def variable_model(x):
    """Simulates variable latency depending on input."""
    time.sleep(0.0001 * (x % 5))
    return x + 1


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestModelRegistration:
    """Test model registration and validation."""

    def test_register_and_list(self):
        bench = ModelBench()
        bench.register_model("fast", fast_model)
        bench.register_model("slow", slow_model)
        assert set(bench.registered_models) == {"fast", "slow"}

    def test_register_non_callable_raises(self):
        bench = ModelBench()
        with pytest.raises(TypeError, match="callable"):
            bench.register_model("bad", "not_a_function")

    def test_benchmark_unregistered_model_raises(self):
        bench = ModelBench()
        with pytest.raises(KeyError, match="not registered"):
            bench.benchmark("nonexistent", [1, 2, 3])


class TestBenchmark:
    """Test the benchmark runner produces valid results."""

    @pytest.fixture()
    def bench(self):
        cfg = BenchmarkConfig(iterations=20, throughput_duration=0.5, warmup_iterations=2)
        b = ModelBench(config=cfg)
        b.register_model("fast", fast_model)
        b.register_model("slow", slow_model)
        return b

    def test_benchmark_returns_result(self, bench: ModelBench):
        result = bench.benchmark("fast", list(range(10)))
        assert isinstance(result, BenchmarkResult)
        assert result.model_name == "fast"
        assert result.iterations == 20
        assert result.p50_latency > 0
        assert result.throughput_rps > 0

    def test_slow_model_has_higher_latency(self, bench: ModelBench):
        fast_result = bench.benchmark("fast", list(range(10)))
        slow_result = bench.benchmark("slow", list(range(10)))
        assert slow_result.p50_latency > fast_result.p50_latency

    def test_compare_models_sorted_by_p50(self, bench: ModelBench):
        results = bench.compare_models(["fast", "slow"], list(range(10)))
        assert len(results) == 2
        assert results[0].p50_latency <= results[1].p50_latency
        assert results[0].model_name == "fast"


class TestReportAndExport:
    """Test report generation and export."""

    def _make_result(self, name: str = "test_model") -> BenchmarkResult:
        return BenchmarkResult(
            model_name=name,
            iterations=100,
            p50_latency=0.005,
            p95_latency=0.008,
            p99_latency=0.012,
            mean_latency=0.006,
            median_latency=0.005,
            min_latency=0.003,
            max_latency=0.020,
            stdev_latency=0.002,
            throughput_rps=180.0,
            total_duration=1.5,
        )

    def test_generate_report_contains_model_name(self):
        result = self._make_result("alpha")
        report = ModelBench.generate_report([result])
        assert "alpha" in report
        assert "p50" in report

    def test_export_json(self):
        result = self._make_result()
        output = ModelBench.export_results([result], format="json")
        import json
        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["model_name"] == "test_model"

    def test_export_csv(self):
        result = self._make_result()
        output = ModelBench.export_results([result], format="csv")
        lines = output.strip().split("\n")
        assert len(lines) == 2  # header + 1 data row
        assert "model_name" in lines[0]

    def test_export_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            ModelBench.export_results([], format="xml")


class TestUtils:
    """Test utility functions."""

    def test_percentile_basic(self):
        data = list(range(1, 101))
        assert percentile(data, 50) == pytest.approx(50.5, abs=0.5)
        assert percentile(data, 99) == pytest.approx(99.5, abs=1.0)

    def test_latency_stats_keys(self):
        stats = latency_stats([0.1, 0.2, 0.15, 0.12, 0.18])
        for key in ("mean", "median", "stdev", "min", "max", "p50", "p95", "p99"):
            assert key in stats

    def test_format_duration_ranges(self):
        assert "us" in format_duration(0.0005)
        assert "ms" in format_duration(0.05)
        assert "s" in format_duration(2.5)
