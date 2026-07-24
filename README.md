# PMI Analyzer (شامخ)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-235%20passing-brightgreen)](#testing)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**PMI Analyzer** is a Python package for automatic analysis of Iran's Purchasing Managers' Index (PMI), known as **Shamkh (شامخ)**. It downloads, parses, analyzes, and visualizes PMI data from the Iran Chamber of Commerce (ICCIMA).

[Documentation](https://alisadeghiaghili.github.io/pmi-analyzer/) | [فارسی](https://alisadeghiaghili.github.io/pmi-analyzer/fa/) | [Deutsch](https://alisadeghiaghili.github.io/pmi-analyzer/de/)

---

## What is PMI?

### The Purchasing Managers' Index

The **Purchasing Managers' Index (PMI)** is a key economic indicator derived from monthly surveys of private sector companies. It measures the health of the manufacturing and service sectors.

### How PMI Works

PMI is calculated from five sub-indicators, each weighted equally (20%):

| Indicator | Weight | What it Measures |
|-----------|--------|------------------|
| **New Orders** | 20% | Future demand |
| **Production** | 20% | Current output |
| **Employment** | 20% | Hiring activity |
| **Supplier Delivery Times** | 20% | Supply chain speed |
| **Stock of Items Purchased** | 20% | Inventory levels |

### Interpreting PMI Values

| Value | Meaning |
|-------|---------|
| **> 50** | **Expansion** - Economy is growing |
| **= 50** | **Neutral** - No change |
| **< 50** | **Contraction** - Economy is shrinking |

The further from 50, the stronger the trend. For example:
- PMI = 55.0 → Strong expansion
- PMI = 45.0 → Moderate contraction
- PMI = 60.0 → Very strong expansion

---

## Iran's PMI: Shamkh (شامخ)

### About Shamkh

**Shamkh (شامخ)** is Iran's official PMI, published monthly by the **Iran Chamber of Commerce, Industries, Mines and Agriculture (ICCIMA)** since 2019.

### Shamkh Sub-Indicators

Iran's Shamkh includes 11 sub-indicators:

| English Name | Persian Name | Description |
|--------------|--------------|-------------|
| PMI Total | شاخص کل | Composite headline index |
| Production | تولید | Manufacturing output |
| New Orders | سفارشات جدید | Customer orders received |
| Sales | فروش | Product sales volume |
| Raw Materials Inventory | موجودی مواد اولیه | Raw material stock |
| Final Goods Inventory | موجودی محصول نهایی | Finished goods stock |
| Input Price | قیمت مواد اولیه | Purchase prices |
| Production Expectations | انتظارات تولید | Future production outlook |
| Employment | استخدام | Hiring activity |
| Exports | صادرات | Export volume |
| Delivery Speed | سرعت تحویل | Supplier delivery times |

### Data Source

Data is sourced from ICCIMA's official reports:
- Website: [iccima.ir](https://iccima.ir)
- Reports are published as PDF files in Persian (Farsi)

---

## Quick Start

### Installation

```bash
pip install pmi-analyzer
```

Or install from source:

```bash
git clone https://github.com/alisadeghiaghili/pmi-analyzer.git
cd pmi-analyzer
pip install -e .
```

### Basic Usage

```python
from pathlib import Path
from pmi_analyzer.parser.pdf_parser import PDFParser
from pmi_analyzer.metrics.calculator import MetricsCalculator

# Parse a PMI PDF report
parser = PDFParser()
results = parser.parse(Path("data/pdfs/shamkh_khordad_1405.pdf"))

# Access the metrics
metrics = results[0]
print(f"Month: {metrics.month}")
print(f"PMI Total: {metrics.pmi_total}")
print(f"Production: {metrics.production}")
print(f"New Orders: {metrics.new_orders}")

# Calculate derived indicators
calculator = MetricsCalculator()
df = calculator.calculate(results)
print(df.head())
```

### Export to Different Formats

```python
from pmi_analyzer.data.exporter import (
    export_to_csv,
    export_to_sql,
    export_to_json,
    export_to_excel,
)

# Export to CSV
export_to_csv(results, Path("output/pmi_data.csv"))

# Export to SQL (for database import)
export_to_sql(results, Path("output/pmi_data.sql"), table_name="pmi_data")

# Export to JSON
export_to_json(results, Path("output/pmi_data.json"))

# Export to Excel
export_to_excel(results, Path("output/pmi_data.xlsx"))
```

### CLI Usage

```bash
# Analyze a PDF
pmi-analyzer analyse --pdf data/pdfs/report.pdf

# Download and analyze latest report
pmi-analyzer analyse --download

# Build historical database
pmi-analyzer build-historical --csv data/shamkh_historical.csv

# Generate charts
pmi-analyzer analyse --pdf report.pdf --plot --composite
```

---

## Features

### PDF Parsing

- Multi-strategy extraction (table, spatial, chart, text fallback)
- RTL (Right-to-Left) Persian text support
- Industry breakdown detection
- Automatic month detection

### Historical Data Management

- Automatic deduplication
- Merge new data with existing CSV
- Chronological sorting

### Analysis & Visualization

- 11 sub-indicator calculations
- Trend analysis (expansion/contraction)
- Rolling means (3-month)
- Composite indicators:
  - Demand Pressure Index
  - Production Capacity Index
  - Labor Market Stress
  - Price Inflation Signal
  - Recession Severity Index
  - Supply Chain Stress

### Export Formats

- **CSV** (UTF-8 BOM for Excel compatibility)
- **SQL** (CREATE TABLE + INSERT statements)
- **JSON** (structured data)
- **Excel** (.xlsx with openpyxl)

---

## Project Structure

```
pmi-analyzer/
├── pmi_analyzer/              # Main package
│   ├── cli.py                 # Command-line interface
│   ├── types.py               # Data classes
│   ├── exceptions.py          # Custom exceptions
│   ├── i18n.py                # Internationalization
│   ├── parser/
│   │   └── pdf_parser.py      # PDF parsing engine
│   ├── data/
│   │   ├── loader.py          # CSV loading
│   │   └── exporter.py        # Multi-format export
│   ├── metrics/
│   │   ├── calculator.py      # Metric calculations
│   │   └── validators.py      # Data validation
│   ├── scraper/
│   │   ├── archive_scraper.py # Historical discovery
│   │   ├── batch_downloader.py# PDF downloading
│   │   └── batch_parser.py    # Batch parsing
│   ├── downloader/
│   │   └── iccima_downloader.py # Latest report download
│   └── plotter/
│       └── plotly_plotter.py   # Chart generation
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── data/                      # Data files
│   ├── pdfs/                  # Downloaded PDFs
│   └── shamkh_historical.csv  # Historical data
├── docs/                      # Documentation (MkDocs)
├── scripts/                   # Utility scripts
├── pyproject.toml             # Project configuration
├── LICENSE                    # MIT License
├── CONTRIBUTING.md            # Contribution guide
├── CODE_OF_CONDUCT.md         # Code of conduct
└── README.md                  # This file
```

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=pmi_analyzer --cov-report=html

# Run specific test file
pytest tests/unit/test_pdf_parser.py -v

# Run edge case tests
pytest tests/unit/test_pdf_parser.py -k "Edge" -v
```

### Test Coverage

- **235 tests** covering:
  - PDF parser (multi-line cells, RTL text, cross-tab detection)
  - Exporter (CSV, SQL, JSON, Excel)
  - Calculator (trends, composites, rolling means)
  - Scraper (link discovery, deduplication)
  - Edge cases (boundary values, special characters, empty inputs)

---

## Documentation

Full documentation is available at:
- [English](https://alisadeghiaghili.github.io/pmi-analyzer/)
- [فارسی (Farsi)](https://alisadeghiaghili.github.io/pmi-analyzer/fa/)
- [Deutsch (German)](https://alisadeghiaghili.github.io/pmi-analyzer/de/)

### Building Docs Locally

```bash
pip install mkdocs-material mkdocs-static-i18n
mkdocs serve
# Open http://localhost:8000
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone and install
git clone https://github.com/alisadeghiaghili/pmi-analyzer.git
cd pmi-analyzer
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run quality checks
black --check .
ruff check .
mypy pmi_analyzer/
pytest tests/
```

---

## Roadmap

- [ ] Add time-series forecasting
- [ ] Industry-specific analysis
- [ ] Interactive dashboard (Streamlit/Panel)
- [ ] API endpoint for real-time data
- [ ] Mobile app notifications

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Iran Chamber of Commerce (ICCIMA)](https://iccima.ir) for PMI data
- [R for Data Science](https://r4ds.had.co.nz/) for documentation inspiration
- All contributors and the Persian developer community

---

## Contact

- **Author**: Ali Sadeghi
- **GitHub**: [alisadeghiaghili](https://github.com/alisadeghiaghili)
- **Issues**: [GitHub Issues](https://github.com/alisadeghiaghili/pmi-analyzer/issues)

---

<div dir="rtl">

## شامخ چیست؟

**شامخ** (شاخص مدیران خرید) شاخصی اقتصادی است که هر ماه توسط **اتاق بازرگانی، صنایع، معادن و کشاورزی ایران (ایکاما)** منتشر می‌شود.

### تفسیر مقادیر

| مقدار | معنی |
|-------|------|
| **> ۵۰** | **رشد** - اقتصاد در حال گسترش است |
| **= ۵۰** | **خنثی** - بدون تغییر |
| **< ۵۰** | **رکود** - اقتصاد در حال کوچک شدن است |

### زیرشاخص‌های شامخ

شامخ از ۱۱ زیرشاخص تشکیل شده است:
- تولید
- سفارشات جدید
- فروش
- موجودی مواد اولیه
- موجودی محصول نهایی
- قیمت مواد اولیه
- انتظارات تولید
- استخدام
- صادرات
- سرعت تحویل
- شاخص کل

برای اطلاعات بیشتر به [مستندات فارسی](https://alisadeghiaghili.github.io/pmi-analyzer/fa/) مراجعه کنید.

</div>
