"""PDF parser for Shamkh reports.

Multi-strategy extraction for ICCIMA PMI PDFs:
  1. Structured table extraction via pdfplumber (works for industry breakdown tables)
  2. Word-coordinate spatial clustering (works for chart-labeled data on pages 5-7)
  3. Chart label extraction (matches indicator words to nearby numeric values)
  4. Plain-text regex fallback
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import pdfplumber
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.exceptions import ParseError

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
    "قیمت محصول": "sales",
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
    "سایر صنایع",      # other industries
    "صنعت خودرو",      # automotive industry
    "صنعت غذا",        # food industry
    "صنعت دارو",       # pharmaceutical industry
    "صنعت نفت",        # oil industry
    "صنعت فلزات",      # metals industry
    "صنعت سیمان",      # cement industry
    "صنعت شیمیایی",    # chemical industry
    "صنعت منسوجات",    # textile industry
    "صنعت کاغذ",       # paper industry
    "صنعت لاستیک",     # rubber industry
    "صنعت الکترونیک",  # electronics industry
    "خودرو",           # automotive
    "فلزات",           # metals
    "سیمان",           # cement
    "شیمیایی",         # chemical
    "منسوجات",         # textile
}

# Aggregate/total qualifiers that indicate the main PMI row
_AGGREGATE_QUALIFIERS = {
    "کل",              # total/all
    "اقتصاد",          # economy
    "مجموع",           # aggregate
    "جمع",             # sum/total
    "عمومی",           # general
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
    """Convert a table cell string to float; return None on failure.

    Handles multi-line cells (e.g. '١٤\n54.8') by extracting the best valid number.
    Prefers decimal numbers over integers, as decimals are more likely to be
    the actual PMI values (e.g. 45.9) rather than year labels (e.g. 1405).
    """
    if not cell:
        return None
    cleaned = cell.strip()
    # normalise Arabic/Persian digits and separators
    cleaned = cleaned.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    # Replace Persian comma with ASCII comma for uniform handling
    cleaned = cleaned.replace("،", ",")
    # Handle comma as decimal separator (common in Persian locale)
    # If pattern is digit,digit (no dot), treat comma as decimal
    if re.match(r"^\d{1,3},\d{1,2}$", cleaned):
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    cleaned = cleaned.replace("/", ".")
    # Find all valid numbers
    # Decimal numbers first (e.g. 45.9), then integers (e.g. 48)
    decimal_matches = re.findall(r"(\d{1,3}\.\d{1,2})", cleaned)
    # Integer matches: 1-3 digits not followed by more digits
    int_matches = re.findall(r"(?<!\d)(\d{1,3})(?!\d)", cleaned)

    # Try decimals first (more likely to be actual PMI values)
    for match in reversed(decimal_matches):
        val = float(match)
        if 0.0 <= val <= 100.0:
            return val

    # Fall back to integers
    for match in reversed(int_matches):
        val = float(match)
        if 0.0 <= val <= 100.0:
            return val

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
    """Return the ShamkhMetrics field name for a row label (exact -> partial match)."""
    if not label:
        return None
    normalized = _normalize_label(label)
    # exact lookup
    if normalized in _ROW_LABEL_MAP:
        return _ROW_LABEL_MAP[normalized]
    # partial match (key in label or label in key)
    for key, field in _ROW_LABEL_MAP.items():
        if key in normalized or normalized in key:
            return field
    # last resort: strip all whitespace and try again
    collapsed = normalized.replace(" ", "")
    for key, field in _ROW_LABEL_MAP.items():
        if key.replace(" ", "") in collapsed or collapsed in key.replace(" ", ""):
            return field
    return None


def _is_aggregate_row(label: str) -> bool:
    """Check if a row label indicates an aggregate/total row (vs industry-specific).

    Returns True if the label has aggregate qualifiers or no industry qualifier.
    Returns False if the label contains an industry-specific keyword.
    """
    if not label:
        return True  # empty label treated as aggregate (fallback)

    normalized = _normalize_label(label)

    # Check for industry-specific qualifiers (disqualify)
    for industry in _INDUSTRY_KEYWORDS:
        if industry in normalized:
            return False

    # Check for aggregate qualifiers (prefer)
    for qualifier in _AGGREGATE_QUALIFIERS:
        if qualifier in normalized:
            return True

    # Default: treat as aggregate if no industry qualifier found
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

        # Second pass: fill missing fields from cross-tab tables
        for table in tables:
            if not table or len(table) < 2:
                continue
            if not self._is_cross_tab_table(table):
                continue  # skip summary tables in second pass

            table_fields = self._extract_from_table(table)
            for field, value in table_fields.items():
                if field not in fields:
                    fields[field] = value

        return fields

    def _is_cross_tab_table(self, table: list) -> bool:
        """Detect if a table is a cross-tab (industry breakdown) table.

        Cross-tab tables have:
        - Multiple rows with the same indicator label (one per industry)
        - Industry names in the header row (e.g., "سایر صنایع", "صنعت خودرو")
        """
        if len(table) < 3:
            return False

        # Count how many times each field appears in the table
        field_counts: Dict[str, int] = {}
        for row in table:
            if not row:
                continue
            # Check last column (RTL layout for cross-tab)
            if len(row) > 1 and row[-1]:
                field = _best_match(str(row[-1]))
                if field:
                    field_counts[field] = field_counts.get(field, 0) + 1

        # If any field appears more than once, it's a cross-tab table
        return any(count > 1 for count in field_counts.values())

    def _extract_from_table(self, table: list) -> Dict[str, Optional[float]]:
        """Extract field values from a single table."""
        fields: Dict[str, Optional[float]] = {}

        # Phase 1: Collect all matches per field
        field_matches: Dict[str, List[Tuple[int, Optional[float], str]]] = {}

        for row_idx, row in enumerate(table):
            if not row:
                continue

            field = None
            value_cells = None
            label_text = ""
            label_col = -1

            # Try label in first column (standard LTR layout)
            label_cell = row[0]
            if label_cell:
                field = _best_match(str(label_cell))
                if field is not None:
                    label_text = str(label_cell)
                    label_col = 0

            # Try label in last column (RTL layout, e.g. industry breakdown)
            if field is None and len(row) > 1:
                last_cell = row[-1]
                if last_cell:
                    field = _best_match(str(last_cell))
                    if field is not None:
                        value_cells = row[:-1]
                        label_text = str(last_cell)
                        label_col = len(row) - 1

            # Try all other columns (summary tables may have label in middle columns)
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

            # Build value cells: all columns except the label column
            if value_cells is None:
                value_cells = [c for c_idx, c in enumerate(row) if c_idx != label_col]

            numeric_cells = [_to_float(str(c)) for c in value_cells if c]
            numeric_cells = [v for v in numeric_cells if v is not None]

            if numeric_cells:
                # Summary tables with 4 period values: first value is current month
                # Cross-tab tables: last value is aggregate
                if len(numeric_cells) == 4:
                    value = numeric_cells[0]
                else:
                    value = numeric_cells[-1]
                field_matches.setdefault(field, []).append((row_idx, value, label_text))

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
    ) -> Optional[Optional[float]]:
        """Select the aggregate row value from multiple matches.

        Prefers rows without industry-specific qualifiers in their label.
        Falls back to first match if no clear aggregate row found.
        """
        # Filter to aggregate rows only
        aggregate_matches = [
            (row_idx, value, label)
            for row_idx, value, label in matches
            if _is_aggregate_row(label)
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
            pattern = re.compile(
                rf"{re.escape(keyword)}{_GAP}{{0,60}}(\d{{1,3}}\.\d{{1,2}})"
            )
            match = pattern.search(text)
            if not match:
                # Fall back to integer (e.g. 45) but not part of a year
                pattern = re.compile(
                    rf"{re.escape(keyword)}{_GAP}{{0,60}}(\d{{1,2}})(?!\d)"
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
        """Detect Jalali month from Persian month names and 4-digit year.

        Finds all month+year pairs and returns the one with the latest year
        (since reports often reference older base years like 1400).
        """
        best: Optional[str] = None
        best_year = 0
        for name, num in _MONTH_NAMES.items():
            pattern = re.compile(
                rf"{re.escape(name)}[^\d]{{0,10}}[\u06f0-\u06f9\d]{{4}}"
                rf"|[\u06f0-\u06f9\d]{{4}}[^\d]{{0,10}}{re.escape(name)}"
            )
            for m in pattern.finditer(text):
                snippet = m.group(0)
                snippet_norm = snippet.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
                year_m = re.search(r"(1[34]\d{2})", snippet_norm)
                if year_m:
                    year = int(year_m.group(1))
                    if year > best_year:
                        best_year = year
                        best = f"{year_m.group(1)}-{num}"
        if best:
            return best
        # last resort: bare 4-digit year (take the latest)
        year_m = re.search(r"(1[34]\d{2})", text)
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
