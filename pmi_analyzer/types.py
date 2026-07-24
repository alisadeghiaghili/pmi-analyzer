"""Type definitions for pmi_analyzer package.

This module defines the core data structures used throughout the PMI Analyzer
package, including the main ShamkhMetrics dataclass and configuration classes.

Example:
    >>> from pmi_analyzer.types import ShamkhMetrics
    >>> m = ShamkhMetrics(month="1405-03", pmi_total=45.9, production=48.2)
    >>> m.validate()
    True
    >>> m.is_complete()
    False
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from enum import Enum


class DataSource(Enum):
    """Enumeration of supported PMI data sources.

    Attributes:
        ICCIM: Data from Iran Chamber of Commerce (iccima.ir)
        CSV: Historical data from local CSV files
        PDF: Direct PDF report parsing
    """

    ICCIM = "iccima.ir"
    CSV = "csv"
    PDF = "pdf"


class PlotType(Enum):
    """Enumeration of supported plot output formats.

    Attributes:
        PLOTLY_HTML: Interactive Plotly charts as HTML files
        PLOTLY_PNG: Static Plotly charts as PNG images
        MATPLOPLIB: Static charts using matplotlib library
    """

    PLOTLY_HTML = "plotly_html"
    PLOTLY_PNG = "plotly_png"
    MATPLOTLIB = "matplotlib"


@dataclass
class ShamkhMetrics:
    """Data class representing a complete set of Shamkh (PMI) sub-indicators.

    This is the primary data structure for storing parsed PMI data from
    ICCIMA reports. Each instance represents one month's measurements.

    Attributes:
        month: Month identifier in "YYYY-MM" format (e.g., "1405-03").
        pmi_total: Composite headline PMI index (شاخص کل). Values > 50
            indicate expansion, < 50 indicate contraction.
        production: Production volume indicator (تولید).
        new_orders: New customer orders indicator (سفارشات جدید).
        sales: Product sales volume indicator (فروش).
        raw_materials_inv: Raw materials inventory level (موجودی مواد اولیه).
        final_goods_inv: Finished goods inventory level (موجودی محصول نهایی).
        input_price: Purchase price of raw materials (قیمت مواد اولیه).
        production_expectations: Future production outlook (انتظارات تولید).
        employment: Hiring activity indicator (استخدام).
        exports: Export volume indicator (صادرات).
        delivery_speed: Supplier delivery times (سرعت تحویل).
        business_activity: Business activity level (فعالیت اقتصادی).

    Example:
        >>> m = ShamkhMetrics(
        ...     month="1405-03",
        ...     pmi_total=45.9,
        ...     production=48.2,
        ...     new_orders=42.1,
        ... )
        >>> m.validate()
        True
        >>> m.month
        '1405-03'

    Note:
        All indicator values are on a 0-100 scale where:
        - Values > 50 indicate expansion/growth
        - Values = 50 indicate no change
        - Values < 50 indicate contraction/decline
    """

    month: str

    # Composite headline PMI index (derived; not required for is_complete)
    pmi_total: Optional[float] = None  # شاخص کل مدیران خرید

    # Core PMI indicators
    production: Optional[float] = None  # تولید
    new_orders: Optional[float] = None  # سفارشات جدید
    sales: Optional[float] = None  # سنجه فروش محصولات
    raw_materials_inv: Optional[float] = None  # موجودی مواد اولیه
    final_goods_inv: Optional[float] = None  # موجودی محصول نهایی در انبار
    input_price: Optional[float] = None  # قیمت خرید مواد اولیه
    production_expectations: Optional[float] = None  # انتظارات تولید برای ماه آینده

    # Extended PMI indicators
    employment: Optional[float] = None  # بهکارگیری نیروی انسانی (اشتغال)
    exports: Optional[float] = None  # صادرات کالا یا خدمات
    delivery_speed: Optional[float] = None  # سرعت تحویل سفارشات
    business_activity: Optional[float] = None  # میزان فعالیت‌های کسب‌وکار

    def validate(self) -> bool:
        """Validate that at least one metric is present.

        Returns:
            True if at least one indicator has a non-None value, False otherwise.

        Example:
            >>> m = ShamkhMetrics(month="1405-03", pmi_total=45.9)
            >>> m.validate()
            True
            >>> empty = ShamkhMetrics(month="1405-03")
            >>> empty.validate()
            False
        """
        return any(
            [
                self.pmi_total is not None,
                self.production is not None,
                self.new_orders is not None,
                self.sales is not None,
                self.raw_materials_inv is not None,
                self.final_goods_inv is not None,
                self.production_expectations is not None,
                self.employment is not None,
                self.exports is not None,
                self.delivery_speed is not None,
                self.business_activity is not None,
            ]
        )

    def is_complete(self) -> bool:
        """Check if all sub-indicator fields are present.

        Note:
            pmi_total is excluded because it is a derived composite value
            that may be calculated after the sub-indicators are populated.

        Returns:
            True if all 11 sub-indicators (excluding pmi_total) are set,
            False otherwise.

        Example:
            >>> m = ShamkhMetrics(
            ...     month="1405-03",
            ...     production=48.2, new_orders=42.1, sales=47.5,
            ...     raw_materials_inv=43.8, final_goods_inv=44.1,
            ...     input_price=72.3, production_expectations=50.2,
            ...     employment=46.2, exports=41.7,
            ...     delivery_speed=47.5, business_activity=50.2,
            ... )
            >>> m.is_complete()
            True
        """
        return all(
            [
                self.production is not None,
                self.new_orders is not None,
                self.sales is not None,
                self.raw_materials_inv is not None,
                self.final_goods_inv is not None,
                self.input_price is not None,
                self.production_expectations is not None,
                self.employment is not None,
                self.exports is not None,
                self.delivery_speed is not None,
                self.business_activity is not None,
            ]
        )


@dataclass
class DownloadConfig:
    """Configuration for downloading PMI reports from ICCIMA.

    Attributes:
        base_url: Base URL for the ICCIMA website.
        output_dir: Directory to save downloaded PDF files.
        timeout: HTTP request timeout in seconds.

    Example:
        >>> config = DownloadConfig(timeout=60)
        >>> config.base_url
        'https://iccima.ir'
    """

    base_url: str = "https://iccima.ir"
    output_dir: Path = field(default_factory=lambda: Path("data/reports"))
    timeout: int = 30


@dataclass
class PlotConfig:
    """Configuration for generating PMI charts and visualizations.

    Attributes:
        output_dir: Directory to save generated chart files.
        plot_type: Format for output charts (HTML, PNG, or matplotlib).
        height: Chart height in pixels.
        width: Chart width in pixels.

    Example:
        >>> config = PlotConfig(plot_type=PlotType.PLOTLY_PNG, width=1600)
        >>> config.width
        1600
    """

    output_dir: Path = field(default_factory=lambda: Path("output"))
    plot_type: PlotType = PlotType.PLOTLY_HTML
    height: int = 1000
    width: int = 1200
