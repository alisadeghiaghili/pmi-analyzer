# PMI Analyzer (شامخ)

Welcome to the PMI Analyzer documentation!

## What is PMI Analyzer?

**PMI Analyzer** is a Python package for automatic analysis of Iran's Purchasing Managers' Index (PMI), known as **Shamkh (شامخ)**.

It provides:

- **PDF Parsing**: Extract PMI data from ICCIMA PDF reports
- **Data Analysis**: Calculate trends, composites, and rolling means
- **Visualization**: Generate interactive charts
- **Export**: Save data to CSV, SQL, JSON, or Excel

## Quick Start

```python
from pathlib import Path
from pmi_analyzer.parser.pdf_parser import PDFParser
from pmi_analyzer.metrics.calculator import MetricsCalculator

# Parse a PMI PDF report
parser = PDFParser()
results = parser.parse(Path("data/pdfs/report.pdf"))

# Access the metrics
metrics = results[0]
print(f"PMI Total: {metrics.pmi_total}")
print(f"Production: {metrics.production}")
```

## Installation

```bash
pip install pmi-analyzer
```

For Excel export support:

```bash
pip install pmi-analyzer[excel]
```

## Documentation

- [Getting Started](getting-started/installation.md) - Installation and setup
- [What is PMI?](concepts/what-is-pmi.md) - Understanding PMI
- [User Guide](user-guide/parsing-pdfs.md) - How to use the package
- [Export Formats](user-guide/export-formats.md) - CSV, SQL, JSON, Excel export

## Links

- [GitHub Repository](https://github.com/alisadeghiaghili/pmi-analyzer)
- [PyPI Package](https://pypi.org/project/pmi-analyzer/)
- [Issue Tracker](https://github.com/alisadeghiaghili/pmi-analyzer/issues)
