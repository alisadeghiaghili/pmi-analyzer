"""Monthly summary report for PMI Analyzer.

Generates a single-month overview with key metrics, gauge charts,
and interpretation.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from pmi_analyzer.reporter.base import BaseReport, ReportConfig
from pmi_analyzer.types import ShamkhMetrics


class MonthlyReport(BaseReport):
    """Monthly PMI summary report.

    Generates a comprehensive single-month report with:
    - Key metrics overview
    - Status indicators (expansion/contraction)
    - Sub-indicator breakdown
    - Text analysis
    """

    def generate(self, metrics: ShamkhMetrics, output_path: Optional[Path] = None) -> Path:
        """Generate monthly report.

        Args:
            metrics: PMI metrics for the month.
            output_path: Output file path.

        Returns:
            Path to generated report.
        """
        output_path = output_path or self.config.output_dir / f"monthly_{metrics.month}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._build_html(metrics)
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _build_html(self, metrics: ShamkhMetrics) -> str:
        """Build HTML content for the report.

        Args:
            metrics: PMI metrics data.

        Returns:
            Complete HTML string.
        """
        rtl_style = self._get_rtl_style()
        pmi_value = metrics.pmi_total or 0
        status = self._get_status(pmi_value)
        status_color = self._get_status_color(pmi_value)

        # Build sub-indicator rows
        indicators = [
            ("production", metrics.production),
            ("new_orders", metrics.new_orders),
            ("sales", metrics.sales),
            ("raw_materials_inv", metrics.raw_materials_inv),
            ("final_goods_inv", metrics.final_goods_inv),
            ("input_price", metrics.input_price),
            ("production_expectations", metrics.production_expectations),
            ("employment", metrics.employment),
            ("exports", metrics.exports),
            ("delivery_speed", metrics.delivery_speed),
            ("business_activity", metrics.business_activity),
        ]

        indicator_rows = ""
        for name, value in indicators:
            if value is not None:
                color = self._get_status_color(value)
                status = self._get_status(value)
                indicator_rows += f"""
                <tr>
                    <td>{self._get_indicator_name(name)}</td>
                    <td style="color: {color}; font-weight: bold;">{value:.1f}</td>
                    <td style="color: {color};">{status}</td>
                </tr>
                """

        # Build gauge chart
        gauge_color = status_color
        gauge_data = f"""
        <script>
        var gaugeData = {{
            type: 'indicator',
            mode: 'gauge+number',
            value: {pmi_value},
            title: {{ text: '{self._get_text("pmi_total")}' }},
            gauge: {{
                axis: {{ range: [0, 100] }},
                bar: {{ color: '{gauge_color}' }},
                steps: [
                    {{ range: [0, 50], color: '#fde0dd' }},
                    {{ range: [50, 100], color: '#e5f5e0' }}
                ],
                threshold: {{
                    line: {{ color: 'red', width: 4 }},
                    thickness: 0.75,
                    value: 50
                }}
            }}
        }};
        Plotly.newPlot('gauge', [gaugeData], {{
            height: 300,
            margin: {{ t: 25, b: 25, l: 25, r: 25 }}
        }});
        </script>
        """

        html = f"""<!DOCTYPE html>
<html {rtl_style}>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._get_text("title")} - {metrics.month}</title>
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
        .status-box {{
            background: {status_color};
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }}
        .status-box h2 {{
            margin: 0;
            font-size: 2em;
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
        .gauge-container {{
            display: flex;
            justify-content: center;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self._get_text("title")}</h1>
            <h2>{self._get_text("month")}: {metrics.month}</h2>
        </div>

        <div class="status-box">
            <h2>{status.upper()}</h2>
            <p>{self._get_text("pmi_total")}: {pmi_value:.1f}</p>
        </div>

        <div class="gauge-container">
            <div id="gauge"></div>
        </div>

        <h3>{self._get_text("summary")}</h3>
        <table>
            <thead>
                <tr>
                    <th>{self._get_text("value")}</th>
                    <th>{self._get_text("status")}</th>
                    <th>{self._get_text("value")}</th>
                </tr>
            </thead>
            <tbody>
                {indicator_rows}
            </tbody>
        </table>

        <h3>{self._get_text("analysis")}</h3>
        <p>{self._generate_analysis(metrics)}</p>
    </div>

    {gauge_data}
</body>
</html>"""

        return html

    def _generate_analysis(self, metrics: ShamkhMetrics) -> str:
        """Generate text analysis for the month.

        Args:
            metrics: PMI metrics data.

        Returns:
            Analysis text.
        """
        pmi = metrics.pmi_total
        if pmi is None:
            return "No data available for analysis."

        if self.config.language == "fa":
            if pmi > 55:
                return f"شاخص مدیران خرید در ماه {metrics.month} با مقدار {pmi:.1f} نشان‌دهنده رشد قوی اقتصادی است. تمام شاخص‌های اصلی بالای 50 قرار دارند."
            elif pmi > 50:
                return f"شاخص مدیران خرید در ماه {metrics.month} با مقدار {pmi:.1f} نشان‌دهنده رشد ملایم اقتصادی است."
            elif pmi > 45:
                return f"شاخص مدیران خرید در ماه {metrics.month} با مقدار {pmi:.1f} نشان‌دهنده رکود خفیف است."
            else:
                return f"شاخص مدیران خرید در ماه {metrics.month} با مقدار {pmi:.1f} نشان‌دهنده رکود شدید است. توجه فوری لازم است."
        else:
            if pmi > 55:
                return f"The PMI in {metrics.month} at {pmi:.1f} indicates strong economic expansion."
            elif pmi > 50:
                return f"The PMI in {metrics.month} at {pmi:.1f} indicates moderate expansion."
            elif pmi > 45:
                return f"The PMI in {metrics.month} at {pmi:.1f} indicates mild contraction."
            else:
                return f"The PMI in {metrics.month} at {pmi:.1f} indicates severe contraction. Immediate attention required."
