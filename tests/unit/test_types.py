"""Tests for ShamkhMetrics types."""

import pytest
from pmi_analyzer.types import ShamkhMetrics


def test_validate_at_least_one_field():
    m = ShamkhMetrics(month="1402-01", production=50.0)
    assert m.validate() is True


def test_validate_empty_fails():
    m = ShamkhMetrics(month="1402-01")
    assert m.validate() is False


def test_is_complete_all_fields():
    m = ShamkhMetrics(
        month="1402-01",
        production=55.0, new_orders=52.0, sales=48.0,
        raw_materials_inv=45.0, final_goods_inv=42.0,
        input_price=65.0, production_expectations=58.0,
        employment=49.3, exports=40.9,
        delivery_speed=49.75, business_activity=50.9,
    )
    assert m.is_complete() is True


def test_is_complete_missing_field():
    m = ShamkhMetrics(month="1402-01", production=55.0)
    assert m.is_complete() is False
