"""Metric calculator for Shamkh sub-indicators.

This module provides the MetricsCalculator class for computing derived
indicators, trends, and composite metrics from raw PMI (Shamkh) data.

Typical usage::

    from pmi_analyzer.parser.pdf_parser import PDFParser
    from pmi_analyzer.metrics.calculator import MetricsCalculator

    parser = PDFParser()
    results = parser.parse(Path("data/pdfs/report.pdf"))

    calculator = MetricsCalculator()
    df = calculator.calculate(results)
    print(df.columns.tolist())
"""

from typing import List

import pandas as pd

from pmi_analyzer.types import ShamkhMetrics


class MetricsCalculator:
    """Calculator for Shamkh metrics and derived indicators.

    This class takes raw ShamkhMetrics data and computes:
    - Month-over-month percentage changes
    - Trend classifications (expansion/contraction)
    - 3-month rolling means
    - Composite indicators (demand pressure, labor stress, etc.)

    Attributes:
        SUB_INDICATORS: List of column names for the 11 PMI sub-indicators.

    Example:
        >>> from pmi_analyzer.metrics.calculator import MetricsCalculator
        >>> from pmi_analyzer.types import ShamkhMetrics
        >>> m = ShamkhMetrics(month="1405-03", pmi_total=45.9, production=48.2)
        >>> calc = MetricsCalculator()
        >>> df = calc.calculate([m])
        >>> "production_trend" in df.columns
        True
    """

    SUB_INDICATORS: List[str] = [
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

    def calculate(self, metrics: List[ShamkhMetrics]) -> pd.DataFrame:
        """Calculate all metrics and derived indicators.

        Processes raw PMI data and adds calculated columns including:
        - `{indicator}_change_pct`: Month-over-month percentage change
        - `{indicator}_trend`: Trend classification (رونق/رکود/خنثی)
        - `{indicator}_rolling_mean_3`: 3-month rolling average
        - Composite indicators (demand pressure, labor stress, etc.)

        Args:
            metrics: List of ShamkhMetrics objects to process.

        Returns:
            DataFrame with original data plus calculated columns.

        Raises:
            ValueError: If metrics list is empty.

        Example:
            >>> from pmi_analyzer.metrics.calculator import MetricsCalculator
            >>> from pmi_analyzer.types import ShamkhMetrics
            >>> m1 = ShamkhMetrics(month="1405-01", production=48.0)
            >>> m2 = ShamkhMetrics(month="1405-02", production=49.0)
            >>> calc = MetricsCalculator()
            >>> df = calc.calculate([m1, m2])
            >>> df["production_trend"].iloc[1]
            'رونق'
        """
        if not metrics:
            raise ValueError("No metrics provided")

        rows = []
        for m in metrics:
            rows.append(
                {
                    "month": m.month,
                    "production": m.production,
                    "new_orders": m.new_orders,
                    "sales": m.sales,
                    "raw_materials_inv": m.raw_materials_inv,
                    "final_goods_inv": m.final_goods_inv,
                    "input_price": m.input_price,
                    "production_expectations": m.production_expectations,
                    "employment": m.employment,
                    "exports": m.exports,
                    "delivery_speed": m.delivery_speed,
                    "business_activity": m.business_activity,
                }
            )

        df = pd.DataFrame(rows).sort_values("month").reset_index(drop=True)

        for col in self.SUB_INDICATORS:
            if col in df.columns and df[col].notna().any():
                df = self._calculate_indicator_metrics(df, col)

        key_cols = ["production", "new_orders", "sales"]
        if all(col in df.columns and df[col].notna().any() for col in key_cols):
            df["shamkh_total"] = df[key_cols].mean(axis=1)

        df = self._calculate_composite_indicators(df)
        df = self._calculate_expectations_metrics(df)

        return df

    def _calculate_indicator_metrics(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Calculate metrics for a single indicator.

        Adds percentage change, trend classification, and rolling mean
        columns for the specified indicator.

        Args:
            df: DataFrame containing the indicator column.
            col: Name of the indicator column to calculate metrics for.

        Returns:
            DataFrame with new calculated columns added.
        """
        df[f"{col}_change_pct"] = df[col].pct_change() * 100
        df[f"{col}_trend"] = df[col].apply(
            lambda x: (
                "رونق" if pd.notna(x) and x > 50 else ("رکود" if pd.notna(x) and x < 50 else "خنثی")
            )
        )
        df[f"{col}_rolling_mean_3"] = df[col].rolling(3).mean()
        return df

    def _calculate_expectations_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate production expectations vs actual production gap.

        Computes the gap between expected and actual production, which
        indicates whether businesses are optimistic or pessimistic.

        Args:
            df: DataFrame with production and production_expectations columns.

        Returns:
            DataFrame with expectations gap columns added.
        """
        if "production_expectations" not in df.columns or "production" not in df.columns:
            return df
        if not (df["production_expectations"].notna().any() and df["production"].notna().any()):
            return df

        df["expectations_gap"] = df["production_expectations"] - df["production"]
        df["expectations_gap_trend"] = df["expectations_gap"].apply(
            lambda x: (
                "افزایش انتظار"
                if pd.notna(x) and x > 0
                else ("کاهش انتظار" if pd.notna(x) and x < 0 else "ثبات")
            )
        )
        df["expectations_gap_rolling_mean"] = df["expectations_gap"].rolling(3).mean()
        df["predicted_production_trend"] = df["expectations_gap"].apply(
            lambda x: (
                "احتمال افزایش تولید"
                if pd.notna(x) and x > 2
                else ("احتمال کاهش تولید" if pd.notna(x) and x < -2 else "احتمال ثبات تولید")
            )
        )
        return df

    def _calculate_composite_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate composite and advanced indicators.

        Computes derived indicators that combine multiple raw sub-indicators:

        - **Demand Pressure**: Average of new_orders, sales, exports
        - **Production Capacity**: Average of production, inventories
        - **Labor Market Stress**: Inverse of employment (100 - employment)
        - **Price Inflation Signal**: input_price - 50
        - **Recession Severity**: 50 - shamkh_total
        - **Supply Chain Stress**: Low inventory + low orders

        Args:
            df: DataFrame with raw PMI sub-indicator columns.

        Returns:
            DataFrame with composite indicator columns added.
        """
        # 1. Demand Pressure Index
        demand_cols = ["new_orders", "sales", "exports"]
        if all(c in df.columns and df[c].notna().any() for c in demand_cols):
            df["demand_pressure"] = df[demand_cols].mean(axis=1)
            df["demand_pressure_trend"] = df["demand_pressure"].apply(
                lambda x: (
                    "تقاضای قوی"
                    if pd.notna(x) and x > 50
                    else ("تقاضای ضعیف" if pd.notna(x) and x < 40 else "تقاضای متوسط")
                )
            )

        # 2. Production Capacity Index
        capacity_cols = ["production", "raw_materials_inv", "final_goods_inv"]
        if all(c in df.columns and df[c].notna().any() for c in capacity_cols):
            df["production_capacity"] = df[capacity_cols].mean(axis=1)

        # 3. Labor Market Stress
        if "employment" in df.columns and df["employment"].notna().any():
            df["labor_stress"] = 100 - df["employment"]
            df["labor_stress_trend"] = df["labor_stress"].apply(
                lambda x: (
                    "استرس شدید"
                    if pd.notna(x) and x > 60
                    else ("استرس متوسط" if pd.notna(x) and x > 50 else "استرس کم")
                )
            )

        # 4. Price Inflation Signal
        if "input_price" in df.columns and df["input_price"].notna().any():
            df["price_inflation_signal"] = df["input_price"] - 50
            df["price_trend"] = df["price_inflation_signal"].apply(
                lambda x: (
                    "تورم قیمت"
                    if pd.notna(x) and x > 10
                    else ("کاهش قیمت" if pd.notna(x) and x < -10 else "ثبات قیمت")
                )
            )

        # 5. Recession Severity Index
        if "shamkh_total" in df.columns and df["shamkh_total"].notna().any():
            df["recession_severity"] = 50 - df["shamkh_total"]
            df["recession_classification"] = df["recession_severity"].apply(
                lambda x: (
                    "رکود عمیق و فراگیر"
                    if pd.notna(x) and x > 15
                    else (
                        "رکود متوسط"
                        if pd.notna(x) and x > 10
                        else ("رکود خفیف" if pd.notna(x) and x > 5 else "رونق یا خنثی")
                    )
                )
            )

        # 6. Supply Chain Stress
        if "raw_materials_inv" in df.columns and "new_orders" in df.columns:
            df["supply_chain_stress"] = (df["raw_materials_inv"] < 45) & (df["new_orders"] < 40)

        return df
