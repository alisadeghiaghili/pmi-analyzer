"""Integration tests: full ShamkhMetrics -> MetricsCalculator pipeline."""

import pytest
import pandas as pd
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.metrics.calculator import MetricsCalculator


def make_declining_series(n: int = 6) -> list:
    """Generate n months of steadily declining PMI."""
    return [
        ShamkhMetrics(
            month=f"1402-{i:02d}",
            production=50.0 - i,
            new_orders=49.0 - i,
            sales=48.0 - i,
            raw_materials_inv=47.0 - i,
            final_goods_inv=46.0 - i,
            input_price=70.0 + i,
            production_expectations=50.0 - i,
            employment=49.0 - i,
            exports=45.0 - i,
            delivery_speed=46.0 - i,
            business_activity=47.0 - i,
        )
        for i in range(1, n + 1)
    ]


@pytest.fixture
def df():
    return MetricsCalculator().calculate(make_declining_series(6))


class TestFullPipeline:
    def test_output_has_expected_rows(self, df):
        assert len(df) == 6

    def test_shamkh_total_declines_over_time(self, df):
        totals = df["shamkh_total"].tolist()
        assert all(totals[i] > totals[i + 1] for i in range(len(totals) - 1))

    def test_recession_severity_increases_over_time(self, df):
        severities = df["recession_severity"].tolist()
        assert all(severities[i] < severities[i + 1] for i in range(len(severities) - 1))

    def test_rolling_mean_available_from_row_3(self, df):
        assert pd.notna(df.loc[2, "production_rolling_mean_3"])
        assert pd.isna(df.loc[0, "production_rolling_mean_3"])

    def test_price_inflation_signal_positive_throughout(self, df):
        assert all(df["price_inflation_signal"] > 0)

    def test_labor_stress_increases_as_employment_drops(self, df):
        stresses = df["labor_stress"].tolist()
        assert all(stresses[i] < stresses[i + 1] for i in range(len(stresses) - 1))

    def test_all_trend_columns_present(self, df):
        for ind in MetricsCalculator.SUB_INDICATORS:
            assert f"{ind}_trend" in df.columns

    def test_all_change_pct_columns_present(self, df):
        for ind in MetricsCalculator.SUB_INDICATORS:
            assert f"{ind}_change_pct" in df.columns


class TestEdgeCases:
    def test_single_month_rolling_and_pct_both_nan(self):
        m = ShamkhMetrics(
            month="1402-01",
            production=48.0,
            new_orders=46.0,
            sales=47.0,
            raw_materials_inv=44.0,
            final_goods_inv=43.0,
            input_price=72.0,
            production_expectations=50.0,
            employment=47.0,
            exports=42.0,
            delivery_speed=44.0,
            business_activity=46.0,
        )
        df = MetricsCalculator().calculate([m])
        assert pd.isna(df.loc[0, "production_rolling_mean_3"])
        assert pd.isna(df.loc[0, "production_change_pct"])

    def test_duplicate_months_does_not_crash(self):
        m1 = ShamkhMetrics(month="1402-01", production=50.0, new_orders=48.0, sales=49.0)
        m2 = ShamkhMetrics(month="1402-01", production=55.0, new_orders=53.0, sales=54.0)
        df = MetricsCalculator().calculate([m1, m2])
        assert isinstance(df, pd.DataFrame)
