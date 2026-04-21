> **Related work:** Primary development for this problem space has converged on **[evalharness](https://github.com/MukundaKatta/evalharness)** — prompts, agents, and RAG-pipeline red-teaming, regression, and CI testing. This repo remains available; check the canonical repo first for the latest tooling.

---# ModelBench — Model serving benchmark toolkit — latency p50/p95/p99, throughput, and model comparison

Model serving benchmark toolkit — latency p50/p95/p99, throughput, and model comparison.

## Why ModelBench

ModelBench exists to make this workflow practical. Model serving benchmark toolkit — latency p50/p95/p99, throughput, and model comparison. It favours a small, inspectable surface over sprawling configuration.

## Features

- `BenchmarkResult` — exported from `src/modelbench/core.py`
- Included test suite
- Dedicated documentation folder

## Tech Stack

- **Runtime:** Python
- **Tooling:** Pydantic

## How It Works

The codebase is organised into `docs/`, `src/`, `tests/`. The primary entry points are `src/modelbench/core.py`, `src/modelbench/__init__.py`. `src/modelbench/core.py` exposes `BenchmarkResult` — the core types that drive the behaviour.

## Getting Started

```bash
pip install -e .
```

## Usage

```python
from modelbench.core import BenchmarkResult

instance = BenchmarkResult()
# See the source for the full API
```

## Project Structure

```
ModelBench/
├── .env.example
├── CONTRIBUTING.md
├── Makefile
├── README.md
├── docs/
├── pyproject.toml
├── src/
├── tests/
```