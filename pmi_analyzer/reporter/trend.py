"""Trend analysis report for PMI Analyzer.

Generates multi-month trend analysis with charts and comparisons.
"""

from pathlib import Path
from typing import List, Optional

import pandas as pd

from pmi_analyzer.reporter.base import BaseReport
from pmi_analyzer.types import ShamkhMetrics


class TrendReport(BaseReport):
    """Trend analysis PMI report.

    Generates a multi-month trend report with:
    - Time series charts
    - Rolling averages
    - Percentage changes
    - Trend indicators
    """

    def generate_from_list(
        self, metrics_list: List[ShamkhMetrics], output_path: Optional[Path] = None
    ) -> Path:
        """Generate trend report from list of metrics.

        Args:
            metrics_list: List of PMI metrics for multiple months.
            output_path: Output file path.

        Returns:
            Path to generated report.
        """
        output_path = output_path or self.config.output_dir / "trend_analysis.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = self._metrics_to_df(metrics_list)
        html = self._build_html(df, metrics_list)
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def generate(self, metrics: ShamkhMetrics, output_path: Optional[Path] = None) -> Path:
        """Generate report (single month - uses list version for trends)."""
        return self.generate_from_list([metrics], output_path)

    def _metrics_to_df(self, metrics_list: List[ShamkhMetrics]) -> pd.DataFrame:
        """Convert metrics list to DataFrame.

        Args:
            metrics_list: List of ShamkhMetrics.

        Returns:
            DataFrame with metrics.
        """
        rows = []
        for m in metrics_list:
            rows.append(
                {
                    "month": m.month,
                    "pmi_total": m.pmi_total,
                    "production": m.production,
                    "new_orders": m.new_orders,
                    "sales": m.sales,
                    "employment": m.employment,
                    "exports": m.exports,
                }
            )
        return pd.DataFrame(rows)

    def _build_html(self, df: pd.DataFrame, metrics_list: List[ShamkhMetrics]) -> str:
        """Build HTML content for trend report.

        Args:
            df: Metrics DataFrame.
            metrics_list: Original metrics list.

        Returns:
            Complete HTML string.
        """
        rtl_style = self._get_rtl_style()

        # Calculate trend data
        if "pmi_total" in df.columns and len(df) > 1:
            df["change"] = df["pmi_total"].diff()
            df["change_pct"] = df["pmi_total"].pct_change() * 100

        # Build chart data
        months = df["month"].tolist()
        pmi_values = df["pmi_total"].fillna(0).tolist() if "pmi_total" in df.columns else []

        # Build trend table
        trend_rows = ""
        for _, row in df.iterrows():
            change = row.get("change", 0) or 0
            change_pct = row.get("change_pct", 0) or 0
            arrow = "↑" if change > 0 else ("↓" if change < 0 else "→")
            color = "#2ecc71" if change > 0 else ("#e74c3c" if change < 0 else "#f39c12")

            trend_rows += f"""
            <tr>
                <td>{row['month']}</td>
                <td style="font-weight: bold;">{row.get('pmi_total', 'N/A')}</td>
                <td style="color: {color};">{arrow} {change:+.1f} ({change_pct:+.1f}%)</td>
            </tr>
            """

        # Chart data
        chart_data = f"""
        <script>
        var trace1 = {{
            x: {months},
            y: {pmi_values},
            type: 'scatter',
            mode: 'lines+markers',
            name: '{self._get_text("pmi_total")}',
            line: {{ color: '#3498db', width: 3 }},
            marker: {{ size: 8 }}
        }};

        var layout = {{
            title: '{self._get_text("trend")} {self._get_text("pmi_total")}',
            xaxis: {{ title: '{self._get_text("month")}' }},
            yaxis: {{ title: 'PMI', range: [0, 100] }},
            shapes: [{{
                type: 'line',
                x0: 0, x1: 1, xref: 'paper',
                y0: 50, y1: 50,
                line: {{ color: 'red', dash: 'dash', width: 2 }}
            }}],
            height: 400
        }};

        Plotly.newPlot('chart', [trace1], layout);
        </script>
        """

        html = f"""<!DOCTYPE html>
<html {rtl_style}>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._get_text("trend")} - {self._get_text("pmi_total")}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Tahoma, Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: {('right' if self.config.language == 'fa' else 'left')};
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        #chart {{
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self._get_text("trend")} {self._get_text("pmi_total")}</h1>
            <p>{len(metrics_list)} {self._get_text("month")}</p>
        </div>

        <div id="chart"></div>

        <h3>{self._get_text("trend")}</h3>
        <table>
            <thead>
                <tr>
                    <th>{self._get_text("month")}</th>
                    <th>{self._get_text("pmi_total")}</th>
                    <th>{self._get_text("trend")}</th>
                </tr>
            </thead>
            <tbody>
                {trend_rows}
            </tbody>
        </table>
    </div>

    {chart_data}
</body>
</html>"""

        return html
