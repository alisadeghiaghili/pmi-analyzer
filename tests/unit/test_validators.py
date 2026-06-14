"""TDD tests for pmi_analyzer/metrics/validators.py."""

import pytest
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.metrics.validators import MetricsValidator


def full(**overrides):
    base = dict(
        month="1402-01",
        production=52.0, new_orders=48.0, sales=50.0,
        raw_materials_inv=47.0, final_goods_inv=45.0, input_price=75.0,
        production_expectations=55.0, employment=49.0,
        exports=44.0, delivery_speed=46.0, business_activity=51.0,
    )
    base.update(overrides)
    return ShamkhMetrics(**base)


class TestMetricsValidator:
    v = MetricsValidator()

    def test_valid_full_metrics_passes(self):
        assert self.v.validate(full()) is True

    def test_empty_month_raises(self):
        with pytest.raises(Exception):
            self.v.validate(ShamkhMetrics(month=""))

    def test_value_below_zero_raises(self):
        with pytest.raises(Exception):
            self.v.validate(full(production=-1.0))

    def test_value_above_100_raises(self):
        with pytest.raises(Exception):
            self.v.validate(full(production=101.0))

    def test_boundary_zero_passes(self):
        assert self.v.validate(full(production=0.0)) is True

    def test_boundary_100_passes(self):
        assert self.v.validate(full(production=100.0)) is True

    def test_all_none_raises(self):
        with pytest.raises(Exception):
            self.v.validate(ShamkhMetrics(month="1402-01"))
