"""PDF parser for Shamkh reports."""

import re
from pathlib import Path
from typing import List, Optional
import pdfplumber
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.exceptions import ParseError


class PDFParser:
    """Parse Shamkh PDF reports and extract sub-indicator values."""

    # Regex patterns for extracting PMI values (float between 0-100)
    PMI_PATTERN = re.compile(r"(\d{1,2}(?:\.\d{1,2})?)")

    # Keyword mapping: PDF keyword -> ShamkhMetrics field
    FIELD_KEYWORDS = {
        "تولید": "production",
        "سفارشات جدید": "new_orders",
        "فروش": "sales",
        "موجودی مواد اولیه": "raw_materials_inv",
        "موجودی محصول نهایی": "final_goods_inv",
        "قیمت خرید": "input_price",
        "انتظارات تولید": "production_expectations",
        "اشتغال": "employment",
        "صادرات": "exports",
        "سرعت تحویل": "delivery_speed",
        "فعالیت": "business_activity",
    }

    def parse(self, pdf_path: Path, month: Optional[str] = None) -> List[ShamkhMetrics]:
        """
        Parse a Shamkh PDF report.

        Args:
            pdf_path: Path to the PDF file
            month: Month label (e.g. '1402-01'); auto-detected if None

        Returns:
            List of ShamkhMetrics extracted from the PDF

        Raises:
            ParseError: If parsing fails
        """
        if not pdf_path.exists():
            raise ParseError(f"PDF file not found: {pdf_path}")

        try:
            metrics_dict = {field: None for field in self.FIELD_KEYWORDS.values()}

            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)

            for keyword, field in self.FIELD_KEYWORDS.items():
                value = self._extract_value(text, keyword)
                if value is not None:
                    metrics_dict[field] = value

            detected_month = month or self._detect_month(text) or "unknown"

            return [
                ShamkhMetrics(month=detected_month, **metrics_dict)
            ]

        except Exception as e:
            raise ParseError(f"Failed to parse PDF: {e}") from e

    def _extract_value(self, text: str, keyword: str) -> Optional[float]:
        """Extract PMI value following a keyword in text."""
        pattern = re.compile(rf"{re.escape(keyword)}[^\d]{{0,30}}(\d{{1,2}}(?:\.\d{{1,2}})?)")
        match = pattern.search(text)
        if match:
            val = float(match.group(1))
            if 0 <= val <= 100:
                return val
        return None

    def _detect_month(self, text: str) -> Optional[str]:
        """Try to detect the report month from PDF text."""
        month_pattern = re.compile(r"(\d{4})[^\d](\d{1,2})")
        match = month_pattern.search(text)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}"
        return None
