"""Plotly plotter for Shamkh metrics."""

import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path
from typing import Optional
from pmi_analyzer.types import PlotConfig
from pmi_analyzer.i18n import _

pio.templates.default = "plotly_white"


class PlotlyPlotter:
    """Plotly implementation for plotting Shamkh metrics."""

    def __init__(self, config: Optional[PlotConfig] = None):
        self.config = config or PlotConfig()

    def plot_full_shamkh(self, df: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
        """Plot ALL Shamkh sub-indicators."""
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        sub_indices = [
            ("production", _("Production")),
            ("new_orders", _("New Orders")),
            ("sales", _("Sales")),
            ("raw_materials_inv", _("Raw Materials Inventory")),
            ("final_goods_inv", _("Final Goods Inventory")),
            ("input_price", _("Input Price")),
            ("production_expectations", _("Production Expectations")),
            ("employment", _("Employment")),
            ("exports", _("Exports")),
            ("delivery_speed", _("Delivery Speed")),
            ("business_activity", _("Business Activity")),
        ]

        available = [(col, title) for col, title in sub_indices if col in df.columns and df[col].notna().any()]
        n = len(available)
        cols = 3
        rows = (n + cols) // cols

        titles = [title for _, title in available] + [_("Shamkh Total")]
        fig = make_subplots(
            rows=rows, cols=cols,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=titles
        )

        for i, (col, title) in enumerate(available):
            row = (i // cols) + 1
            col_num = (i % cols) + 1
            fig.add_trace(
                go.Scatter(
                    x=df["month"], y=df[col],
                    mode="lines+markers",
                    name=title,
                    line=dict(width=2),
                    marker=dict(size=6),
                ),
                row=row, col=col_num
            )
            fig.add_hline(y=50, line=dict(color="red", dash="dash"), row=row, col=col_num)

        if "shamkh_total" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["month"], y=df["shamkh_total"],
                    mode="lines+markers",
                    name=_("Shamkh Total"),
                    line=dict(color="#ff7f0e", width=3),
                    marker=dict(size=8),
                ),
                row=rows, col=cols
            )
            fig.add_hline(y=50, line=dict(color="red", dash="dash"), row=rows, col=cols)

        fig.update_layout(
            height=max(800, rows * 280),
            title_text=_("Full Shamkh Sub-Indicators"),
            title_x=0.5,
            showlegend=False,
            template="plotly_white",
        )
        fig.update_xaxes(title_text=_("Month"))

        filepath = output_dir / "shamkh_full.html"
        fig.write_html(str(filepath))
        return filepath

    def plot_composite_indicators(self, df: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
        """Plot composite/advanced indicators."""
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        composite_cols = [
            ("demand_pressure", _("Demand Pressure")),
            ("production_capacity", _("Production Capacity")),
            ("labor_stress", _("Labor Market Stress")),
            ("recession_severity", _("Recession Severity")),
        ]
        available = [(col, title) for col, title in composite_cols if col in df.columns]

        fig = make_subplots(rows=2, cols=2, subplot_titles=[t for _, t in available])

        for i, (col, title) in enumerate(available):
            row = (i // 2) + 1
            col_num = (i % 2) + 1
            fig.add_trace(
                go.Scatter(x=df["month"], y=df[col], mode="lines+markers", name=title, line=dict(width=2)),
                row=row, col=col_num
            )
            ref_y = 50 if col in ("demand_pressure", "labor_stress") else 0
            fig.add_hline(y=ref_y, line=dict(color="red", dash="dash"), row=row, col=col_num)

        fig.update_layout(
            height=700,
            title_text=_("Composite Indicators"),
            title_x=0.5,
            showlegend=False,
            template="plotly_white",
        )
        filepath = output_dir / "composite_indicators.html"
        fig.write_html(str(filepath))
        return filepath

    def plot_labor_and_exports(self, df: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
        """Plot Employment and Exports together."""
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        fig = go.Figure()
        for col, name, color in [
            ("employment", _("Employment"), "#1f77b4"),
            ("exports", _("Exports"), "#2ca02c"),
        ]:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["month"], y=df[col],
                    mode="lines+markers", name=name,
                    line=dict(color=color, width=3), marker=dict(size=8)
                ))
        fig.add_hline(y=50, line=dict(color="red", dash="dash"), annotation_text="50")
        fig.update_layout(
            height=450, title_text=_("Employment & Exports"),
            title_x=0.5, xaxis_title=_("Month"), yaxis_title="PMI",
            showlegend=True, template="plotly_white"
        )
        filepath = output_dir / "labor_and_exports.html"
        fig.write_html(str(filepath))
        return filepath

    def plot_production_expectations(self, df: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
        """Plot production expectations vs actual production."""
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        fig = go.Figure()
        for col, name, color, dash in [
            ("production", _("Production"), "#1f77b4", "solid"),
            ("production_expectations", _("Production Expectations"), "#2ca02c", "dash"),
        ]:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["month"], y=df[col],
                    mode="lines+markers", name=name,
                    line=dict(color=color, width=3, dash=dash), marker=dict(size=8)
                ))
        fig.add_hline(y=50, line=dict(color="red", dash="dash"))
        fig.update_layout(
            height=500,
            title_text="Production Expectations vs Actual",
            title_x=0.5, xaxis_title=_("Month"), yaxis_title="PMI",
            showlegend=True, template="plotly_white"
        )
        filepath = output_dir / "production_expectations.html"
        fig.write_html(str(filepath))
        return filepath

    def plot_inventory_comparison(self, df: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
        """Plot Raw Materials vs Final Goods Inventory comparison."""
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        fig = go.Figure()
        for col, name, color in [
            ("raw_materials_inv", _("Raw Materials Inventory"), "#1f77b4"),
            ("final_goods_inv", _("Final Goods Inventory"), "#2ca02c"),
        ]:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["month"], y=df[col],
                    mode="lines+markers", name=name,
                    line=dict(color=color, width=3), marker=dict(size=8)
                ))
        fig.add_hline(y=50, line=dict(color="red", dash="dash"))
        fig.update_layout(
            height=450, title_text=_("Inventory Comparison"),
            title_x=0.5, xaxis_title=_("Month"), yaxis_title="PMI",
            showlegend=True, template="plotly_white"
        )
        filepath = output_dir / "inventory_comparison.html"
        fig.write_html(str(filepath))
        return filepath
