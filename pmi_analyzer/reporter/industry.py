"""Industry breakdown report for PMI Analyzer.

Generates a cross-industry comparison report with heatmap
and radar chart for multi-indicator analysis.
"""

from pathlib import Path
from typing import Dict, List, Optional

from pmi_analyzer.reporter.base import BaseReport, ReportConfig
from pmi_analyzer.types import ShamkhMetrics

# All 11 sub-indicator field names
_INDICATORS = [
    "pmi_total",
    "production",
    "new_orders",
    "sales",
    "raw_materials_inv",
    "final_goods_inv",
    "input_price",
    "production_expectations",
    "employment",
    "exports",
    "delivery_speed",
    "business_activity",
]


class IndustryReport(BaseReport):
    """Industry breakdown PMI report.

    Generates a multi-industry comparison report with:
    - Heatmap of all sub-indicators across industries
    - Radar chart for multi-indicator comparison
    - Comparison table with expansion/contraction status per cell
    - Summary ranking of industries by PMI total

    Usage::

        from pmi_analyzer.reporter.industry import IndustryReport
        from pmi_analyzer.reporter.base import ReportConfig

        report = IndustryReport(ReportConfig(language="fa", export_format="html"))
        path = report.generate_multi(industry_metrics, output_path=Path("output/industry.html"))
    """

    def generate(
        self,
        metrics: ShamkhMetrics,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate a single-industry report (wraps generate_multi for one entry).

        Args:
            metrics: PMI metrics for a single industry or aggregate.
            output_path: Output file path.

        Returns:
            Path to generated report.
        """
        return self.generate_multi(
            {metrics.month: metrics},
            output_path=output_path or self.config.output_dir / f"industry_{metrics.month}.html",
        )

    def generate_multi(
        self,
        industry_data: Dict[str, ShamkhMetrics],
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate a multi-industry breakdown report.

        Args:
            industry_data: Mapping of industry name -> ShamkhMetrics.
            output_path: Output file path.

        Returns:
            Path to generated report.
        """
        if not industry_data:
            raise ValueError("industry_data must not be empty")

        output_path = output_path or self.config.output_dir / "industry_breakdown.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._build_html(industry_data)
        output_path.write_text(html, encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------
    # HTML building
    # ------------------------------------------------------------------

    def _build_html(self, industry_data: Dict[str, ShamkhMetrics]) -> str:
        """Build the full HTML report."""
        rtl = self._get_rtl_style()
        title = self._get_text("title")
        industries = list(industry_data.keys())

        heatmap_js = self._build_heatmap_js(industry_data)
        radar_js = self._build_radar_js(industry_data)
        table_rows = self._build_table_rows(industry_data)
        ranking_rows = self._build_ranking_rows(industry_data)

        align = "right" if self.config.language == "fa" else "left"

        return f"""<!DOCTYPE html>
<html {rtl}>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Industry Breakdown</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Tahoma, Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white;
                      padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,.1); }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .header {{ text-align: center; border-bottom: 2px solid #3498db;
                   padding-bottom: 20px; margin-bottom: 30px; }}
        .charts {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.9em; }}
        th, td {{ padding: 10px; text-align: {align}; border: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .expansion {{ color: #27ae60; font-weight: bold; }}
        .contraction {{ color: #e74c3c; font-weight: bold; }}
        .neutral {{ color: #f39c12; font-weight: bold; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{title}</h1>
        <h2>Industry Breakdown — {len(industries)} {'صنعت' if self.config.language == 'fa' else 'Industries'}</h2>
    </div>

    <div class="charts">
        <div id="heatmap" style="width:900px;height:500px;"></div>
        <div id="radar" style="width:500px;height:500px;"></div>
    </div>

    <h3>{'جدول مقایسه‌ای' if self.config.language == 'fa' else 'Comparison Table'}</h3>
    <table>
        <thead><tr>
            <th>{'صنعت' if self.config.language == 'fa' else 'Industry'}</th>
            {''.join(f'<th>{self._get_indicator_name(ind)}</th>' for ind in _INDICATORS)}
        </tr></thead>
        <tbody>{table_rows}</tbody>
    </table>

    <h3>{'رتبه‌بندی بر اساس شاخص کل' if self.config.language == 'fa' else 'Ranking by PMI Total'}</h3>
    <table>
        <thead><tr>
            <th>#</th>
            <th>{'صنعت' if self.config.language == 'fa' else 'Industry'}</th>
            <th>PMI</th>
            <th>{'وضعیت' if self.config.language == 'fa' else 'Status'}</th>
        </tr></thead>
        <tbody>{ranking_rows}</tbody>
    </table>
</div>
{heatmap_js}
{radar_js}
</body></html>"""

    def _build_heatmap_js(self, industry_data: Dict[str, ShamkhMetrics]) -> str:
        """Build Plotly heatmap JS block."""
        industries = list(industry_data.keys())
        indicators = _INDICATORS
        indicator_labels = [self._get_indicator_name(i) for i in indicators]

        z_rows = []
        for ind_name in industries:
            m = industry_data[ind_name]
            row = [getattr(m, field, None) for field in indicators]
            row = [v if v is not None else 0 for v in row]
            z_rows.append(row)

        import json
        z_json = json.dumps(z_rows)
        x_json = json.dumps(indicator_labels)
        y_json = json.dumps(industries)

        return f"""<script>
Plotly.newPlot('heatmap', [{{
    type: 'heatmap',
    z: {z_json},
    x: {x_json},
    y: {y_json},
    colorscale: [[0,'#e74c3c'],[0.5,'#f39c12'],[1,'#27ae60']],
    zmin: 0, zmax: 100,
    text: {z_json},
    texttemplate: '%{{text:.1f}}',
    showscale: true
}}], {{
    title: '{'نقشه حرارتی زیرشاخص‌ها' if self.config.language == 'fa' else 'Sub-Indicator Heatmap'}',
    margin: {{t:60,b:120,l:120,r:20}},
    xaxis: {{tickangle: -30}}
}});
</script>"""

    def _build_radar_js(self, industry_data: Dict[str, ShamkhMetrics]) -> str:
        """Build Plotly radar chart JS block."""
        indicators = _INDICATORS
        indicator_labels = [self._get_indicator_name(i) for i in indicators]
        # Close the polygon
        closed_labels = indicator_labels + [indicator_labels[0]]

        import json
        traces = []
        for ind_name, m in industry_data.items():
            vals = [getattr(m, f, None) or 0 for f in indicators]
            vals_closed = vals + [vals[0]]
            traces.append({
                "type": "scatterpolar",
                "r": vals_closed,
                "theta": closed_labels,
                "fill": "toself",
                "name": ind_name,
                "opacity": 0.6,
            })

        traces_json = json.dumps(traces)
        return f"""<script>
Plotly.newPlot('radar', {traces_json}, {{
    polar: {{radialaxis: {{visible:true, range:[0,100]}}}},
    title: '{'نمودار رادار' if self.config.language == 'fa' else 'Radar Chart'}',
    showlegend: true
}});
</script>"""

    def _build_table_rows(self, industry_data: Dict[str, ShamkhMetrics]) -> str:
        """Build HTML table rows for all industries."""
        rows = ""
        for ind_name, m in industry_data.items():
            cells = f"<td><strong>{ind_name}</strong></td>"
            for field in _INDICATORS:
                val = getattr(m, field, None)
                if val is None:
                    cells += "<td>—</td>"
                else:
                    css = "expansion" if val > 50 else ("contraction" if val < 50 else "neutral")
                    cells += f'<td class="{css}">{val:.1f}</td>'
            rows += f"<tr>{cells}</tr>\n"
        return rows

    def _build_ranking_rows(self, industry_data: Dict[str, ShamkhMetrics]) -> str:
        """Build ranking table rows sorted by pmi_total descending."""
        ranked = sorted(
            industry_data.items(),
            key=lambda kv: kv[1].pmi_total or 0,
            reverse=True,
        )
        rows = ""
        for rank, (ind_name, m) in enumerate(ranked, start=1):
            pmi = m.pmi_total
            if pmi is None:
                rows += f"<tr><td>{rank}</td><td>{ind_name}</td><td>—</td><td>—</td></tr>\n"
            else:
                css = "expansion" if pmi > 50 else ("contraction" if pmi < 50 else "neutral")
                status = self._get_status(pmi)
                rows += (
                    f'<tr><td>{rank}</td><td>{ind_name}</td>'
                    f'<td class="{css}">{pmi:.1f}</td>'
                    f'<td class="{css}">{status}</td></tr>\n'
                )
        return rows
