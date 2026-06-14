"""TDD tests for pmi_analyzer/metrics/calculator.py.

Defines EXPECTED behaviour. Implement MetricsCalculator to pass these.
"""

import pytest
import pandas as pd
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.metrics.calculator import MetricsCalculator


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def full(month="1402-01", **overrides):
    base = dict(
        production=52.0, new_orders=48.0, sales=50.0,
        raw_materials_inv=47.0, final_goods_inv=45.0, input_price=75.0,
        production_expectations=55.0, employment=49.0,
        exports=44.0, delivery_speed=46.0, business_activity=51.0,
    )
    base.update(overrides)
    return ShamkhMetrics(month=month, **base)


@pytest.fixture
def calc():
    return MetricsCalculator()


@pytest.fixture
def three_months():
    return [
        full("1402-01", production=52.0, new_orders=50.0, input_price=72.0),
        full("1402-02", production=48.0, new_orders=45.0, input_price=78.0),
        full("1402-03", production=44.0, new_orders=40.0, input_price=82.0),
    ]


# ------------------------------------------------------------------ #
#  Basic output
# ------------------------------------------------------------------ #

class TestCalculatorBasic:
    def test_raises_on_empty_input(self, calc):
        with pytest.raises(ValueError):
            calc.calculate([])

    def test_returns_dataframe(self, calc, three_months):
        assert isinstance(calc.calculate(three_months), pd.DataFrame)

    def test_row_count_matches_input(self, calc, three_months):
        assert len(calc.calculate(three_months)) == 3

    def test_month_column_preserved(self, calc, three_months):
        df = calc.calculate(three_months)
        assert set(df["month"]) == {"1402-01", "1402-02", "1402-03"}

    def test_sorted_by_month_ascending(self, calc):
        df = calc.calculate([full("1402-03"), full("1402-01"), full("1402-02")])
        assert list(df["month"]) == ["1402-01", "1402-02", "1402-03"]

    def test_single_record_no_crash(self, calc):
        assert len(calc.calculate([full()])) == 1


# ------------------------------------------------------------------ #
#  Trend labels
# ------------------------------------------------------------------ #

class TestTrendLabels:
    def test_trend_boom_above_50(self, calc):
        df = calc.calculate([full(production=55.0)])
        assert df.loc[0, "production_trend"] == "رونق"

    def test_trend_recession_below_50(self, calc):
        df = calc.calculate([full(production=45.0)])
        assert df.loc[0, "production_trend"] == "رکود"

    def test_trend_neutral_at_exactly_50(self, calc):
        df = calc.calculate([full(production=50.0)])
        assert df.loc[0, "production_trend"] == "خنثی"

    def test_trend_column_exists_for_all_sub_indicators(self, calc, three_months):
        df = calc.calculate(three_months)
        for ind in MetricsCalculator.SUB_INDICATORS:
            assert f"{ind}_trend" in df.columns


# ------------------------------------------------------------------ #
#  Rolling mean
# ------------------------------------------------------------------ #

class TestRollingMean:
    def test_rolling_mean_3_column_exists(self, calc, three_months):
        assert "production_rolling_mean_3" in calc.calculate(three_months).columns

    def test_rolling_mean_3_correct_value(self, calc):
        metrics = [
            full("1402-01", production=50.0),
            full("1402-02", production=52.0),
            full("1402-03", production=54.0),
        ]
        df = calc.calculate(metrics)
        assert abs(df.loc[2, "production_rolling_mean_3"] - 52.0) < 0.01

    def test_rolling_mean_first_row_is_nan(self, calc, three_months):
        df = calc.calculate(three_months)
        assert pd.isna(df.loc[0, "production_rolling_mean_3"])


# ------------------------------------------------------------------ #
#  Shamkh Total
# ------------------------------------------------------------------ #

class TestShamkhTotal:
    def test_shamkh_total_column_exists(self, calc, three_months):
        assert "shamkh_total" in calc.calculate(three_months).columns

    def test_shamkh_total_is_mean_of_key_cols(self, calc):
        df = calc.calculate([full(production=50.0, new_orders=50.0, sales=50.0)])
        assert abs(df.loc[0, "shamkh_total"] - 50.0) < 0.01

    def test_shamkh_total_below_50_in_recession(self, calc):
        df = calc.calculate([full(production=44.0, new_orders=40.0, sales=42.0)])
        assert df.loc[0, "shamkh_total"] < 50


# ------------------------------------------------------------------ #
#  Composite indicators
# ------------------------------------------------------------------ #

class TestCompositeIndicators:
    def test_demand_pressure_exists(self, calc, three_months):
        assert "demand_pressure" in calc.calculate(three_months).columns

    def test_demand_pressure_strong(self, calc):
        df = calc.calculate([full(new_orders=60.0, sales=62.0, exports=58.0)])
        assert df.loc[0, "demand_pressure_trend"] == "تقاضای قوی"

    def test_demand_pressure_weak(self, calc):
        df = calc.calculate([full(new_orders=35.0, sales=36.0, exports=34.0)])
        assert df.loc[0, "demand_pressure_trend"] == "تقاضای ضعیف"

    def test_labor_stress_exists(self, calc, three_months):
        assert "labor_stress" in calc.calculate(three_months).columns

    def test_labor_stress_equals_100_minus_employment(self, calc):
        df = calc.calculate([full(employment=49.0)])
        assert abs(df.loc[0, "labor_stress"] - 51.0) < 0.01

    def test_price_inflation_signal_exists(self, calc, three_months):
        assert "price_inflation_signal" in calc.calculate(three_months).columns

    def test_price_inflation_signal_equals_input_price_minus_50(self, calc):
        df = calc.calculate([full(input_price=75.0)])
        assert abs(df.loc[0, "price_inflation_signal"] - 25.0) < 0.01

    def test_recession_severity_exists(self, calc, three_months):
        assert "recession_severity" in calc.calculate(three_months).columns

    def test_recession_classification_deep(self, calc):
        df = calc.calculate([full(production=28.0, new_orders=25.0, sales=27.0)])
        assert df.loc[0, "recession_classification"] == "رکود عمیق و فراگیر"

    def test_supply_chain_stress_true_when_both_low(self, calc):
        df = calc.calculate([full(raw_materials_inv=40.0, new_orders=35.0)])
        assert df.loc[0, "supply_chain_stress"] == True

    def test_supply_chain_stress_false_when_healthy(self, calc):
        df = calc.calculate([full(raw_materials_inv=55.0, new_orders=55.0)])
        assert not df.loc[0, "supply_chain_stress"]


# ------------------------------------------------------------------ #
#  Expectations gap
# ------------------------------------------------------------------ #

class TestExpectationsGap:
    def test_expectations_gap_exists(self, calc, three_months):
        assert "expectations_gap" in calc.calculate(three_months).columns

    def test_expectations_gap_value(self, calc):
        df = calc.calculate([full(production=50.0, production_expectations=55.0)])
        assert abs(df.loc[0, "expectations_gap"] - 5.0) < 0.01

    def test_expectations_gap_trend_increase(self, calc):
        df = calc.calculate([full(production=50.0, production_expectations=55.0)])
        assert df.loc[0, "expectations_gap_trend"] == "افزایش انتظار"

    def test_expectations_gap_trend_decrease(self, calc):
        df = calc.calculate([full(production=55.0, production_expectations=50.0)])
        assert df.loc[0, "expectations_gap_trend"] == "کاهش انتظار"

    def test_predicted_production_increase(self, calc):
        df = calc.calculate([full(production=50.0, production_expectations=55.0)])
        assert "افزایش" in df.loc[0, "predicted_production_trend"]

    def test_predicted_production_decrease(self, calc):
        df = calc.calculate([full(production=55.0, production_expectations=50.0)])
        assert "کاهش" in df.loc[0, "predicted_production_trend"]


# ------------------------------------------------------------------ #
#  Edge cases
# ------------------------------------------------------------------ #

class TestCalculatorEdgeCases:
    def test_pct_change_first_row_is_nan(self, calc):
        df = calc.calculate([full("1402-01"), full("1402-02")])
        assert pd.isna(df.loc[0, "production_change_pct"])

    def test_pct_change_second_row_correct(self, calc):
        df = calc.calculate([
            full("1402-01", production=50.0),
            full("1402-02", production=55.0),
        ])
        assert abs(df.loc[1, "production_change_pct"] - 10.0) < 0.01

    def test_minimal_record_no_crash(self, calc):
        df = calc.calculate([ShamkhMetrics(month="1402-01", production=50.0)])
        assert len(df) == 1
