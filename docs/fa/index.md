# تحلیلگر شامخ

به مستندات تحلیلگر شامخ خوش آمدید!

## شامخ چیست؟

**تحلیلگر شامخ** یک پکیج پایتون برای تحلیل خودکار شاخص مدیران خرید ایران (شامخ) است.

## نصب

```bash
pip install pmi-analyzer
```

## استفاده سریع

```python
from pathlib import Path
from pmi_analyzer.parser.pdf_parser import PDFParser

parser = PDFParser()
results = parser.parse(Path("data/pdfs/report.pdf"))

metrics = results[0]
print(f"ماه: {metrics.month}")
print(f"شاخص کل: {metrics.pmi_total}")
print(f"تولید: {metrics.production}")
```

## پیوندها

- [GitHub](https://github.com/alisadeghiaghili/pmi-analyzer)
- [مستندات انگلیسی](../index.md)
