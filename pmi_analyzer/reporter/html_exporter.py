"""HTML exporter for PMI reports.

Standalone exporter that wraps any BaseReport subclass and writes
an interactive HTML file. Supports Persian RTL and dark/light mode.
"""

from pathlib import Path
from typing import Optional

from pmi_analyzer.reporter.alerts import AlertReport
from pmi_analyzer.reporter.base import ReportConfig
from pmi_analyzer.reporter.monthly import MonthlyReport
from pmi_analyzer.reporter.trend import TrendReport
from pmi_analyzer.types import ShamkhMetrics


class HtmlExporter:
    """Export PMI reports as interactive HTML files.

    Wraps existing report classes and ensures HTML output with
    optional dark-mode toggle and responsive layout.

    Example::

        from pmi_analyzer.reporter.html_exporter import HtmlExporter
        from pmi_analyzer.reporter.base import ReportConfig

        exporter = HtmlExporter(ReportConfig(language="fa"))
        path = exporter.export_monthly(metrics, Path("output/report.html"))
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialise the exporter.

        Args:
            config: Shared ReportConfig for all exports. Defaults to Persian HTML.
        """
        self.config = config or ReportConfig(language="fa", export_format="html")
        # force html
        self.config.export_format = "html"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_monthly(
        self,
        metrics: ShamkhMetrics,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Export a monthly summary report as HTML.

        Args:
            metrics: PMI metrics for the target month.
            output_path: Destination file (default: output/reports/monthly_<month>.html).

        Returns:
            Path to the written HTML file.
        """
        report = MonthlyReport(self.config)
        path = report.generate(metrics, output_path)
        return self._inject_dark_mode_toggle(path)

    def export_trend(
        self,
        metrics_list: list,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Export a trend analysis report as HTML.

        Args:
            metrics_list: List of ShamkhMetrics sorted chronologically.
            output_path: Destination file.

        Returns:
            Path to the written HTML file.
        """
        report = TrendReport(self.config)
        path = report.generate_trend(metrics_list, output_path)
        return self._inject_dark_mode_toggle(path)

    def export_alerts(
        self,
        metrics_list: list,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Export an alerts report as HTML.

        Args:
            metrics_list: List of ShamkhMetrics sorted chronologically.
            output_path: Destination file.

        Returns:
            Path to the written HTML file.
        """
        report = AlertReport(self.config)
        path = report.generate(
            metrics_list[-1] if metrics_list else ShamkhMetrics(month="unknown"), output_path
        )
        return self._inject_dark_mode_toggle(path)

    # ------------------------------------------------------------------
    # Dark-mode toggle injection
    # ------------------------------------------------------------------

    def _inject_dark_mode_toggle(self, html_path: Path) -> Path:
        """Inject a dark/light mode toggle button into an existing HTML file.

        Args:
            html_path: Path to an existing HTML file to modify in-place.

        Returns:
            The same path after modification.
        """
        content = html_path.read_text(encoding="utf-8")

        toggle_css = """
<style id="dark-mode-style"></style>
<style>
  #dark-toggle {
    position: fixed; top: 14px; left: 14px; z-index: 9999;
    background: #3498db; color: white; border: none;
    padding: 8px 14px; border-radius: 6px; cursor: pointer;
    font-size: 0.85em;
  }
  body.dark-mode {
    background: #1a1a2e !important;
    color: #e0e0e0 !important;
  }
  body.dark-mode .container {
    background: #16213e !important;
    color: #e0e0e0 !important;
  }
  body.dark-mode th { background: #0f3460 !important; }
  body.dark-mode tr:nth-child(even) { background: #1e2a45 !important; }
</style>"""

        toggle_html = """
<button id="dark-toggle" onclick="toggleDark()">🌙 Dark</button>
<script>
function toggleDark() {
  document.body.classList.toggle('dark-mode');
  const btn = document.getElementById('dark-toggle');
  btn.textContent = document.body.classList.contains('dark-mode') ? '☀️ Light' : '🌙 Dark';
}
</script>"""

        # inject CSS before </head> and button after <body>
        content = content.replace("</head>", toggle_css + "\n</head>", 1)
        content = content.replace("<body>", "<body>\n" + toggle_html, 1)
        if "<body " in content and toggle_html not in content:
            idx = content.find("<body ")
            end = content.find(">", idx)
            content = content[: end + 1] + "\n" + toggle_html + content[end + 1 :]

        html_path.write_text(content, encoding="utf-8")
        return html_path
