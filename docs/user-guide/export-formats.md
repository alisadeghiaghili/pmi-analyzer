# Export Formats

## Overview

PMI Analyzer supports exporting data to 4 formats: CSV, SQL, JSON, and Excel.

## CSV Export

```python
from pathlib import Path
from pmi_analyzer.data.exporter import export_to_csv

export_to_csv(results, Path("output/pmi_data.csv"))
```

**Features:**
- UTF-8 with BOM for Excel compatibility
- All indicators as columns
- NaN values preserved

## SQL Export

```python
from pmi_analyzer.data.exporter import export_to_sql

export_to_sql(
    results,
    Path("output/pmi_data.sql"),
    table_name="pmi_data"
)
```

**Features:**
- CREATE TABLE statement included
- INSERT statements for each row
- NULL handling for missing values
- Single-quote escaping

## JSON Export

```python
from pmi_analyzer.data.exporter import export_to_json

export_to_json(results, Path("output/pmi_data.json"))
```

**Features:**
- JSON array format
- Unicode preserved (no escaping)
- Configurable indentation
- null for missing values

## Excel Export

```python
from pmi_analyzer.data.exporter import export_to_excel

export_to_excel(
    results,
    Path("output/pmi_data.xlsx"),
    sheet_name="PMI Data"
)
```

**Requirements:**
```bash
pip install openpyxl
```

## Including Calculated Metrics

All export functions accept `include_calculated=True`:

```python
export_to_csv(
    results,
    Path("output/pmi_data.csv"),
    include_calculated=True  # Includes trends, composites, rolling means
)
```

## Merging with Historical Data

```python
from pmi_analyzer.data.exporter import merge_with_historical

# Merge new data with existing CSV
df = merge_with_historical(
    results,
    Path("data/shamkh_historical.csv")
)
```
