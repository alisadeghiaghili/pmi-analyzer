"""Tests for Jalali month identity normalisation and pipeline wiring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pmi_analyzer.calendar import (
    is_canonical_month,
    month_sort_key,
    normalize_month_id,
)
from pmi_analyzer.data.loader import append_record, load_historical, rewrite_historical
from pmi_analyzer.scraper.batch_parser import BatchParser
from pmi_analyzer.scraper.archive_scraper import ReportLink
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.updater.monthly_updater import MonthlyUpdater


class TestNormalizeMonthId:
    def test_canonical_passthrough(self):
        assert normalize_month_id("1404-10") == "1404-10"

    def test_persian_label_with_year(self):
        assert normalize_month_id("دی ۱۴۰۴") == "1404-10"
        assert normalize_month_id("خرداد 1405") == "1405-03"

    def test_rejects_rtl_gibberish_substring(self):
        assert normalize_month_id("ندیدج") is None
        assert normalize_month_id("دیدج تاشرافس", default_year=1405) is None

    def test_bare_month_uses_default_year(self):
        assert normalize_month_id("دی", default_year=1404) == "1404-10"

    def test_year_only(self):
        assert normalize_month_id("گزارش 1405") == "1405-??"

    def test_none_and_empty(self):
        assert normalize_month_id(None) is None
        assert normalize_month_id("  ") is None

    def test_reversed_month_name_from_rtl_dump(self):
        # RTL dump of خرداد is دادرخ / دادرخ.
        assert normalize_month_id("دادرخ 1405") == "1405-03"

    def test_short_jalali_year_in_filename(self):
        assert normalize_month_id("تیر405") == "1405-04"
        assert normalize_month_id("شامخ-اردیبهشت-1405") == "1405-02"

    def test_is_canonical(self):
        assert is_canonical_month("1404-10") is True
        assert is_canonical_month("1404-13") is False
        assert is_canonical_month("دی") is False

    def test_sort_key(self):
        assert month_sort_key("1404-09") < month_sort_key("1404-10")
        assert month_sort_key("1404-12") < month_sort_key("1405-01")


class TestBatchParserMonthIdentity:
    def test_period_label_is_normalised_not_used_raw(self, tmp_path: Path):
        pdf = tmp_path / "dummy.pdf"
        pdf.write_bytes(b"%PDF-1.4 dummy")
        link = ReportLink(
            title="t",
            page_url="https://example.com",
            pdf_url="https://example.com/x.pdf",
            period_label="دی ۱۴۰۴",
            period_number=88,
        )
        parser = BatchParser()
        parser.pdf_parser = MagicMock()
        parser.pdf_parser.parse.return_value = [ShamkhMetrics(month="1404-10", pmi_total=46.0)]

        results = parser.parse_all([(link, pdf)])

        parser.pdf_parser.parse.assert_called_once()
        assert parser.pdf_parser.parse.call_args.kwargs["month"] == "1404-10"
        assert results[0].month == "1404-10"

    def test_invalid_label_falls_back_to_auto_detect(self, tmp_path: Path):
        pdf = tmp_path / "dummy.pdf"
        pdf.write_bytes(b"%PDF-1.4 dummy")
        link = ReportLink(
            title="t",
            page_url="https://example.com",
            pdf_url="https://example.com/x.pdf",
            period_label="ندیدج",
            period_number=None,
        )
        parser = BatchParser()
        parser.pdf_parser = MagicMock()
        parser.pdf_parser.parse.return_value = [ShamkhMetrics(month="1405-03", pmi_total=45.0)]

        parser.parse_all([(link, pdf)])

        assert parser.pdf_parser.parse.call_args.kwargs["month"] is None


class TestMonthlyUpdaterMonthMatch:
    def test_exact_canonical_match(self, tmp_path: Path):
        csv_path = tmp_path / "hist.csv"
        csv_path.write_text(
            "month,production\n1404-10,47.0\n",
            encoding="utf-8-sig",
        )
        updater = MonthlyUpdater(csv_path=csv_path)
        assert updater._month_exists("1404-10", {"1404-10"}) is True
        assert updater._month_exists("1404-11", {"1404-10"}) is False

    def test_persian_label_matches_canonical(self):
        updater = MonthlyUpdater(csv_path=Path("unused.csv"))
        assert updater._month_exists("دی ۱۴۰۴", {"1404-10"}) is True
        assert updater._month_exists("بهمن ۱۴۰۴", {"1404-10"}) is False


class TestLoaderCanonicalMonths:
    def test_rewrite_drops_non_canonical_months(self, tmp_path: Path):
        src = tmp_path / "hist.csv"
        src.write_text(
            "month,production,new_orders,sales,raw_materials_inv,final_goods_inv,"
            "input_price,production_expectations,employment,exports,delivery_speed,"
            "business_activity,pmi_total\n"
            "1404-06,43,43,52,43,48,78,38,47,44,49,45,45.5\n"
            "دی,47,47,47,47,47,47,47,47,47,47,47,8.28\n"
            "1404-07,,,,,,, ,,,,47.4,47.4\n",
            encoding="utf-8-sig",
        )
        kept, dropped = rewrite_historical(src)
        assert kept == 2
        assert dropped == 1
        months = [m.month for m in load_historical(src)]
        assert months == ["1404-06", "1404-07"]
        assert "دی" not in months

    def test_append_rejects_non_canonical_month(self, tmp_path: Path):
        path = tmp_path / "hist.csv"
        with pytest.raises(ValueError):
            append_record(ShamkhMetrics(month="دی", pmi_total=40.0), path)
