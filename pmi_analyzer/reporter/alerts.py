"""Recession/expansion alert report for PMI Analyzer.

Generates alerts based on PMI thresholds and consecutive months.
"""

from pathlib import Path
from typing import List, Optional

import pandas as pd

from pmi_analyzer.reporter.base import BaseReport
from pmi_analyzer.types import ShamkhMetrics


class AlertReport(BaseReport):
    """Recession/expansion alert report.

    Monitors PMI values and generates alerts when:
    - PMI crosses 50 threshold
    - Consecutive months above/below 50
    - Severity increases
    """

    def generate_from_list(
        self, metrics_list: List[ShamkhMetrics], output_path: Optional[Path] = None
    ) -> Path:
        """Generate alert report from list of metrics.

        Args:
            metrics_list: List of PMI metrics for multiple months.
            output_path: Output file path.

        Returns:
            Path to generated report.
        """
        output_path = output_path or self.config.output_dir / "alerts.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = self._metrics_to_df(metrics_list)
        alerts = self._analyze_alerts(df)
        html = self._build_html(df, alerts)
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def generate(self, metrics: ShamkhMetrics, output_path: Optional[Path] = None) -> Path:
        """Generate report (single month)."""
        return self.generate_from_list([metrics], output_path)

    def _metrics_to_df(self, metrics_list: List[ShamkhMetrics]) -> pd.DataFrame:
        """Convert metrics list to DataFrame."""
        rows = []
        for m in metrics_list:
            rows.append(
                {
                    "month": m.month,
                    "pmi_total": m.pmi_total,
                }
            )
        return pd.DataFrame(rows)

    def _analyze_alerts(self, df: pd.DataFrame) -> List[dict]:
        """Analyze PMI data for alerts.

        Args:
            df: Metrics DataFrame.

        Returns:
            List of alert dictionaries.
        """
        alerts = []

        if "pmi_total" not in df.columns or len(df) < 1:
            return alerts

        # Check for consecutive months below 50 (recession)
        consecutive_below = 0
        for _, row in df.iterrows():
            if row["pmi_total"] and row["pmi_total"] < 50:
                consecutive_below += 1
            else:
                consecutive_below = 0

            if consecutive_below >= 3:
                alerts.append(
                    {
                        "type": "recession",
                        "severity": "high",
                        "month": row["month"],
                        "value": row["pmi_total"],
                        "message": self._get_alert_message("recession", consecutive_below),
                    }
                )

        # Check for consecutive months above 50 (expansion)
        consecutive_above = 0
        for _, row in df.iterrows():
            if row["pmi_total"] and row["pmi_total"] > 50:
                consecutive_above += 1
            else:
                consecutive_above = 0

            if consecutive_above >= 3:
                alerts.append(
                    {
                        "type": "expansion",
                        "severity": "positive",
                        "month": row["month"],
                        "value": row["pmi_total"],
                        "message": self._get_alert_message("expansion", consecutive_above),
                    }
                )

        # Check for sharp decline
        if len(df) > 1 and "pmi_total" in df.columns:
            for i in range(1, len(df)):
                prev = df.iloc[i - 1]["pmi_total"]
                curr = df.iloc[i]["pmi_total"]
                if prev and curr and (prev - curr) > 5:
                    alerts.append(
                        {
                            "type": "sharp_decline",
                            "severity": "high",
                            "month": df.iloc[i]["month"],
                            "value": curr,
                            "message": self._get_alert_message("sharp_decline", prev - curr),
                        }
                    )

        return alerts

    def _get_alert_message(self, alert_type: str, value: float) -> str:
        """Get translated alert message.

        Args:
            alert_type: Type of alert.
            value: Related value.

        Returns:
            Translated alert message.
        """
        if self.config.language == "fa":
            messages = {
                "recession": f"هشدار: {value:.0f} ماه متوالی زیر 50 - رکود اقتصادی",
                "expansion": f"اطلاع‌رسانی: {value:.0f} ماه متوالی بالای 50 - رشد اقتصادی",
                "sharp_decline": f"هشدار: کاهش شدید {value:.1f} واحد در یک ماه",
            }
        else:
            messages = {
                "recession": f"ALERT: {value:.0f} consecutive months below 50 - Economic recession",
                "expansion": f"INFO: {value:.0f} consecutive months above 50 - Economic expansion",
                "sharp_decline": f"ALERT: Sharp decline of {value:.1f} points in one month",
            }
        return messages.get(alert_type, "")

    def _build_html(self, df: pd.DataFrame, alerts: List[dict]) -> str:
        """Build HTML content for alert report."""
        rtl_style = self._get_rtl_style()

        # Build alerts list
        alerts_html = ""
        for alert in alerts:
            color = "#e74c3c" if alert["severity"] == "high" else "#2ecc71"
            alerts_html += f"""
            <div style="background: {color}; color: white; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <strong>{alert['month']}</strong>: {alert['message']}
            </div>
            """

        if not alerts_html:
            alerts_html = (
                f"<p>{'هشداری وجود ندارد' if self.config.language == 'fa' else 'No alerts'}</p>"
            )

        # Chart data
        months = df["month"].tolist() if "month" in df.columns else []
        pmi_values = df["pmi_total"].fillna(0).tolist() if "pmi_total" in df.columns else []

        chart_data = f"""
        <script>
        var trace1 = {{
            x: {months},
            y: {pmi_values},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'PMI',
            line: {{ color: '#3498db', width: 3 }},
            marker: {{ size: 8 }}
        }};

        var layout = {{
            title: '{self._get_text("alert")} {self._get_text("pmi_total")}',
            xaxis: {{ title: '{self._get_text("month")}' }},
            yaxis: {{ title: 'PMI', range: [0, 100] }},
            shapes: [{{
                type: 'line',
                x0: 0, x1: 1, xref: 'paper',
                y0: 50, y1: 50,
                line: {{ color: 'red', dash: 'dash', width: 2 }}
            }}],
            height: 300
        }};

        Plotly.newPlot('chart', [trace1], layout);
        </script>
        """

        html = f"""<!DOCTYPE html>
<html {rtl_style}>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._get_text("alert")}</title>
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
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self._get_text("alert")}</h1>
        </div>

        <div id="chart"></div>

        <h3>{self._get_text("recession_alert")}</h3>
        {alerts_html}
    </div>

    {chart_data}
</body>
</html>"""

        return html
