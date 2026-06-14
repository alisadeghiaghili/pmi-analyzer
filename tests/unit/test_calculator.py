"""Tests for MetricsCalculator."""

import pytest
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.metrics.calculator import MetricsCalculator


@pytest.fixture
def full_metrics():
    return [
        ShamkhMetrics(
            month="1402-01",
            production=55.0, new_orders=52.0, sales=48.0,
            raw_materials_inv=45.0, final_goods_inv=42.0,
            input_price=65.0, production_expectations=58.0,
            employment=49.3, exports=40.9,
            delivery_speed=49.75, business_activity=50.9,
        ),
        ShamkhMetrics(
            month="1402-02",
            production=53.0, new_orders=50.0, sales=45.0,
            raw_materials_inv=43.0, final_goods_inv=40.0,
            input_price=70.0, production_expectations=50.0,
            employment=48.5, exports=39.0,
            delivery_speed=48.5, business_activity=49.0,
        ),
        ShamkhMetrics(
            month="1402-03",
            production=46.6, new_orders=36.5, sales=41.3,
            raw_materials_inv=41.3, final_goods_inv=38.0,
            input_price=77.5, production_expectations=32.2,
            employment=49.32, exports=40.9,
            delivery_speed=49.75, business_activity=50.97,
        ),
    ]


def test_calculate_returns_dataframe(full_metrics):
    df = MetricsCalculator().calculate(full_metrics)
    assert len(df) == 3


def test_all_sub_indicators_present(full_metrics):
    df = MetricsCalculator().calculate(full_metrics)
    for col in MetricsCalculator.SUB_INDICATORS:
        assert col in df.columns


def test_shamkh_total_calculated(full_metrics):
    df = MetricsCalculator().calculate(full_metrics)
    assert "shamkh_total" in df.columns


def test_composite_indicators_present(full_metrics):
    df = MetricsCalculator().calculate(full_metrics)
    assert "demand_pressure" in df.columns
    assert "production_capacity" in df.columns
    assert "labor_stress" in df.columns
    assert "recession_severity" in df.columns
    assert "supply_chain_stress" in df.columns


def test_expectations_gap(full_metrics):
    df = MetricsCalculator().calculate(full_metrics)
    assert "expectations_gap" in df.columns
    assert "predicted_production_trend" in df.columns


def test_recession_classification_deep(full_metrics):
    df = MetricsCalculator().calculate(full_metrics)
    last = df.iloc[-1]
    # shamkh_total in last row = (46.6+36.5+41.3)/3 = 41.47 => severity=8.5 => رکود متوسط
    assert last["recession_classification"] in ["رکود متوسط", "رکود عمیق و فراگیر", "رکود خفیف"]


def test_trend_column_values(full_metrics):
    df = MetricsCalculator().calculate(full_metrics)
    assert set(df["production_trend"].unique()).issubset({"رونق", "رکود", "خنثی"})
