"""Base report class for PMI Analyzer.

This module provides the foundational classes for generating PMI reports
with support for multiple languages and export formats.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from pmi_analyzer.types import ShamkhMetrics


@dataclass
class ReportConfig:
    """Configuration for report generation.

    Attributes:
        language: Language code ("fa" for Persian, "en" for English).
        export_format: Export format ("html", "pdf", "docx").
        output_dir: Directory for output files.
        include_charts: Whether to include interactive charts.
        include_tables: Whether to include data tables.
        include_analysis: Whether to include text analysis.
        title: Custom report title (optional).

    Example:
        >>> config = ReportConfig(language="fa", export_format="html")
        >>> config.language
        'fa'
    """

    language: str = "fa"
    export_format: str = "html"
    output_dir: Path = field(default_factory=lambda: Path("output/reports"))
    include_charts: bool = True
    include_tables: bool = True
    include_analysis: bool = True
    title: Optional[str] = None


class BaseReport(ABC):
    """Abstract base class for PMI reports.

    All report types inherit from this class and implement
    the `generate` method.
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialize the report.

        Args:
            config: Report configuration. Uses defaults if None.
        """
        self.config = config or ReportConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def generate(self, metrics: ShamkhMetrics, output_path: Optional[Path] = None) -> Path:
        """Generate the report.

        Args:
            metrics: PMI metrics data for the report.
            output_path: Output file path. Uses default if None.

        Returns:
            Path to the generated report file.
        """
        pass

    def _get_text(self, key: str, default: str = "") -> str:
        """Get translated text based on configured language.

        Args:
            key: Translation key.
            default: Default value if translation not found.

        Returns:
            Translated text.
        """
        translations = {
            "fa": {
                "title": "گزارش شاخص مدیران خرید",
                "month": "ماه",
                "pmi_total": "شاخص کل",
                "production": "تولید",
                "new_orders": "سفارشات جدید",
                "sales": "فروش",
                "raw_materials_inv": "موجودی مواد اولیه",
                "final_goods_inv": "موجودی محصول نهایی",
                "input_price": "قیمت مواد اولیه",
                "production_expectations": "انتظارات تولید",
                "employment": "استخدام",
                "exports": "صادرات",
                "delivery_speed": "سرعت تحویل",
                "business_activity": "فعالیت اقتصادی",
                "expansion": "رشد",
                "contraction": "رکود",
                "neutral": "خنثی",
                "analysis": "تحلیل",
                "summary": "خلاصه",
                "trend": "روند",
                "alert": "هشدار",
                "recession_alert": "هشدار رکود",
                "expansion_alert": "هشدار رشد",
                "consecutive_months": "ماه‌های متوالی",
                "value": "مقدار",
                "status": "وضعیت",
            },
            "en": {
                "title": "PMI Report",
                "month": "Month",
                "pmi_total": "PMI Total",
                "production": "Production",
                "new_orders": "New Orders",
                "sales": "Sales",
                "raw_materials_inv": "Raw Materials Inventory",
                "final_goods_inv": "Final Goods Inventory",
                "input_price": "Input Price",
                "production_expectations": "Production Expectations",
                "employment": "Employment",
                "exports": "Exports",
                "delivery_speed": "Delivery Speed",
                "business_activity": "Business Activity",
                "expansion": "Expansion",
                "contraction": "Contraction",
                "neutral": "Neutral",
                "analysis": "Analysis",
                "summary": "Summary",
                "trend": "Trend",
                "alert": "Alert",
                "recession_alert": "Recession Alert",
                "expansion_alert": "Expansion Alert",
                "consecutive_months": "Consecutive Months",
                "value": "Value",
                "status": "Status",
            },
        }
        return translations.get(self.config.language, {}).get(key, default or key)

    def _get_indicator_name(self, indicator: str) -> str:
        """Get translated indicator name.

        Args:
            indicator: Indicator field name.

        Returns:
            Translated indicator name.
        """
        return self._get_text(indicator, indicator)

    def _get_status(self, value: float) -> str:
        """Get status text based on PMI value.

        Args:
            value: PMI value (0-100).

        Returns:
            Status text (expansion/contraction/neutral).
        """
        if value > 50:
            return self._get_text("expansion")
        elif value < 50:
            return self._get_text("contraction")
        else:
            return self._get_text("neutral")

    def _get_status_color(self, value: float) -> str:
        """Get color based on PMI value.

        Args:
            value: PMI value (0-100).

        Returns:
            Hex color code.
        """
        if value > 55:
            return "#2ecc71"  # Strong green
        elif value > 50:
            return "#27ae60"  # Green
        elif value == 50:
            return "#f39c12"  # Yellow
        elif value > 45:
            return "#e74c3c"  # Red
        else:
            return "#c0392b"  # Dark red

    def _get_rtl_style(self) -> str:
        """Get CSS style for RTL layout.

        Returns:
            CSS style string.
        """
        if self.config.language == "fa":
            return 'dir="rtl" style="text-align: right; font-family: Tahoma, Arial, sans-serif;"'
        return 'dir="ltr" style="text-align: left;"'
