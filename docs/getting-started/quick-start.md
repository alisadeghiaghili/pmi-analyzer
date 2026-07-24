# Quick Start

## Parse a PDF Report

```python
from pathlib import Path
from pmi_analyzer.parser.pdf_parser import PDFParser

# Initialize parser
parser = PDFParser()

# Parse a PMI PDF report
results = parser.parse(Path("data/pdfs/shamkh_khordad_1405.pdf"))

# Access the metrics
metrics = results[0]
print(f"Month: {metrics.month}")
print(f"PMI Total: {metrics.pmi_total}")
print(f"Production: {metrics.production}")
print(f"New Orders: {metrics.new_orders}")
```

## Export to Different Formats

```python
from pmi_analyzer.data.exporter import (
    export_to_csv,
    export_to_sql,
    export_to_json,
    export_to_excel,
)

# Export to CSV
export_to_csv(results, Path("output/pmi_data.csv"))

# Export to SQL
export_to_sql(results, Path("output/pmi_data.sql"), table_name="pmi_data")

# Export to JSON
export_to_json(results, Path("output/pmi_data.json"))

# Export to Excel (requires openpyxl)
export_to_excel(results, Path("output/pmi_data.xlsx"))
```

## Calculate Derived Indicators

```python
from pmi_analyzer.metrics.calculator import MetricsCalculator

calculator = MetricsCalculator()
df = calculator.calculate(results)

# View calculated columns
print(df.columns.tolist())

# Access trend data
print(df[["month", "production", "production_trend"]])
```

## CLI Usage

```bash
# Analyze a PDF
pmi-analyzer analyse --pdf data/pdfs/report.pdf

# Download and analyze latest report
pmi-analyzer analyse --download

# Generate charts
pmi-analyzer analyse --pdf report.pdf --plot --composite

# Build historical database
pmi-analyzer build-historical --csv data/shamkh_historical.csv
```
