# Parsing PDFs

## Overview

The PDF parser extracts PMI data from ICCIMA PDF reports using multiple strategies.

## Basic Usage

```python
from pathlib import Path
from pmi_analyzer.parser.pdf_parser import PDFParser

parser = PDFParser()
results = parser.parse(Path("data/pdfs/shamkh_khordad_1405.pdf"))

metrics = results[0]
print(f"Month: {metrics.month}")
print(f"PMI Total: {metrics.pmi_total}")
```

## Extraction Strategies

The parser tries multiple strategies in order:

1. **Table Extraction**: Structured table parsing via pdfplumber
2. **Spatial Clustering**: Word-coordinate based extraction
3. **Chart Labels**: Matches indicator words to nearby numbers
4. **Text Fallback**: Regex-based plain text extraction

## Handling RTL Text

The parser handles Persian Right-to-Left text:

```python
# Labels can be in standard or reversed format
label = "شاخص کل اقتصاد"  # Standard
label_reversed = "داصتقا لک خماش"  # Reversed (from PDF)
```

## Cross-Tab Tables

The parser detects and handles industry breakdown tables:

```python
# Automatically prefers aggregate rows over industry-specific rows
parser = PDFParser()
results = parser.parse(pdf_path)  # Extracts main PMI, not industry breakdown
```

## Month Detection

Automatic month detection from PDF text:

```python
parser = PDFParser()
results = parser.parse(pdf_path)
print(results[0].month)  # e.g., "1405-03"
```

## Error Handling

```python
from pmi_analyzer.exceptions import ParseError

parser = PDFParser()
try:
    results = parser.parse(Path("report.pdf"))
except ParseError as e:
    print(f"Parsing failed: {e}")
```
