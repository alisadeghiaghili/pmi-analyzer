"""PDF parser for Shamkh reports."""

import re
from pathlib import Path
from typing import List, Optional, Dict
import pdfplumber
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.exceptions import ParseError

# ---------------------------------------------------------------------------
# Label -> ShamkhMetrics field mapping (Persian row labels from the tables)
# ---------------------------------------------------------------------------
_ROW_LABEL_MAP: Dict[str, str] = {
    # headline
    "شامخ کل": "pmi_total",
    "شاخص کل": "pmi_total",
    # core 5
    "مقدار تولید": "production",
    "تولید محصول": "production",
    "میزان تولید": "production",
    "سفارشات جدید": "new_orders",
    "میزان سفارشات": "new_orders",
    "سرعت انجام": "delivery_speed",
    "سرعت تحویل": "delivery_speed",
    "موجودی مواد اولیه": "raw_materials_inv",
    "موجودی مواد": "raw_materials_inv",
    "استخدام": "employment",
    "بکارگیری": "employment",
    # auxiliary
    "قیمت مواد اولیه": "input_price",
    "قیمت خرید": "input_price",
    "موجودی محصول نهایی": "final_goods_inv",
    "موجودی انبار": "final_goods_inv",
    "صادرات": "exports",
    "میزان صادرات": "exports",
    "قیمت محصول": "sales",  # قیمت فروش محصولات treated as sales proxy
    "میزان فروش": "sales",
    "فروش کالا": "sales",
    "انتظارات تولید": "production_expectations",
    "انتظارات فعالیت": "business_activity",
    "فعالیت کسب": "business_activity",
}

# Persian month names -> zero-padded month number
_MONTH_NAMES: Dict[str, str] = {
    "فروردین": "01",
    "اردیبهشت": "02",
    "خرداد": "03",
    "تیر": "04",
    "مرداد": "05",
    "شهریور": "06",
    "مهر": "07",
    "آبان": "08",
    "آذر": "09",
    "دی": "10",
    "بهمن": "11",
    "اسفند": "12",
}


def _to_float(cell: Optional[str]) -> Optional[float]:
    """Convert a table cell string to float; return None on failure."""
    if not cell:
        return None
    # normalise Arabic/Persian digits and separators
    cleaned = cell.strip()
    cleaned = cleaned.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    cleaned = cleaned.replace("/", ".").replace("،", "").replace(",", "")
    m = re.search(r"(\d{1,3}(?:\.\d{1,2})?)", cleaned)
    if m:
        val = float(m.group(1))
        return val if 0.0 <= val <= 100.0 else None
    return None


def _best_match(label: str) -> Optional[str]:
    """Return the ShamkhMetrics field name for a row label (partial match)."""
    if not label:
        return None
    label = label.strip()
    # exact lookup first
    if label in _ROW_LABEL_MAP:
        return _ROW_LABEL_MAP[label]
    # partial match
    for key, field in _ROW_LABEL_MAP.items():
        if key in label or label in key:
            return field
    return None


class PDFParser:
    """Parse Shamkh PDF reports and extract sub-indicator values."""

    def parse(self, pdf_path: Path, month: Optional[str] = None) -> List[ShamkhMetrics]:
        """
        Parse a Shamkh PDF report.

        Extraction strategy:
        1. Try pdfplumber structured table extraction on every page.
        2. For each table found, attempt to map row labels to ShamkhMetrics
           fields.  The *latest-month* column (rightmost numeric column) is
           used as the value (seasonal-adjusted preferred when available).
        3. Fall back to plain-text regex scan if no table is found.

        Args:
            pdf_path: Path to the PDF file
            month: Month label (e.g. '1402-01'); auto-detected if None

        Returns:
            List[ShamkhMetrics] – typically a single element

        Raises:
            ParseError: If parsing fails entirely
        """
        if not pdf_path.exists():
            raise ParseError(f"PDF file not found: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
                all_tables = []
                for page in pdf.pages:
                    tbls = page.extract_tables()
                    if tbls:
                        all_tables.extend(tbls)

            full_text = "\n".join(pages_text)
            detected_month = month or self._detect_month(full_text) or "unknown"

            fields: Dict[str, Optional[float]] = {}

            if all_tables:
                fields = self._parse_tables(all_tables)

            # fall back to plain-text regex
            if not any(v is not None for v in fields.values()):
                fields = self._parse_text_fallback(full_text)

            return [ShamkhMetrics(month=detected_month, **fields)]

        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse PDF: {e}") from e

    # ------------------------------------------------------------------
    # Table-based extraction
    # ------------------------------------------------------------------

    def _parse_tables(self, tables: list) -> Dict[str, Optional[float]]:
        """Extract field values from all tables found in the PDF."""
        fields: Dict[str, Optional[float]] = {}

        for table in tables:
            if not table or len(table) < 2:
                continue
            for row in table:
                if not row:
                    continue
                label_cell = row[0]
                field = _best_match(str(label_cell) if label_cell else "")
                if field is None or field in fields:
                    continue
                # Prefer the last non-None numeric cell (latest month)
                numeric_cells = [_to_float(str(c)) for c in row[1:] if c]
                numeric_cells = [v for v in numeric_cells if v is not None]
                if numeric_cells:
                    fields[field] = numeric_cells[-1]

        return fields

    # ------------------------------------------------------------------
    # Plain-text fallback
    # ------------------------------------------------------------------

    def _parse_text_fallback(self, text: str) -> Dict[str, Optional[float]]:
        """Fallback: scan plain text for keyword + adjacent number."""
        fields: Dict[str, Optional[float]] = {}
        for keyword, field in _ROW_LABEL_MAP.items():
            if field in fields:
                continue
            pattern = re.compile(
                rf"{re.escape(keyword)}[^\d]{{0,40}}(\d{{1,2}}(?:[\./]\d{{1,2}})?)"
            )
            match = pattern.search(text)
            if match:
                val = _to_float(match.group(1))
                if val is not None:
                    fields[field] = val
        return fields

    # ------------------------------------------------------------------
    # Month detection
    # ------------------------------------------------------------------

    def _detect_month(self, text: str) -> Optional[str]:
        """Detect Jalali month from Persian month names and 4-digit year."""
        for name, num in _MONTH_NAMES.items():
            # look for «فروردین ماه \u06f1\u06f4\u06f0\u06f5» or similar
            pattern = re.compile(
                rf"{re.escape(name)}[^\d{{0,10}}]?[\u06f0-\u06f9\d]{{4}}"
                rf"|[\u06f0-\u06f9\d]{{4}}[^\d]{{0,10}}?{re.escape(name)}"
            )
            m = pattern.search(text)
            if m:
                # extract 4-digit year (Arabic-Indic or ASCII)
                snippet = m.group(0)
                snippet_norm = snippet.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
                year_m = re.search(r"(1[34]\d{2})", snippet_norm)
                if year_m:
                    return f"{year_m.group(1)}-{num}"
        # last resort: bare 4-digit year
        year_m = re.search(r"(1[34]\d{2})", text)
        if year_m:
            return f"{year_m.group(1)}-??"
        return None
