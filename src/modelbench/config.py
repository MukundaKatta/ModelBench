"""Configuration for ModelBench benchmarking sessions."""

from __future__ import annotations

import os
from pydantic import BaseModel, Field


class BenchmarkConfig(BaseModel):
    """Global configuration for benchmark runs."""

    iterations: int = Field(
        default_factory=lambda: int(os.getenv("MODELBENCH_ITERATIONS", "100")),
        description="Number of iterations per benchmark run",
    )
    throughput_duration: float = Field(
        default_factory=lambda: float(os.getenv("MODELBENCH_THROUGHPUT_DURATION", "10.0")),
        description="Duration in seconds for throughput measurement",
    )
    warmup_iterations: int = Field(
        default_factory=lambda: int(os.getenv("MODELBENCH_WARMUP_ITERATIONS", "5")),
        description="Number of warmup iterations before benchmarking",
    )
    output_dir: str = Field(
        default_factory=lambda: os.getenv("MODELBENCH_OUTPUT_DIR", "benchmark_results"),
        description="Directory for exported results",
    )

    model_config = {"frozen": False}
