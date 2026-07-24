# Contributing to PMI Analyzer

Thank you for considering contributing to PMI Analyzer! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/pmi-analyzer.git
   cd pmi-analyzer
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip or uv package manager

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=pmi_analyzer --cov-report=html

# Run specific test file
pytest tests/unit/test_pdf_parser.py -v
```

### Code Quality Tools

```bash
# Format code with black
black .

# Check linting with ruff
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type checking with mypy
mypy pmi_analyzer/
```

## Code Style

We use [Black](https://black.readthedocs.io/) for code formatting and [Ruff](https://docs.astral.sh/ruff/) for linting.

### Key Rules

1. **Line Length**: Maximum 100 characters
2. **String Quotes**: Double quotes for strings
3. **Import Sorting**: Handled by ruff
4. **Type Hints**: Required for all public functions
5. **Docstrings**: Google style for all public APIs

### Example Docstring

```python
def export_to_csv(
    metrics: List[ShamkhMetrics],
    output_path: Path,
    include_calculated: bool = False,
) -> Path:
    """Export ShamkhMetrics list to a CSV file.

    Args:
        metrics: List of parsed ShamkhMetrics to export.
        output_path: Path for the output CSV file.
        include_calculated: If True, include calculated metrics.

    Returns:
        Path to the created CSV file.

    Example:
        >>> from pmi_analyzer.data.exporter import export_to_csv
        >>> export_to_csv([metrics], Path("output.csv"))
        PosixPath('output.csv')
    """
```

## Pull Request Process

1. **Update Tests**: Add tests for any new functionality
2. **Update Documentation**: Update docstrings and README if needed
3. **Run Quality Checks**:
   ```bash
   black --check .
   ruff check .
   mypy pmi_analyzer/
   pytest tests/
   ```
4. **Commit Messages**: Use conventional commits format:
   - `feat: add new feature`
   - `fix: bug fix`
   - `docs: documentation changes`
   - `test: add tests`
   - `refactor: code refactoring`
5. **Create PR**: Target the `main` branch with a clear description

### PR Title Format

```
feat(parser): add support for new PDF format
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`

## Reporting Bugs

Use GitHub Issues with the following template:

**Title**: `[BUG] Brief description`

**Description**:
- What happened
- What you expected
- Steps to reproduce
- Environment (OS, Python version)

## Suggesting Features

Use GitHub Issues with the following template:

**Title**: `[FEATURE] Brief description`

**Description**:
- Use case
- Proposed solution
- Alternatives considered

## Questions?

Open a GitHub Discussion or issue for any questions.
