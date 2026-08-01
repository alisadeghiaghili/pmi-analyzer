"""Report-specific chart generators for PMI Analyzer.

Provides Plotly-based chart builders for use inside reporter modules:
  - Gauge charts for single PMI values
  - Heatmaps for industry/sub-indicator comparison
  - Radar charts for multi-indicator profiles
  - Sparklines for inline trend indicators

All functions return a Plotly Figure object that can be saved as
HTML (``fig.write_html``) or PNG (``fig.write_image``, requires kaleido).
"""

from typing import Dict, List, Optional, Sequence

try:
    import plotly.graph_objects as go
    import plotly.express as px
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False

from pmi_analyzer.types import ShamkhMetrics

# Indicator fields in display order
_INDICATORS: List[str] = [
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

# English labels matching field order
_LABELS_EN: List[str] = [
    "PMI Total",
    "Production",
    "New Orders",
    "Sales",
    "Raw Materials Inv.",
    "Final Goods Inv.",
    "Input Price",
    "Production Exp.",
    "Employment",
    "Exports",
    "Delivery Speed",
    "Business Activity",
]

_LABELS_FA: List[str] = [
    "شاخص کل",
    "تولید",
    "سفارشات جدید",
    "فروش",
    "موجودی مواد اولیه",
    "موجودی محصول نهایی",
    "قیمت مواد اولیه",
    "انتظارات تولید",
    "استخدام",
    "صادرات",
    "سرعت تحویل",
    "فعالیت اقتصادی",
]


def _require_plotly() -> None:
    if not _PLOTLY_AVAILABLE:
        raise ImportError(
            "plotly is required for report_charts. "
            "Install with: pip install plotly"
        )


def _labels(lang: str = "en") -> List[str]:
    return _LABELS_FA if lang == "fa" else _LABELS_EN


def _color(value: float) -> str:
    """Return a hex colour for a PMI value."""
    if value > 55:
        return "#2ecc71"
    elif value > 50:
        return "#27ae60"
    elif value == 50:
        return "#f39c12"
    elif value > 45:
        return "#e74c3c"
    return "#c0392b"


# ---------------------------------------------------------------------------
# Gauge chart
# ---------------------------------------------------------------------------

def gauge_chart(
    value: float,
    title: str = "PMI",
    lang: str = "en",
    height: int = 300,
) -> "go.Figure":
    """Create a gauge (indicator) chart for a single PMI value.

    Args:
        value: PMI value (0–100).
        title: Chart title.
        lang: Language code for labels (``"fa"`` or ``"en"``).
        height: Chart height in pixels.

    Returns:
        Plotly Figure.

    Example::

        fig = gauge_chart(47.3, title="شاخص کل", lang="fa")
        fig.write_html("gauge.html")
    """
    _require_plotly()
    bar_color = _color(value)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": title},
        delta={"reference": 50, "relative": False},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": bar_color},
            "steps": [
                {"range": [0, 50], "color": "#fde0dd"},
                {"range": [50, 100], "color": "#e5f5e0"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 3},
                "thickness": 0.75,
                "value": 50,
            },
        },
    ))
    fig.update_layout(height=height, margin=dict(t=40, b=10, l=20, r=20))
    return fig


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

def heatmap_chart(
    industry_data: Dict[str, ShamkhMetrics],
    lang: str = "en",
    height: int = 500,
) -> "go.Figure":
    """Create a heatmap for industry × sub-indicator PMI values.

    Args:
        industry_data: Mapping of industry name → ShamkhMetrics.
        lang: Language code for axis labels.
        height: Chart height in pixels.

    Returns:
        Plotly Figure.

    Example::

        fig = heatmap_chart({"Total": metrics}, lang="fa")
        fig.write_html("heatmap.html")
    """
    _require_plotly()
    labels = _labels(lang)
    industries = list(industry_data.keys())

    z: List[List[float]] = []
    text: List[List[str]] = []
    for ind in industries:
        m = industry_data[ind]
        row = [getattr(m, f, None) or 0.0 for f in _INDICATORS]
        z.append(row)
        text.append([f"{v:.1f}" for v in row])

    fig = go.Figure(go.Heatmap(
        z=z,
        x=labels,
        y=industries,
        text=text,
        texttemplate="%{text}",
        colorscale=[[0, "#e74c3c"], [0.5, "#f39c12"], [1, "#27ae60"]],
        zmin=0,
        zmax=100,
        showscale=True,
    ))
    fig.update_layout(
        height=height,
        xaxis_tickangle=-30,
        margin=dict(t=40, b=120, l=150, r=20),
    )
    return fig


# ---------------------------------------------------------------------------
# Radar chart
# ---------------------------------------------------------------------------

def radar_chart(
    industry_data: Dict[str, ShamkhMetrics],
    lang: str = "en",
    height: int = 500,
) -> "go.Figure":
    """Create a radar (polar) chart for multi-industry PMI comparison.

    Args:
        industry_data: Mapping of industry name → ShamkhMetrics.
        lang: Language code for axis labels.
        height: Chart height in pixels.

    Returns:
        Plotly Figure.

    Example::

        fig = radar_chart({"Automotive": m1, "Food": m2}, lang="en")
        fig.write_image("radar.png")  # requires kaleido
    """
    _require_plotly()
    labels = _labels(lang)
    closed_labels = labels + [labels[0]]

    traces = []
    for ind_name, m in industry_data.items():
        vals = [getattr(m, f, None) or 0.0 for f in _INDICATORS]
        closed_vals = vals + [vals[0]]
        traces.append(go.Scatterpolar(
            r=closed_vals,
            theta=closed_labels,
            fill="toself",
            name=ind_name,
            opacity=0.65,
        ))

    fig = go.Figure(traces)
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=height,
        margin=dict(t=40, b=40, l=60, r=60),
    )
    return fig


# ---------------------------------------------------------------------------
# Sparkline
# ---------------------------------------------------------------------------

def sparkline_chart(
    values: Sequence[float],
    months: Optional[Sequence[str]] = None,
    indicator_name: str = "PMI",
    height: int = 120,
    width: int = 300,
) -> "go.Figure":
    """Create a compact sparkline for inline trend display.

    Args:
        values: Sequence of PMI values in chronological order.
        months: Optional month labels for x-axis.
        indicator_name: Name shown as the line label.
        height: Chart height in pixels.
        width: Chart width in pixels.

    Returns:
        Plotly Figure (minimal axes, suitable for embedding).

    Example::

        fig = sparkline_chart([47.1, 48.5, 50.2, 49.8], months=["1404-09", "1404-10", "1404-11", "1404-12"])
        fig.write_html("spark.html")
    """
    _require_plotly()
    x = months if months else list(range(len(values)))
    colors = [_color(v) for v in values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=list(values),
        mode="lines+markers",
        name=indicator_name,
        line=dict(width=2, color="#3498db"),
        marker=dict(color=colors, size=6),
    ))
    # 50-line reference
    fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.5)

    fig.update_layout(
        height=height,
        width=width,
        showlegend=False,
        margin=dict(t=10, b=20, l=30, r=10),
        xaxis=dict(showgrid=False, showticklabels=bool(months)),
        yaxis=dict(showgrid=True, range=[0, 100]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
