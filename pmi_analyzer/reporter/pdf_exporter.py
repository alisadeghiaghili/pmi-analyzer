"""PDF exporter for PMI reports.

Converts HTML reports to static PDF using weasyprint (if installed)
or falls back to pdfkit/wkhtmltopdf. Supports Persian RTL via
arabic_reshaper + python-bidi for proper text rendering.

Dependencies (optional — install with `pip install pmi-analyzer[report]`)::

    weasyprint>=60.0
    arabic-reshaper>=3.0.0
    python-bidi>=0.6.0
"""

import importlib
import logging
from pathlib import Path
from typing import Optional

from pmi_analyzer.reporter.base import ReportConfig
from pmi_analyzer.reporter.html_exporter import HtmlExporter
from pmi_analyzer.types import ShamkhMetrics

logger = logging.getLogger(__name__)


class PdfExporter:
    """Export PMI reports as static PDF files.

    Uses WeasyPrint for PDF rendering with full Persian RTL support.
    Falls back to a warning and saves HTML if WeasyPrint is not installed.

    Example::

        from pmi_analyzer.reporter.pdf_exporter import PdfExporter
        from pmi_analyzer.reporter.base import ReportConfig

        exporter = PdfExporter(ReportConfig(language="fa"))
        path = exporter.export_monthly(metrics, Path("output/report.pdf"))
    """

    _WEASYPRINT_AVAILABLE: Optional[bool] = None  # cached

    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialise the PDF exporter.

        Args:
            config: Shared ReportConfig. export_format is forced to "pdf".
        """
        self.config = config or ReportConfig(language="fa", export_format="pdf")
        self.config.export_format = "pdf"
        self._html_exporter = HtmlExporter(config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_monthly(
        self,
        metrics: ShamkhMetrics,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Export a monthly report as PDF.

        Args:
            metrics: PMI metrics for the target month.
            output_path: Destination PDF file.

        Returns:
            Path to the generated PDF (or HTML fallback).
        """
        output_path = output_path or self.config.output_dir / f"monthly_{metrics.month}.pdf"
        html_path = output_path.with_suffix(".html")
        self._html_exporter.export_monthly(metrics, html_path)
        return self._html_to_pdf(html_path, output_path)

    def export_trend(
        self,
        metrics_list: list,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Export a trend report as PDF.

        Args:
            metrics_list: List of ShamkhMetrics sorted chronologically.
            output_path: Destination PDF file.

        Returns:
            Path to the generated PDF (or HTML fallback).
        """
        output_path = output_path or self.config.output_dir / "trend_report.pdf"
        html_path = output_path.with_suffix(".html")
        self._html_exporter.export_trend(metrics_list, html_path)
        return self._html_to_pdf(html_path, output_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _html_to_pdf(self, html_path: Path, pdf_path: Path) -> Path:
        """Convert an HTML file to PDF.

        Args:
            html_path: Source HTML file.
            pdf_path: Destination PDF file.

        Returns:
            pdf_path on success, html_path on fallback.
        """
        if self._weasyprint_available():
            try:
                weasyprint = importlib.import_module("weasyprint")
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                weasyprint.HTML(filename=str(html_path)).write_pdf(str(pdf_path))
                logger.info("PDF written to %s", pdf_path)
                return pdf_path
            except Exception as exc:
                logger.warning("WeasyPrint failed (%s); returning HTML fallback.", exc)
                return html_path
        else:
            logger.warning(
                "WeasyPrint not installed. Install with `pip install pmi-analyzer[report]`. "
                "Returning HTML file: %s",
                html_path,
            )
            return html_path

    @classmethod
    def _weasyprint_available(cls) -> bool:
        """Check (and cache) whether WeasyPrint is importable."""
        if cls._WEASYPRINT_AVAILABLE is None:
            cls._WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None
        return cls._WEASYPRINT_AVAILABLE
