# PMI Analyzer (شامخ آنالایزر)

[![CI](https://github.com/alisadeghiaghili/pmi-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/alisadeghiaghili/pmi-analyzer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-261230.svg)](https://github.com/astral-sh/ruff)

Tool for automatic analysis of Shamkh (PMI) and Iranian economic indicators.

## Features
- Download latest Shamkh report from iccima.ir
- Parse PDF with pdfplumber
- Calculate all Shamkh sub-indicators
- Interactive Plotly charts
- Dual-language support: Persian (fa) / English (en)

## All Shamkh Sub-Indicators

| # | Sub-Indicator | فارسی |
|---|---|---|
| 1 | Production | تولید |
| 2 | New Orders | سفارشات جدید |
| 3 | Sales | سنجه فروش محصولات |
| 4 | Raw Materials Inventory | موجودی مواد اولیه |
| 5 | Final Goods Inventory | موجودی محصول نهایی در انبار |
| 6 | Input Price | قیمت خرید مواد اولیه |
| 7 | Production Expectations | انتظارات تولید برای ماه آینده |
| 8 | Employment | اشتغال |
| 9 | Exports | صادرات |
| 10 | Delivery Speed | سرعت تحویل سفارشات |
| 11 | Business Activity | فعالیت کسب‌وکار |

## Composite Indicators
- **Demand Pressure** = (New Orders + Sales + Exports) / 3
- **Production Capacity** = (Production + Raw Materials + Final Goods) / 3
- **Labor Market Stress** = 100 - Employment
- **Recession Severity** = 50 - Shamkh Total
- **Forward Confidence** = Production Expectations
- **Supply Chain Stress** = Raw Materials < 45 ∧ New Orders < 40

## Install
```bash
pip install -e .
```

## Usage
```bash
# Download latest report and analyze
pmi-analyzer analyse --download --plot

# Analyze existing PDF
pmi-analyzer analyse --pdf report.pdf --plot

# Composite indicators chart
pmi-analyzer analyse --pdf report.pdf --composite

# Switch language
pmi-analyzer --locale en analyse --download --plot
```

## Development
```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint + format
ruff check pmi_analyzer/
black pmi_analyzer/ tests/
```

## i18n
```python
from pmi_analyzer.i18n import set_locale

set_locale("fa")  # Persian (default)
set_locale("en")  # English
```
