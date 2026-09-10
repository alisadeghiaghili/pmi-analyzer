"""PDF parser for Shamkh reports.

Multi-strategy extraction for ICCIMA PMI PDFs:
  1. Structured table extraction via pdfplumber (works for industry breakdown tables)
  2. Word-coordinate spatial clustering (works for chart-labeled data on pages 5-7)
  3. Chart label extraction (matches indicator words to nearby numeric values)
  4. Plain-text regex fallback
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pdfplumber

from pmi_analyzer.exceptions import ParseError
from pmi_analyzer.types import ShamkhMetrics

# ---------------------------------------------------------------------------
# Label -> ShamkhMetrics field mapping
# Includes: short forms, full-form names from real PDFs, reversed Persian labels
# ---------------------------------------------------------------------------
_ROW_LABEL_MAP: Dict[str, str] = {
    # --- headline ---
    "شامخ کل": "pmi_total",
    "شاخص کل": "pmi_total",
    "کل اقتصاد": "pmi_total",
    "شاخص کل اقتصاد": "pmi_total",
    # --- core indicators (short + full forms) ---
    "مقدار تولید": "production",
    "تولید محصول": "production",
    "میزان تولید": "production",
    "میزان تولید محصول": "production",
    "میزان تولید محصول یا ارائه خدمت": "production",
    "تولید محصول یا ارائه خدمت": "production",
    "سفارشات جدید": "new_orders",
    "میزان سفارشات": "new_orders",
    "میزان سفارشات جدید": "new_orders",
    "میزان سفارشات جدید مشتریان": "new_orders",
    "سفارشات جدید مشتریان": "new_orders",
    "سرعت انجام": "delivery_speed",
    "سرعت تحویل": "delivery_speed",
    "سرعت انجام و تحویل سفارش": "delivery_speed",
    "سرعت انجام و تحویل سفارشات": "delivery_speed",
    "موجودی مواد اولیه": "raw_materials_inv",
    "موجودی مواد": "raw_materials_inv",
    "موجودی مواد اولیه یا لوازم خریداری": "raw_materials_inv",
    "موجودی مواد اولیه یا لوازم خریداری شده": "raw_materials_inv",
    "موجودی مواد اولیه یا لوازم": "raw_materials_inv",
    "استخدام": "employment",
    "بکارگیری": "employment",
    "میزان استخدام": "employment",
    "میزان استخدام و بکارگیری": "employment",
    "میزان استخدام و بکارگیری نیروی انسانی": "employment",
    "بکارگیری نیروی انسانی": "employment",
    # --- auxiliary indicators ---
    "قیمت مواد اولیه": "input_price",
    "قیمت خرید": "input_price",
    "قیمت مواد اولیه یا لوازم خریداری شده": "input_price",
    "قیمت مواد اولیه یا لوازم": "input_price",
    "موجودی محصول نهایی": "final_goods_inv",
    "موجودی انبار": "final_goods_inv",
    "موجودی محصول نهایی در انبار": "final_goods_inv",
    "موجودی محصول نهایی در انبار یا کارهای در حال تکمیل": "final_goods_inv",
    "صادرات": "exports",
    "میزان صادرات": "exports",
    "میزان صادرات کالا یا خدمت": "exports",
    "صادرات کالا یا خدمت": "exports",
    "میزان فروش": "sales",
    "فروش کالا": "sales",
    "میزان فروش کالاها یا خدمات": "sales",
    "فروش کالاها یا خدمات": "sales",
    "انتظارات تولید": "production_expectations",
    "انتظارات فعالیت": "business_activity",
    "فعالیت کسب": "business_activity",
    "انتظارات در مورد میزان فعالیت اقتصادی": "business_activity",
    "انتظارات در مورد میزان فعالیت اقتصادی در ماه آینده": "business_activity",
    "فعالیت اقتصادی": "business_activity",
    # --- reversed Persian labels (from industry breakdown tables in real PDFs) ---
    "تیلاعف لک خماش": "pmi_total",
    "داصتقا لک خماش": "pmi_total",  # reversed شاخص کل اقتصاد
    "شامخ لک اچیعف": "pmi_total",  # reversed شاخص کل شامخ
    "تلاوصحم دیلوت رادقم": "production",
    "دیدج تاشرافس نازیم": "new_orders",
    "شرافس لیوحت و ماجنا تعرس": "delivery_speed",
    "هیلوا داوم یدوجوم": "raw_materials_inv",
    "یناسنا یورین یریگراکب و مادختسا نازیم": "employment",
    "هیلوا داوم دیرخ تمیق": "input_price",
    ")رابنا (لوصحم یدوجوم": "final_goods_inv",
    "لااک تارداص نازیم": "exports",
    "هدشدیلوت تلاوصحم تمیق": "sales",
    "یژرنا یاه لماح فرصم": "business_activity",
    "تلاوصحم شورف نازیم": "sales",
    "هدنیآ هام رد دیلوت تاراظتنا": "production_expectations",
    # Additional reversed labels from real PDF summary tables
    "تمدخ هئارا ای لوصحم دیلوت نازیم": "production",
    "نایرتشم دیدج تاشرافس نازیم": "new_orders",
    "شرافس سن لاییروحتوم مدايجدجنا تتعاشرسراف": "delivery_speed",
    "هدش یرادیرخ مزاول ای هیلوا داوم یدوجوم": "raw_materials_inv",
    "یناسنا یورین یریگراکب و مادختسا نازیم": "employment",
    "هدش یرادیرخ مزاول ای هیلوا داوم": "raw_materials_inv",
    "هدنیآ هام رد یداصتقا تیلاعف نازیم دروم رد": "business_activity",
    "تامدخ ای لااک تارداص نازیم": "exports",
    "هدش هئارا تامدخ و هدشدیلوت تلاوصحم": "sales",
}

# Industry-specific keywords that disqualify a row from being the aggregate/total
_INDUSTRY_KEYWORDS = {
    "سایر صنایع",
    "صنعت خودرو",
    "صنعت غذا",
    "صنعت دارو",
    "صنعت نفت",
    "صنعت فلزات",
    "صنعت سیمان",
    "صنعت شیمیایی",
    "صنعت منسوجات",
    "صنعت کاغذ",
    "صنعت لاستیک",
    "صنعت الکترونیک",
    "صنعت پتروشیمی",
    "صنعت هوافضا",
    "صنعت فناوری",
    "صنعت نساجی",
    "صنعت غذایی",
    "خودرو",
    "فلزات",
    "سیمان",
    "شیمیایی",
    "منسوجات",
    "پتروشیمی",
    "هوافضا",
    "نساجی",
    "غذایی",
    "لاستیک",
    "پلاستیک",
    "خانگی",
    "فلزی",
    "غیر فلزی",
}

# Aggregate/total qualifiers that indicate the main PMI row
_AGGREGATE_QUALIFIERS = {
    "کل",  # total/all
    "اقتصاد",  # economy
    "مجموع",  # aggregate
    "جمع",  # sum/total
    "عمومی",  # general
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


_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
_CORRUPT_TOKEN_RE = re.compile(r"\d+\.\d+\.\d+")
_YEAR_RE = re.compile(r"(?<!\d)(1[34]\d{2})(?!\d)")


def _normalize_numeric_text(text: str) -> str:
    """Normalise Persian/Arabic digits and decimal separators to ASCII.

    Args:
        text: Raw cell or token text.

    Returns:
        Text with ASCII digits, '.' as decimal point, and ',' stripped
        unless it is a single decimal comma (``45,9``).
    """
    cleaned = text.translate(_DIGIT_MAP)
    cleaned = cleaned.replace("٫", ".")  # Arabic decimal separator U+066B
    cleaned = cleaned.replace("،", ",")
    cleaned = cleaned.replace("/", ".")
    if re.match(r"^\d{1,3},\d{1,2}$", cleaned):
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    return cleaned


def _is_corrupted_numeric_token(token: str) -> bool:
    """Return True when a token looks like a double-drawn PDF cell.

    Live ICCIMA PDFs often emit stacked glyphs such as ``4511..42`` or
    ``951.49.2``. Those must not be parsed as PMI values.

    Args:
        token: A single line or whitespace-separated token.

    Returns:
        True if the token is treated as corrupt and must be skipped.
    """
    if ".." in token:
        return True
    if _CORRUPT_TOKEN_RE.search(token):
        return True
    return False


def _first_pmi_in_token(token: str) -> Optional[float]:
    """Extract the first plausible PMI value from a normalised token.

    Args:
        token: Token already passed through :func:`_normalize_numeric_text`.

    Returns:
        First decimal in ``[0, 100]``, else first non-year integer in range.
    """
    for match in re.findall(r"(\d{1,3}\.\d{1,2})", token):
        val = float(match)
        if 0.0 <= val <= 100.0:
            return val
    for match in re.findall(r"(?<!\d)(\d{1,3})(?!\d)", token):
        if _YEAR_RE.fullmatch(match):
            continue
        val = float(match)
        if 0.0 <= val <= 100.0:
            return val
    return None


def _to_float(cell: Optional[str]) -> Optional[float]:
    """Convert a table cell string to float; return None on failure.

    Handles multi-line cells and common ICCIMA PDF artefacts:
    Persian/Arabic digits, Arabic decimal separator (``٫``), stacked
    double-drawn tokens, and year labels mixed with values.

    The first clean PMI-range number in the cell wins (current month is
    typically listed first in summary rows).

    Args:
        cell: Raw cell text from pdfplumber, or None.

    Returns:
        PMI value in ``[0, 100]``, or None if no clean number is found.

    Example:
        >>> _to_float("45.9\\n١٤٠٥ دادرخ")
        45.9
        >>> _to_float("۴۷٫۶۳")
        47.63
        >>> _to_float("4511..42") is None
        True
    """
    if not cell:
        return None
    cleaned = cell.strip().translate(_DIGIT_MAP)
    cleaned = cleaned.replace("٫", ".").replace("،", ",").replace("/", ".")

    decimals: List[float] = []
    integers: List[float] = []
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for token in line.split():
            if _is_corrupted_numeric_token(token):
                continue
            if re.match(r"^\d{1,3},\d{1,2}$", token):
                token = token.replace(",", ".")
            else:
                token = token.replace(",", "")
            for match in re.findall(r"(\d{1,3}\.\d{1,2})", token):
                val = float(match)
                if 0.0 <= val <= 100.0:
                    decimals.append(val)
            for match in re.findall(r"(?<!\d)(\d{1,3})(?!\d)", token):
                if _YEAR_RE.fullmatch(match):
                    continue
                val = float(match)
                if 0.0 <= val <= 100.0:
                    integers.append(val)

    if decimals:
        return decimals[0]
    if integers:
        return integers[0]
    return None


def _normalize_label(text: str) -> str:
    """Normalize a label for matching: strip, collapse whitespace, normalize characters."""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    # Normalize Arabic Yeh/Keh to Persian equivalents for consistent matching
    t = t.replace("ي", "ی").replace("ك", "ک")
    return t


def _best_match(label: str) -> Optional[str]:
    """Return the ShamkhMetrics field name for a row label.

    Matching order:
      1. Exact key in the label map.
      2. Longest map key contained in the label (avoids short-key false hits).
      3. Collapsed-whitespace containment for reversed/malformed PDF labels.

    Args:
        label: Raw or normalised row label from a PDF table.

    Returns:
        Field name on :class:`~pmi_analyzer.types.ShamkhMetrics`, or None.

    Example:
        >>> _best_match("شامخ کل")
        'pmi_total'
        >>> _best_match("خبر جدید") is None
        True
    """
    if not label:
        return None
    normalized = _normalize_label(label)
    if normalized in _ROW_LABEL_MAP:
        return _ROW_LABEL_MAP[normalized]

    best_key = ""
    best_field = None
    for key, field in _ROW_LABEL_MAP.items():
        if key in normalized and len(key) > len(best_key):
            best_key = key
            best_field = field
    if best_field is not None:
        return best_field

    # Short label contained in a longer map key ("تولید" ⊂ "میزان تولید").
    if len(normalized) >= 3:
        best_key = ""
        for key, field in _ROW_LABEL_MAP.items():
            if normalized in key and len(key) > len(best_key):
                best_key = key
                best_field = field
        if best_field is not None:
            return best_field

    collapsed = normalized.replace(" ", "")
    best_key = ""
    for key, field in _ROW_LABEL_MAP.items():
        key_c = key.replace(" ", "")
        if len(key_c) < 4:
            continue
        if key_c in collapsed and len(key_c) > len(best_key):
            best_key = key_c
            best_field = field
    return best_field


def _is_aggregate_row(label: str) -> bool:
    """Check if a row label indicates an aggregate/total row.

    Args:
        label: Row label text.

    Returns:
        False when an industry keyword or an ``X - <industry>`` suffix is
        present; True for national/economy rows and empty fallbacks.

    Example:
        >>> _is_aggregate_row("شاخص کل اقتصاد")
        True
        >>> _is_aggregate_row("میزان تولید - پتروشیمی")
        False
    """
    if not label:
        return True

    normalized = _normalize_label(label)

    for industry in _INDUSTRY_KEYWORDS:
        if industry in normalized:
            return False

    # "indicator - something" is almost always an industry breakdown row.
    if " - " in normalized or "–" in normalized or "—" in normalized:
        return False

    for qualifier in _AGGREGATE_QUALIFIERS:
        if qualifier in normalized:
            return True

    return True


class PDFParser:
    """Parse Shamkh PDF reports and extract sub-indicator values.

    Multi-strategy extraction:
      1. Structured table extraction via pdfplumber
      2. Word-coordinate spatial clustering for chart-labeled data
      3. Chart label extraction (indicator words near numeric values)
      4. Plain-text regex fallback
    """

    def parse(self, pdf_path: Path, month: Optional[str] = None) -> List[ShamkhMetrics]:
        """Parse a Shamkh PDF report.

        Args:
            pdf_path: Path to the PDF file
            month: Month label override (e.g. '1402-01'); auto-detected if None

        Returns:
            List[ShamkhMetrics] -- typically a single element

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

            # Strategy 1: structured table extraction
            if all_tables:
                fields = self._parse_tables(all_tables)

            # Strategy 2: word-coordinate spatial clustering
            if not any(v is not None for v in fields.values()):
                fields = self._parse_spatial(pdf_path)

            # Strategy 3: chart label extraction
            if not any(v is not None for v in fields.values()):
                fields = self._parse_chart_labels(pdf_path)

            # Strategy 4: plain-text regex fallback
            if not any(v is not None for v in fields.values()):
                fields = self._parse_text_fallback(full_text)

            return [ShamkhMetrics(month=detected_month, **fields)]

        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse PDF: {e}") from e

    # ------------------------------------------------------------------
    # Strategy 1: Table-based extraction
    # ------------------------------------------------------------------

    def _parse_tables(self, tables: list) -> Dict[str, Optional[float]]:
        """Extract field values from all tables found in the PDF.

        Priority-based extraction:
        1. Summary tables (aggregate values) - extract first
        2. Cross-tab tables (industry breakdown) - only fill missing fields
        """
        fields: Dict[str, Optional[float]] = {}

        # First pass: extract from summary tables (non-cross-tab)
        for table in tables:
            if not table or len(table) < 2:
                continue
            if self._is_cross_tab_table(table):
                continue  # skip cross-tab tables in first pass

            table_fields = self._extract_from_table(table)
            for field, value in table_fields.items():
                if field not in fields:
                    fields[field] = value

        # Second pass: classic cross-tabs that repeat indicators and include
        # an aggregate row. Wide sector matrices are national-irrelevant.
        for table in tables:
            if not table or len(table) < 2:
                continue
            if not self._is_cross_tab_table(table):
                continue
            if self._is_wide_industry_matrix(table):
                continue

            table_fields = self._extract_from_table(table)
            for field, value in table_fields.items():
                if field not in fields:
                    fields[field] = value

        return fields

    def _is_wide_industry_matrix(self, table: list) -> bool:
        """Detect a sector matrix (one row per indicator, many industries).

        Args:
            table: pdfplumber table.

        Returns:
            True for wide industry matrices that must not feed national metrics.
        """
        if not table:
            return False
        widest = max(len(r) for r in table if r)
        if widest < 8:
            return False
        label_hits = sum(1 for r in table if r and len(r) > 1 and _best_match(str(r[-1] or "")))
        return label_hits >= 2

    def _is_cross_tab_table(self, table: list) -> bool:
        """Detect if a table is a cross-tab (industry breakdown) table.

        Cross-tab tables either repeat the same indicator label on multiple
        rows, or expose many industry columns with the label in the last
        column (RTL ICCIMA layout).

        Args:
            table: pdfplumber table (list of rows).

        Returns:
            True when the table should be treated as industry breakdown.
        """
        if len(table) < 3:
            return False

        field_counts: Dict[str, int] = {}
        for row in table:
            if not row:
                continue
            if len(row) > 1 and row[-1]:
                field = _best_match(str(row[-1]))
                if field:
                    field_counts[field] = field_counts.get(field, 0) + 1

        if any(count > 1 for count in field_counts.values()):
            return True

        # Wide RTL table with label in the last column and industry headers.
        widest = max((len(r) for r in table if r), default=0)
        if widest >= 8:
            for row in table:
                if row and row[-1] and _best_match(str(row[-1])):
                    return True
        return False

    def _current_value_index(self, value_cells: list, table: list, label_col: int) -> int:
        """Pick the index of the current-period numeric cell.

        Uses an explicit header token (``جاری`` / ``ماه جاری``) when present.
        Otherwise falls back to layout heuristics: first clean value for
        multi-period summary rows (ICCIMA lists current first), last value
        when only one comparable remains.

        Args:
            value_cells: Non-label cells for the current row.
            table: Full table (for header inspection).
            label_col: Index of the label column in the original row.

        Returns:
            Index into the parsed numeric list, or ``-1`` for the last item.
        """
        header_idx = self._header_current_index(table, label_col, len(value_cells))
        if header_idx is not None:
            return header_idx
        if value_cells and self._cell_marks_current_period(str(value_cells[0] or "")):
            return 0
        # Default layout: oldest → newest, current is the last numeric cell.
        return -1

    def _cell_marks_current_period(self, cell: str) -> bool:
        """Return True when a value cell embeds the report month name.

        ICCIMA summary rows often pack ``45.9\\n١٤٠٥ دادرخ`` (value + month)
        into the current-period column.

        Args:
            cell: Raw cell text.

        Returns:
            True if a known Jalali month name (or its RTL reversal) appears.
        """
        if not cell:
            return False
        for name in _MONTH_NAMES:
            if name in cell or name[::-1] in cell:
                return True
        return False

    def _header_current_index(
        self, table: list, label_col: int, n_values: int
    ) -> Optional[int]:
        """Locate the current-month column from a header row.

        Args:
            table: Full pdfplumber table.
            label_col: Label column index.
            n_values: Number of value columns on data rows.

        Returns:
            Index within value columns, or None if no header token found.
        """
        current_tokens = ("جاری", "ماه جاری", "دوره جاری", "این ماه")
        for row in table[:3]:
            if not row:
                continue
            value_positions = [i for i in range(len(row)) if i != label_col]
            for pos_i, col_i in enumerate(value_positions[:n_values]):
                cell = str(row[col_i] or "")
                norm = _normalize_label(cell)
                if any(tok in norm for tok in current_tokens):
                    return pos_i
        return None

    def _extract_from_table(self, table: list) -> Dict[str, Optional[float]]:
        """Extract field values from a single table.

        Skips percent-only columns, prefers aggregate rows, and selects the
        current-period column from headers when available.

        Args:
            table: pdfplumber table.

        Returns:
            Mapping of ShamkhMetrics field names to numeric values.
        """
        fields: Dict[str, Optional[float]] = {}
        field_matches: Dict[str, List[Tuple[int, Optional[float], str]]] = {}

        for row_idx, row in enumerate(table):
            if not row:
                continue

            field = None
            value_cells = None
            label_text = ""
            label_col = -1

            label_cell = row[0]
            if label_cell:
                field = _best_match(str(label_cell))
                if field is not None:
                    label_text = str(label_cell)
                    label_col = 0

            if field is None and len(row) > 1:
                last_cell = row[-1]
                if last_cell:
                    field = _best_match(str(last_cell))
                    if field is not None:
                        value_cells = list(row[:-1])
                        label_text = str(last_cell)
                        label_col = len(row) - 1

            if field is None:
                for col_idx, cell in enumerate(row):
                    if cell and col_idx != 0 and col_idx != len(row) - 1:
                        candidate = _best_match(str(cell))
                        if candidate is not None:
                            field = candidate
                            label_text = str(cell)
                            label_col = col_idx
                            break

            if field is None:
                continue

            if value_cells is None:
                value_cells = [c for c_idx, c in enumerate(row) if c_idx != label_col]

            # Drop percent/delta cells so they cannot override the level value.
            cleaned_cells = []
            for c in value_cells:
                if c is None:
                    continue
                text = str(c)
                if "%" in text or "٪" in text:
                    continue
                cleaned_cells.append(text)

            numeric_cells = [_to_float(c) for c in cleaned_cells]
            numeric_cells = [v for v in numeric_cells if v is not None]
            if not numeric_cells:
                continue

            idx = self._current_value_index(value_cells, table, label_col)
            if idx < 0 or idx >= len(numeric_cells):
                value = numeric_cells[-1]
            else:
                value = numeric_cells[idx]
            field_matches.setdefault(field, []).append((row_idx, value, label_text))

        for field, matches in field_matches.items():
            if field in fields:
                continue

            if len(matches) == 1:
                fields[field] = matches[0][1]
            else:
                best_value = self._select_aggregate_match(matches, table)
                if best_value is not None:
                    fields[field] = best_value

        return fields

        # Phase 2: Select best match for each field
        for field, matches in field_matches.items():
            if field in fields:
                continue

            if len(matches) == 1:
                # Single match - use it directly
                fields[field] = matches[0][1]
            else:
                # Multiple matches - prefer aggregate row
                best_value = self._select_aggregate_match(matches, table)
                if best_value is not None:
                    fields[field] = best_value

        return fields

    def _select_aggregate_match(
        self,
        matches: List[Tuple[int, Optional[float], str]],
        table: list,
    ) -> Union[None, float]:
        """Select the aggregate row value from multiple matches.

        Prefers rows without industry-specific qualifiers in their label.
        Falls back to first match if no clear aggregate row found.
        """
        # Filter to aggregate rows only
        aggregate_matches = [
            (row_idx, value, label) for row_idx, value, label in matches if _is_aggregate_row(label)
        ]

        if aggregate_matches:
            # Prefer first aggregate row (typically the main total)
            return aggregate_matches[0][1]

        # Fallback: if no clear aggregate row, use first match
        return matches[0][1] if matches else None

    # ------------------------------------------------------------------
    # Strategy 2: Word-coordinate spatial clustering
    # ------------------------------------------------------------------

    def _parse_spatial(self, pdf_path: Path) -> Dict[str, Optional[float]]:
        """Extract PMI values using word coordinates.

        Groups words by y-coordinate into rows, then matches indicator labels
        to numeric values within the same row. Handles chart-labeled data
        where values appear as text labels on chart data points.
        """
        fields: Dict[str, Optional[float]] = {}

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                if not words:
                    continue

                # Group words by y-coordinate (3px bucket)
                rows_by_y: Dict[int, list] = {}
                for w in words:
                    y_key = round(w["top"] / 3) * 3
                    if y_key not in rows_by_y:
                        rows_by_y[y_key] = []
                    rows_by_y[y_key].append(w)

                # For each row, try to match a known indicator label
                for y_key in sorted(rows_by_y.keys()):
                    row_words = sorted(rows_by_y[y_key], key=lambda w: w["x0"])
                    row_text = " ".join(w["text"] for w in row_words)

                    for label, field in _ROW_LABEL_MAP.items():
                        if field in fields:
                            continue
                        if _label_in_text(label, row_text):
                            # Find the first numeric value in this row
                            for w in row_words:
                                val = _to_float(w["text"])
                                if val is not None:
                                    fields[field] = val
                                    break

        return fields

    # ------------------------------------------------------------------
    # Strategy 3: Chart label extraction
    # ------------------------------------------------------------------

    def _parse_chart_labels(self, pdf_path: Path) -> Dict[str, Optional[float]]:
        """Extract values from chart data point labels.

        Finds indicator label words and matches them to the nearest numeric
        word within 80px vertically on the same page.
        """
        fields: Dict[str, Optional[float]] = {}

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                if not words:
                    continue

                # Collect all numeric words
                numeric_words: List[Tuple[dict, float]] = []
                for w in words:
                    val = _to_float(w["text"])
                    if val is not None:
                        numeric_words.append((w, val))

                # Find indicator label words
                indicator_positions: Dict[str, list] = {}
                for w in words:
                    text = w["text"]
                    for label, field in _ROW_LABEL_MAP.items():
                        if field in fields:
                            continue
                        if text in label or label in text:
                            indicator_positions.setdefault(field, []).append(w)

                # Match each indicator to the closest numeric value
                for field, positions in indicator_positions.items():
                    if field in fields:
                        continue
                    for pos_word in positions:
                        best_val = None
                        best_dist = float("inf")
                        for num_word, val in numeric_words:
                            dist = abs(num_word["top"] - pos_word["top"])
                            if dist < 80 and dist < best_dist:
                                best_dist = dist
                                best_val = val
                        if best_val is not None:
                            fields[field] = best_val
                            break

        return fields

    # ------------------------------------------------------------------
    # Strategy 4: Plain-text fallback
    # ------------------------------------------------------------------

    def _parse_text_fallback(self, text: str) -> Dict[str, Optional[float]]:
        """Fallback: scan plain text for keyword + adjacent number.

        The regex prefers decimal numbers (e.g. 45.9) over plain integers
        to avoid matching year digits like 14 from 1405.
        Uses [^\\d\\u06f0-\\u06f9] to skip over both ASCII and Persian digits
        in the gap between keyword and target number.
        """
        fields: Dict[str, Optional[float]] = {}
        # Character class that matches anything except ASCII/Persian digits
        _GAP = r"[^\d\u06f0-\u06f9]"
        for keyword, field in _ROW_LABEL_MAP.items():
            if field in fields:
                continue
            # Try decimal first (e.g. 45.9)
            pattern = re.compile(rf"{re.escape(keyword)}{_GAP}{{0,60}}(\d{{1,3}}\.\d{{1,2}})")
            match = pattern.search(text)
            if not match:
                # Fall back to integer (e.g. 45) but not part of a year
                pattern = re.compile(rf"{re.escape(keyword)}{_GAP}{{0,60}}(\d{{1,2}})(?!\d)")
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
        """Detect the report's Jalali month from Persian text.

        Month names must appear as standalone tokens (not as substrings of
        RTL gibberish such as ``دهدی`` for «می‌دهد``). Among valid pairs,
        the highest report year wins, then the earliest match in the text
        (page titles come first).

        Args:
            text: Full or partial extracted PDF text.

        Returns:
            ``YYYY-MM`` string, ``YYYY-??`` when only a year is found, or None.

        Example:
            >>> PDFParser()._detect_month("گزارش خرداد ۱۴۰۵ دوره ۹۳")
            '1405-03'
            >>> PDFParser()._detect_month("ندیدج 1405") is None
            True
        """
        if not text:
            return None

        letter = r"[\u0600-\u06FF]"
        year_pat = r"[۰-۹\d]{4}"
        candidates: List[Tuple[int, int, str]] = []  # (year, start, month_id)

        for name, num in _MONTH_NAMES.items():
            token = rf"(?<!{letter}){re.escape(name)}(?!{letter})"
            pattern = re.compile(
                rf"{token}[^\d]{{0,12}}{year_pat}|{year_pat}[^\d]{{0,12}}{token}"
            )
            for m in pattern.finditer(text):
                snippet = m.group(0).translate(_DIGIT_MAP)
                year_m = re.search(r"(1[34]\d{2})", snippet)
                if not year_m:
                    continue
                year = int(year_m.group(1))
                candidates.append((year, m.start(), f"{year_m.group(1)}-{num}"))

        if candidates:
            candidates.sort(key=lambda c: (-c[0], c[1]))
            return candidates[0][2]

        year_m = re.search(r"(1[34]\d{2})", text.translate(_DIGIT_MAP))
        if year_m:
            return f"{year_m.group(1)}-??"
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _label_in_text(label: str, text: str) -> bool:
    """Check if a label appears in text, handling reversed/malformed text."""
    if not label or not text:
        return False
    # Direct match
    if label in text:
        return True
    # Normalized match
    norm_label = _normalize_label(label)
    norm_text = _normalize_label(text)
    if norm_label in norm_text:
        return True
    # Collapsed-whitespace match
    collapsed_label = norm_label.replace(" ", "")
    collapsed_text = norm_text.replace(" ", "")
    if collapsed_label in collapsed_text or collapsed_text in collapsed_label:
        return True
    return False
