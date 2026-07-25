"""Reporting module for PMI Analyzer.

This module provides classes for generating insightful PMI reports
with multiple export formats and Persian RTL support.

Typical usage::

    from pmi_analyzer.reporter import ReportConfig, MonthlyReport
    from pmi_analyzer.parser.pdf_parser import PDFParser

    parser = PDFParser()
    results = parser.parse(Path("data/pdfs/report.pdf"))

    config = ReportConfig(language="fa", export_format="html")
    report = MonthlyReport(config)
    report.generate(results[0], Path("output/report.html"))
"""

from pmi_analyzer.reporter.alerts import AlertReport
from pmi_analyzer.reporter.base import BaseReport, ReportConfig
from pmi_analyzer.reporter.monthly import MonthlyReport
from pmi_analyzer.reporter.trend import TrendReport

__all__ = [
    "AlertReport",
    "BaseReport",
    "MonthlyReport",
    "ReportConfig",
    "TrendReport",
]
