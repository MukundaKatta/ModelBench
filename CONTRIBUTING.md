# Contributing to ModelBench

Thank you for your interest in contributing to ModelBench! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/officethree/ModelBench.git
   cd ModelBench
   ```

2. Install in development mode:

   ```bash
   make dev
   ```

3. Run the test suite:

   ```bash
   make test
   ```

## How to Contribute

### Reporting Bugs

- Open a GitHub Issue with a clear title and description.
- Include steps to reproduce, expected vs. actual behavior, and your Python version.

### Suggesting Features

- Open a GitHub Issue tagged as a feature request.
- Describe the use case and how it benefits model serving benchmarks.

### Submitting Pull Requests

1. Fork the repo and create a feature branch from `main`.
2. Write tests for any new functionality.
3. Ensure all tests pass: `make test`
4. Ensure code passes linting: `make lint`
5. Submit a PR with a clear description of the changes.

## Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.
- Target Python 3.10+.
- Use type annotations where possible.
- Follow the existing code structure.

## Project Structure

```
src/modelbench/
  __init__.py     # Public API exports
  core.py         # ModelBench class and BenchmarkResult
  config.py       # BenchmarkConfig (pydantic)
  utils.py        # Timing, percentile, formatting helpers
tests/
  test_core.py    # Unit tests
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
