"""Unit tests for PDF parser."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pmi_analyzer.parser.pdf_parser import (
    PDFParser,
    _to_float,
    _best_match,
    _normalize_label,
    _label_in_text,
    _is_aggregate_row,
)


# ------------------------------------------------------------------ #
#  _to_float
# ------------------------------------------------------------------ #


class TestToFloat:
    def test_ascii_integer(self):
        assert _to_float("45") == 45.0

    def test_ascii_decimal(self):
        assert _to_float("45.7") == 45.7

    def test_persian_digits(self):
        assert _to_float("۴۵.۷") == 45.7

    def test_arabic_digits(self):
        assert _to_float("٤٥.٧") == 45.7

    def test_comma_separator(self):
        assert _to_float("45,7") == 45.7

    def test_persian_comma(self):
        assert _to_float("۴۵،۷") == 45.7

    def test_empty_string(self):
        assert _to_float("") is None

    def test_none(self):
        assert _to_float(None) is None

    def test_no_number(self):
        assert _to_float("abc") is None

    def test_out_of_range(self):
        assert _to_float("150") is None

    def test_zero(self):
        assert _to_float("0") == 0.0

    def test_hundred(self):
        assert _to_float("100") == 100.0

    def test_over_hundred(self):
        assert _to_float("101") is None

    def test_whitespace(self):
        assert _to_float(" 45.7 ") == 45.7

    def test_number_with_text(self):
        assert _to_float("45.7 extra") == 45.7

    def test_slash_separator(self):
        assert _to_float("45/7") == 45.7

    # --- Edge cases ---

    def test_multiline_cell_prefers_decimal(self):
        """Multi-line cell: prefer decimal over year digits."""
        assert _to_float("45.9\n١٤٠٥ دادرخ") == 45.9

    def test_multiline_cell_last_number(self):
        """Multi-line cell: last decimal is the actual value."""
        assert _to_float("١٤\n54.8") == 54.8

    def test_year_in_text_ignored(self):
        """Year-like numbers (1405) should not be returned as PMI values."""
        assert _to_float("1405") is None  # 3 digits, > 100

    def test_mixed_persian_english_digits(self):
        """Mixed Persian and English digits in same string."""
        assert _to_float("۴۵.7") == 45.7

    def test_negative_value_extracts_number(self):
        """Negative value extracts the number (PMI values are always positive)."""
        assert _to_float("-5.0") == 5.0

    def test_decimal_only(self):
        """Just a decimal point with no digits."""
        assert _to_float(".") is None

    def test_multiple_commas(self):
        """Multiple commas treated as thousands separators."""
        assert _to_float("1,234") is None  # > 100 after removing commas

    def test_leading_trailing_dots(self):
        """Leading/trailing dots don't break extraction."""
        assert _to_float(".45.7") == 45.7

    def test_nested_parentheses(self):
        """Numbers in parentheses."""
        assert _to_float("(45.7)") == 45.7

    def test_label_with_dot_prefix(self):
        """Label with .8 prefix extracts the decimal."""
        assert _to_float(".8 د اصتقا") == 8.0


# ------------------------------------------------------------------ #
#  _normalize_label
# ------------------------------------------------------------------ #


class TestNormalizeLabel:
    def test_strips_whitespace(self):
        assert _normalize_label("  شامخ کل  ") == "شامخ کل"

    def test_collapses_whitespace(self):
        assert _normalize_label("شامخ   کل") == "شامخ کل"

    def test_arabic_yeh_to_persian(self):
        assert _normalize_label("توليد") == "تولید"

    def test_arabic_keh_to_persian(self):
        assert _normalize_label("موجودي") == "موجودی"

    def test_empty(self):
        assert _normalize_label("") == ""

    def test_none(self):
        assert _normalize_label(None) == ""


# ------------------------------------------------------------------ #
#  _label_in_text
# ------------------------------------------------------------------ #


class TestLabelInText:
    def test_direct_match(self):
        assert _label_in_text("شامخ کل", "شاخص شامخ کل اقتصاد") is True

    def test_no_match(self):
        assert _label_in_text("شامخ کل", "اخبار اقتصاد") is False

    def test_normalized_match(self):
        assert _label_in_text("توليد", "میزان تولید محصول") is True

    def test_collapsed_match(self):
        assert _label_in_text("شامخ کل", "شامخکل") is True

    def test_empty_label(self):
        assert _label_in_text("", "text") is False

    def test_empty_text(self):
        assert _label_in_text("label", "") is False


# ------------------------------------------------------------------ #
#  _best_match
# ------------------------------------------------------------------ #


class TestBestMatch:
    def test_exact_match(self):
        assert _best_match("شامخ کل") == "pmi_total"

    def test_exact_match_production(self):
        assert _best_match("میزان تولید") == "production"

    def test_partial_match_in_label(self):
        assert _best_match("شاخص کل اقتصاد ایران") == "pmi_total"

    def test_partial_match_key_in_text(self):
        assert _best_match("قیمت خرید مواد اولیه") == "input_price"

    def test_reversed_persian_label(self):
        assert _best_match("تیلاعف لک خماش") == "pmi_total"

    def test_reversed_production(self):
        assert _best_match("تلاوصحم دیلوت رادقم") == "production"

    def test_no_match(self):
        assert _best_match("خبر جدید") is None

    def test_empty(self):
        assert _best_match("") is None

    def test_full_form_production(self):
        assert _best_match("میزان تولید محصول یا ارائه خدمت") == "production"

    def test_full_form_employment(self):
        assert _best_match("میزان استخدام و بکارگیری نیروی انسانی") == "employment"

    # --- Edge cases ---

    def test_reversed_economic_label(self):
        """Reversed شاخص کل اقتصاد."""
        assert _best_match("داصتقا لک خماش") == "pmi_total"

    def test_arabic_yeh_in_label(self):
        """Arabic Yeh (ي) should be normalized to Persian (ی)."""
        assert _best_match("توليد محصول") == "production"

    def test_arabic_keh_in_label(self):
        """Arabic Keh (ك) should be normalized to Persian (ک)."""
        assert _best_match("موجودي مواد") == "raw_materials_inv"

    def test_whitespace_in_label(self):
        """Extra whitespace should be collapsed."""
        assert _best_match("شامخ   کل") == "pmi_total"

    def test_label_with_numbers_no_match(self):
        """Label with numbers in unexpected position may not match."""
        assert _best_match("شاخص ۱ کل") is None  # numbers disrupt matching

    def test_long_label_partial_match(self):
        """Long label with partial match."""
        assert _best_match("سرعت انجام و تحویل سفارشات") == "delivery_speed"


# ------------------------------------------------------------------ #
#  _detect_month
# ------------------------------------------------------------------ #


class TestDetectMonth:
    parser = PDFParser()

    def test_persian_month_before_year(self):
        text = "گزارش خرداد ۱۴۰۵ دوره ۹۳"
        assert self.parser._detect_month(text) == "1405-03"

    def test_persian_month_after_year(self):
        text = "دوره ۸۸ - دی ۱۴۰۴"
        assert self.parser._detect_month(text) == "1404-10"

    def test_ascii_year(self):
        text = "فروردین 1405"
        assert self.parser._detect_month(text) == "1405-01"

    def test_no_month_found(self):
        text = "گزارش اقتصادی"
        assert self.parser._detect_month(text) is None

    def test_bare_year_only(self):
        text = "some text 1404 other text"
        assert self.parser._detect_month(text) == "1404-??"

    def test_all_months(self):
        months = {
            "فروردین": "01", "اردیبهشت": "02", "خرداد": "03",
            "تیر": "04", "مرداد": "05", "شهریور": "06",
            "مهر": "07", "آبان": "08", "آذر": "09",
            "دی": "10", "بهمن": "11", "اسفند": "12",
        }
        for name, num in months.items():
            result = self.parser._detect_month(f"{name} ۱۴۰۵")
            assert result == f"1405-{num}", f"Failed for {name}"


# ------------------------------------------------------------------ #
#  _parse_tables
# ------------------------------------------------------------------ #


class TestParseTables:
    parser = PDFParser()

    def test_standard_table(self):
        tables = [
            [
                ["میزان تولید", "45.0", "48.0", "50.0"],
                ["سفارشات جدید", "42.0", "44.0", "46.0"],
            ]
        ]
        fields = self.parser._parse_tables(tables)
        assert fields["production"] == 50.0
        assert fields["new_orders"] == 46.0

    def test_rtl_table_label_last(self):
        """Industry breakdown tables have label in the last column."""
        tables = [
            [
                ["41.6", "42.5", "42.5", "تیلاعف لک خماش"],
                ["39.3", "41.3", "41.3", "تلاوصحم دیلوت رادقم"],
            ]
        ]
        fields = self.parser._parse_tables(tables)
        assert fields.get("pmi_total") is not None
        assert fields.get("production") is not None

    def test_skips_short_tables(self):
        tables = [["", ""]]
        fields = self.parser._parse_tables(tables)
        assert fields == {}

    def test_skips_none_rows(self):
        tables = [[[None, None, None], ["میزان تولید", "45.0"]]]
        fields = self.parser._parse_tables(tables)
        assert fields["production"] == 45.0

    def test_cross_tab_prefers_aggregate_row(self):
        """Cross-tab table should extract from aggregate row, not industry rows."""
        tables = [
            [
                # Industry rows first (wrong values) - labels include industry name
                ["41.6", "42.5", "42.5", "شامخ کل - سایر صنایع"],  # pmi_total from "سایر صنایع"
                ["39.3", "41.3", "41.3", "تولید - سایر صنایع"],  # production from "سایر صنایع"
                # Aggregate row last (correct values) - no industry qualifier
                ["45.9", "47.2", "48.2", "شامخ کل"],  # pmi_total aggregate
                ["48.2", "49.1", "50.0", "تولید"],  # production aggregate
            ]
        ]
        fields = self.parser._parse_tables(tables)
        # Should use aggregate values, not industry values
        assert fields.get("pmi_total") == 48.2
        assert fields.get("production") == 50.0

    def test_cross_tab_with_industry_qualifier(self):
        """Rows with industry qualifiers should be skipped in favor of aggregate."""
        tables = [
            [
                ["41.6", "42.5", "42.5", "تولید - صنعت خودرو"],  # automotive industry
                ["39.3", "41.3", "41.3", "تولید - سایر صنایع"],  # other industries
                ["48.2", "49.1", "50.0", "تولید"],  # aggregate (no qualifier)
            ]
        ]
        fields = self.parser._parse_tables(tables)
        assert fields.get("production") == 50.0


# ------------------------------------------------------------------ #
#  _is_aggregate_row
# ------------------------------------------------------------------ #


class TestIsAggregateRow:
    def test_aggregate_with_kol_qualifier(self):
        assert _is_aggregate_row("شاخص کل اقتصاد") is True

    def test_aggregate_with_eghtesad_qualifier(self):
        assert _is_aggregate_row("تولید اقتصاد") is True

    def test_industry_specific_sayer(self):
        assert _is_aggregate_row("تولید - سایر صنایع") is False

    def test_industry_specific_khodro(self):
        assert _is_aggregate_row("تولید - صنعت خودرو") is False

    def test_no_qualifier_treated_as_aggregate(self):
        assert _is_aggregate_row("تولید") is True

    def test_empty_label(self):
        assert _is_aggregate_row("") is True

    def test_none_label(self):
        assert _is_aggregate_row(None) is True

    # --- Edge cases ---

    def test_industry_food(self):
        """Food industry qualifier."""
        assert _is_aggregate_row("تولید - صنعت غذا") is False

    def test_industry_pharma(self):
        """Pharmaceutical industry qualifier."""
        assert _is_aggregate_row("تولید - صنعت دارو") is False

    def test_industry_oil(self):
        """Oil industry qualifier."""
        assert _is_aggregate_row("تولید - صنعت نفت") is False

    def test_aggregate_with_majmoo(self):
        """Aggregate qualifier مجموع (aggregate)."""
        assert _is_aggregate_row("تولید مجموع") is True

    def test_aggregate_with_jame(self):
        """Aggregate qualifier جمع (sum)."""
        assert _is_aggregate_row("تولید جمع") is True

    def test_multiple_industry_keywords(self):
        """Label with multiple industry keywords is still industry-specific."""
        assert _is_aggregate_row("تولید - صنعت فلزات - سایر صنایع") is False

    def test_label_with_kol_in_industry(self):
        """Industry label containing کل should still be industry-specific if industry keyword present."""
        assert _is_aggregate_row("تولید کل - سایر صنایع") is False

    def test_label_with_numbers(self):
        """Label with numbers but no industry keyword."""
        assert _is_aggregate_row("تولید ۱۲۳") is True


# ------------------------------------------------------------------ #
#  _parse_text_fallback
# ------------------------------------------------------------------ #


class TestParseTextFallback:
    parser = PDFParser()

    def test_extracts_from_text(self):
        text = "شاخص کل اقتصاد: 45.9"
        fields = self.parser._parse_text_fallback(text)
        assert fields.get("pmi_total") == 45.9

    def test_multiple_indicators(self):
        text = (
            "میزان تولید: 48.2\n"
            "سفارشات جدید مشتریان: 42.1\n"
            "میزان فروش کالاها یا خدمات: 47.5"
        )
        fields = self.parser._parse_text_fallback(text)
        assert fields.get("production") == 48.2
        assert fields.get("new_orders") == 42.1
        assert fields.get("sales") == 47.5

    def test_no_match(self):
        text = "خبر جدید اقتصادی"
        fields = self.parser._parse_text_fallback(text)
        assert fields == {}


# ------------------------------------------------------------------ #
#  Full parse() with mocked PDF
# ------------------------------------------------------------------ #


class TestParse:
    def test_parse_file_not_found(self):
        parser = PDFParser()
        with pytest.raises(Exception):
            parser.parse(Path("nonexistent.pdf"))

    def test_parse_with_mocked_tables(self, tmp_path):
        """Test full parse flow with mocked pdfplumber output."""
        # Create a minimal PDF-like object
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "گزارش شاخص مدیران خرید خرداد ۱۴۰۵ دوره ۹۳\n"
            "شاخص کل اقتصاد: 45.9\n"
            "میزان تولید: 48.2\n"
            "میزان سفارشات جدید مشتریان: 42.1\n"
        )
        mock_page.extract_tables.return_value = [
            [
                ["شاخص کل اقتصاد", "45.9"],
                ["میزان تولید", "48.2"],
                ["میزان سفارشات جدید مشتریان", "42.1"],
                ["سرعت انجام و تحویل سفارش", "47.5"],
                ["موجودی مواد اولیه یا لوازم خریداری شده", "43.8"],
                ["میزان استخدام و بکارگیری نیروی انسانی", "46.2"],
                ["قیمت مواد اولیه یا لوازم خریداری شده", "72.3"],
                ["موجودی محصول نهایی در انبار یا کارهای در حال تکمیل", "44.1"],
                ["میزان صادرات کالا یا خدمت", "41.7"],
                ["میزان فروش کالاها یا خدمات", "47.5"],
                ["انتظارات در مورد میزان فعالیت اقتصادی در ماه آینده", "50.2"],
            ]
        ]

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        # Write a dummy PDF file so the Path check passes
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy")

        with patch("pdfplumber.open", return_value=mock_pdf):
            parser = PDFParser()
            results = parser.parse(pdf_path, month="1405-03")

        assert len(results) == 1
        m = results[0]
        assert m.month == "1405-03"
        assert m.pmi_total == 45.9
        assert m.production == 48.2
        assert m.new_orders == 42.1
        assert m.delivery_speed == 47.5
        assert m.raw_materials_inv == 43.8
        assert m.employment == 46.2
        assert m.input_price == 72.3
        assert m.final_goods_inv == 44.1
        assert m.exports == 41.7
        assert m.sales == 47.5
        assert m.business_activity == 50.2

    def test_parse_fallback_to_text(self, tmp_path):
        """When tables return nothing, should fall back to text."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "گزارش شاخص مدیران خرید اردیبهشت ۱۴۰۵\n"
            "شاخص کل: 47.3\n"
            "تولید: 49.1\n"
        )
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy")

        with patch("pdfplumber.open", return_value=mock_pdf):
            parser = PDFParser()
            results = parser.parse(pdf_path, month="1405-02")

        assert len(results) == 1
        m = results[0]
        assert m.month == "1405-02"
        assert m.pmi_total == 47.3
