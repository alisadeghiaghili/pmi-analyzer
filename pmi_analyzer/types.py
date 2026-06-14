"""Type definitions for pmi_analyzer package."""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from enum import Enum


class DataSource(Enum):
    """Data source types."""

    ICCIM = "iccima.ir"
    CSV = "csv"
    PDF = "pdf"


class PlotType(Enum):
    """Plot types."""

    PLOTLY_HTML = "plotly_html"
    PLOTLY_PNG = "plotly_png"
    MATPLOTLIB = "matplotlib"


@dataclass
class ShamkhMetrics:
    """Data class for all Shamkh sub-indicators (Full Set)."""

    month: str

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
        """Validate that at least one metric is present."""
        return any(
            [
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
        """Check if all metrics are present."""
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
    """Configuration for downloading reports."""

    base_url: str = "https://iccima.ir"
    output_dir: Path = field(default_factory=lambda: Path("data/reports"))
    timeout: int = 30


@dataclass
class PlotConfig:
    """Configuration for plotting."""

    output_dir: Path = field(default_factory=lambda: Path("output"))
    plot_type: PlotType = PlotType.PLOTLY_HTML
    height: int = 1000
    width: int = 1200
