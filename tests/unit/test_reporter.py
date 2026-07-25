"""Tests for reporter module."""

import pytest
from pathlib import Path

from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.reporter import ReportConfig, MonthlyReport, TrendReport, AlertReport


# ------------------------------------------------------------------ #
#  ReportConfig
# ------------------------------------------------------------------ #


class TestReportConfig:
    def test_default_config(self):
        config = ReportConfig()
        assert config.language == "fa"
        assert config.export_format == "html"

    def test_custom_config(self):
        config = ReportConfig(language="en", export_format="pdf")
        assert config.language == "en"
        assert config.export_format == "pdf"


# ------------------------------------------------------------------ #
#  MonthlyReport
# ------------------------------------------------------------------ #


class TestMonthlyReport:
    def test_generates_html(self, tmp_path):
        config = ReportConfig(output_dir=tmp_path)
        report = MonthlyReport(config)
        metrics = ShamkhMetrics(
            month="1405-03",
            pmi_total=45.9,
            production=48.2,
            new_orders=42.1,
        )
        path = report.generate(metrics)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "1405-03" in content
        assert "45.9" in content

    def test_persian_rtl(self, tmp_path):
        config = ReportConfig(language="fa", output_dir=tmp_path)
        report = MonthlyReport(config)
        metrics = ShamkhMetrics(month="1405-03", pmi_total=45.9)
        path = report.generate(metrics)
        content = path.read_text(encoding="utf-8")
        assert 'dir="rtl"' in content

    def test_english_ltr(self, tmp_path):
        config = ReportConfig(language="en", output_dir=tmp_path)
        report = MonthlyReport(config)
        metrics = ShamkhMetrics(month="1405-03", pmi_total=45.9)
        path = report.generate(metrics)
        content = path.read_text(encoding="utf-8")
        assert 'dir="ltr"' in content


# ------------------------------------------------------------------ #
#  TrendReport
# ------------------------------------------------------------------ #


class TestTrendReport:
    def test_generates_html(self, tmp_path):
        config = ReportConfig(output_dir=tmp_path)
        report = TrendReport(config)
        metrics_list = [
            ShamkhMetrics(month="1405-01", pmi_total=47.0),
            ShamkhMetrics(month="1405-02", pmi_total=46.5),
            ShamkhMetrics(month="1405-03", pmi_total=45.9),
        ]
        path = report.generate_from_list(metrics_list)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "1405-01" in content
        assert "1405-03" in content

    def test_includes_chart(self, tmp_path):
        config = ReportConfig(output_dir=tmp_path)
        report = TrendReport(config)
        metrics_list = [
            ShamkhMetrics(month="1405-01", pmi_total=47.0),
            ShamkhMetrics(month="1405-02", pmi_total=46.5),
        ]
        path = report.generate_from_list(metrics_list)
        content = path.read_text(encoding="utf-8")
        assert "Plotly.newPlot" in content


# ------------------------------------------------------------------ #
#  AlertReport
# ------------------------------------------------------------------ #


class TestAlertReport:
    def test_generates_html(self, tmp_path):
        config = ReportConfig(output_dir=tmp_path)
        report = AlertReport(config)
        metrics_list = [
            ShamkhMetrics(month="1405-01", pmi_total=47.0),
            ShamkhMetrics(month="1405-02", pmi_total=46.5),
            ShamkhMetrics(month="1405-03", pmi_total=45.9),
        ]
        path = report.generate_from_list(metrics_list)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "1405-01" in content

    def test_detects_recession(self, tmp_path):
        config = ReportConfig(language="en", output_dir=tmp_path)
        report = AlertReport(config)
        # 4 months below 50 = recession alert
        metrics_list = [
            ShamkhMetrics(month="1405-01", pmi_total=49.0),
            ShamkhMetrics(month="1405-02", pmi_total=48.0),
            ShamkhMetrics(month="1405-03", pmi_total=47.0),
            ShamkhMetrics(month="1405-04", pmi_total=46.0),
        ]
        path = report.generate_from_list(metrics_list)
        content = path.read_text(encoding="utf-8")
        assert "recession" in content.lower() or "Recession" in content
