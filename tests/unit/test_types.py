"""TDD tests for pmi_analyzer/types.py.

These tests define EXPECTED behaviour of ShamkhMetrics.
Write them first; implement types.py to make them pass.
"""

import pytest
from pmi_analyzer.types import ShamkhMetrics, PlotType, DataSource, PlotConfig, DownloadConfig


# ------------------------------------------------------------------ #
#  ShamkhMetrics construction
# ------------------------------------------------------------------ #

class TestShamkhMetricsConstruction:
    def test_requires_month(self):
        with pytest.raises(TypeError):
            ShamkhMetrics()

    def test_all_optional_fields_default_to_none(self):
        m = ShamkhMetrics(month="1402-01")
        for field in [
            "production", "new_orders", "sales", "raw_materials_inv",
            "final_goods_inv", "input_price", "production_expectations",
            "employment", "exports", "delivery_speed", "business_activity",
        ]:
            assert getattr(m, field) is None, f"{field} should default to None"

    def test_month_is_stored_correctly(self):
        m = ShamkhMetrics(month="1402-06")
        assert m.month == "1402-06"

    def test_full_construction(self):
        m = ShamkhMetrics(
            month="1402-01",
            production=52.0, new_orders=48.0, sales=50.0,
            input_price=75.0, employment=49.0,
        )
        assert m.production == 52.0
        assert m.employment == 49.0


# ------------------------------------------------------------------ #
#  validate()
# ------------------------------------------------------------------ #

class TestShamkhMetricsValidate:
    def test_empty_metrics_is_invalid(self):
        assert ShamkhMetrics(month="1402-01").validate() is False

    def test_single_field_makes_valid(self):
        assert ShamkhMetrics(month="1402-01", production=50.0).validate() is True

    def test_full_metrics_is_valid(self):
        m = ShamkhMetrics(
            month="1402-01",
            production=52.0, new_orders=48.0, sales=50.0,
            raw_materials_inv=47.0, final_goods_inv=45.0, input_price=75.0,
            production_expectations=55.0, employment=49.0,
            exports=44.0, delivery_speed=46.0, business_activity=51.0,
        )
        assert m.validate() is True


# ------------------------------------------------------------------ #
#  is_complete()
# ------------------------------------------------------------------ #

class TestShamkhMetricsIsComplete:
    def test_empty_is_not_complete(self):
        assert ShamkhMetrics(month="1402-01").is_complete() is False

    def test_missing_one_field_is_not_complete(self):
        m = ShamkhMetrics(
            month="1402-01",
            production=52.0, new_orders=48.0, sales=50.0,
            raw_materials_inv=47.0, final_goods_inv=45.0, input_price=75.0,
            production_expectations=55.0, employment=49.0,
            exports=44.0, delivery_speed=46.0,
            # business_activity intentionally missing
        )
        assert m.is_complete() is False

    def test_all_fields_present_is_complete(self):
        m = ShamkhMetrics(
            month="1402-01",
            production=52.0, new_orders=48.0, sales=50.0,
            raw_materials_inv=47.0, final_goods_inv=45.0, input_price=75.0,
            production_expectations=55.0, employment=49.0,
            exports=44.0, delivery_speed=46.0, business_activity=51.0,
        )
        assert m.is_complete() is True


# ------------------------------------------------------------------ #
#  Enums
# ------------------------------------------------------------------ #

class TestEnums:
    def test_plot_type_values(self):
        assert PlotType.PLOTLY_HTML.value == "plotly_html"
        assert PlotType.PLOTLY_PNG.value == "plotly_png"
        assert PlotType.MATPLOTLIB.value == "matplotlib"

    def test_data_source_values(self):
        assert DataSource.ICCIM.value == "iccima.ir"
        assert DataSource.CSV.value == "csv"
        assert DataSource.PDF.value == "pdf"


# ------------------------------------------------------------------ #
#  Config dataclasses
# ------------------------------------------------------------------ #

class TestConfigs:
    def test_plot_config_defaults(self):
        cfg = PlotConfig()
        assert cfg.plot_type == PlotType.PLOTLY_HTML
        assert cfg.height == 1000
        assert cfg.width == 1200

    def test_download_config_defaults(self):
        cfg = DownloadConfig()
        assert "iccima.ir" in cfg.base_url
        assert cfg.timeout == 30
