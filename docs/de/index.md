# PMI Analyzer (Deutsch)

Willkommen in der PMI Analyzer Dokumentation!

## Was ist PMI Analyzer?

**PMI Analyzer** ist ein Python-Paket zur automatischen Analyse des iranischen Einkaufsmanagerindex (PMI), auch bekannt als **Shamkh (شامخ)**.

## Installation

```bash
pip install pmi-analyzer
```

## Schnellstart

```python
from pathlib import Path
from pmi_analyzer.parser.pdf_parser import PDFParser

parser = PDFParser()
results = parser.parse(Path("data/pdfs/report.pdf"))

metrics = results[0]
print(f"Monat: {metrics.month}")
print(f"PMI Gesamt: {metrics.pmi_total}")
print(f"Produktion: {metrics.production}")
```

## Links

- [GitHub](https://github.com/alisadeghiaghili/pmi-analyzer)
- [Englische Dokumentation](../index.md)
