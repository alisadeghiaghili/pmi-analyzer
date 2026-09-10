"""Regression tests for PDF extraction accuracy against real ICCIMA shapes.

These tests encode failure modes observed on live Shamkh PDFs:
false month detection, garbage multi-line cells, magic column picking,
industry-vs-national aggregate confusion, and dataclass validation gaps.
"""

from __future__ import annotations

import pytest

from pmi_analyzer.data.loader import _row_to_metrics
from pmi_analyzer.metrics.calculator import MetricsCalculator
from pmi_analyzer.parser.pdf_parser import (
    PDFParser,
    _best_match,
    _is_aggregate_row,
    _to_float,
)
from pmi_analyzer.types import ShamkhMetrics
from tests.fixtures.golden_tables import (
    CLEAN_SUMMARY_TABLE,
    FARVARDIN_INDUSTRY_TABLE,
    KHORDAD_SUMMARY_TABLE,
)

# --------------------------------------------------------------------------- #
#  _to_float
# --------------------------------------------------------------------------- #


class TestToFloatRealPdfCells:
    def test_arabic_decimal_separator(self):
        assert _to_float("۴۷٫۶۳") == pytest.approx(47.63)

    def test_arabic_decimal_separator_short(self):
        assert _to_float("۸٫۲۸") == pytest.approx(8.28)

    def test_doubled_digit_corruption_returns_none_or_clean(self):
        """'4478..02' is a doubled-layer artifact; must not become 2.0."""
        val = _to_float("4478..02")
        assert val is None or 20.0 <= val <= 100.0

    def test_doubled_digit_twin(self):
        val = _to_float("951.49.2")
        assert val is None or 20.0 <= val <= 100.0

    def test_triple_line_prefers_first_clean_pmi(self):
        # Real cell: current, then history. First clean decimal is current.
        assert _to_float("38.5\n39.8\n39.8") == pytest.approx(38.5)

    def test_persian_year_with_value(self):
        assert _to_float("45.9\n١٤٠٥ دادرخ") == pytest.approx(45.9)

    def test_percent_column_value(self):
        assert _to_float("12%") == pytest.approx(12.0)


# --------------------------------------------------------------------------- #
#  month detection
# --------------------------------------------------------------------------- #


class TestDetectMonthOnRealText:
    parser = PDFParser()

    def test_rejects_dey_inside_rtl_gibberish(self):
        # 'دی' as substring of garbled 'می‌دهد' near year must not win.
        text = "اکت زا سپ ناریا داصتقا دهدی م ناشن 1405 هامدادرخ دیر"
        month = self.parser._detect_month(text)
        assert month != "1405-10"
        assert month is None or month.startswith("1405-03") or month == "1405-??"

    def test_prefers_title_month_near_report_year(self):
        text = "گزارش شاخص مدیران خرید خرداد ۱۴۰۵ دوره ۹۳"
        assert self.parser._detect_month(text) == "1405-03"

    def test_does_not_pick_comparison_year_month_over_title(self):
        # Comparison mentions خرداد 1400; title is فروردین 1405.
        text = "فروردین 1405 نسبت به خرداد 1400 مورد بررسی قرار گرفت"
        assert self.parser._detect_month(text) == "1405-01"

    def test_dey_requires_word_boundary(self):
        month = self.parser._detect_month("ندیدج 1405")
        assert month != "1405-10"
        assert month in (None, "1405-??")
        assert self.parser._detect_month("دی 1405") == "1405-10"


# --------------------------------------------------------------------------- #
#  table extraction
# --------------------------------------------------------------------------- #


class TestExtractFromRealTableShapes:
    parser = PDFParser()

    def test_clean_summary_takes_current_when_three_periods(self):
        fields = self.parser._parse_tables([CLEAN_SUMMARY_TABLE])
        assert fields["production"] == pytest.approx(50.0)
        assert fields["new_orders"] == pytest.approx(46.0)
        assert fields["pmi_total"] == pytest.approx(45.9)

    def test_current_column_is_determined_by_header_not_count(self):
        """Four period columns: header says current is first."""
        table = [
            ["شاخص", "جاری", "قبل", "قبل‌تر", "پارسال"],
            ["میزان تولید", "48.2", "45.0", "44.0", "40.0"],
        ]
        fields = self.parser._parse_tables([table])
        assert fields["production"] == pytest.approx(48.2)

    def test_industry_table_does_not_export_last_industry_as_pmi(self):
        fields = self.parser._parse_tables([FARVARDIN_INDUSTRY_TABLE])
        # Sector breakdown must not populate national headline metrics.
        assert fields.get("pmi_total") is None

    def test_unknown_industry_is_not_aggregate(self):
        assert _is_aggregate_row("میزان تولید - پتروشیمی") is False
        assert _is_aggregate_row("میزان تولید - هوافضا") is False

    def test_percent_trailing_column_does_not_override_value(self):
        table = [
            ["میزان تولید", "48.2", "12%"],
            ["سفارشات جدید", "42.1", "5%"],
        ]
        fields = self.parser._parse_tables([table])
        assert fields["production"] == pytest.approx(48.2)
        assert fields["new_orders"] == pytest.approx(42.1)

    def test_khordad_summary_extracts_headline_from_garbled_cell(self):
        fields = self.parser._parse_tables([KHORDAD_SUMMARY_TABLE])
        # Headline row label is reversed شاخص کل اقتصاد.
        assert fields.get("pmi_total") == pytest.approx(45.9)


# --------------------------------------------------------------------------- #
#  dataclass + loader + calculator
# --------------------------------------------------------------------------- #


class TestValidateAndPipeline:
    def test_validate_accepts_only_input_price(self):
        m = ShamkhMetrics(month="1402-01", input_price=75.0)
        assert m.validate() is True

    def test_loader_tolerates_none_cells(self):
        m = _row_to_metrics({"month": "1402-01", "production": None, "pmi_total": "45.9"})
        assert m.production is None
        assert m.pmi_total == pytest.approx(45.9)

    def test_calculator_preserves_pmi_total(self):
        m = ShamkhMetrics(
            month="1402-01",
            pmi_total=48.5,
            production=50.0,
            new_orders=45.0,
            sales=47.0,
        )
        df = MetricsCalculator().calculate([m])
        assert "pmi_total" in df.columns
        assert df["pmi_total"].iloc[0] == pytest.approx(48.5)


class TestBestMatchGuards:
    def test_price_of_output_is_not_sales(self):
        assert _best_match("قیمت محصول") != "sales"

    def test_short_label_alone_not_overmatched(self):
        # Bare 'شاخص' may map to pmi_total, but must not match random text.
        assert _best_match("خبر جدید") is None
