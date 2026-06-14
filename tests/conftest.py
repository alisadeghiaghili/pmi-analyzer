"""Shared pytest fixtures."""

import csv
import pytest
from pathlib import Path
from pmi_analyzer.types import ShamkhMetrics

# ------------------------------------------------------------------ #
#  Factories
# ------------------------------------------------------------------ #


def make_full_metrics(month: str = "1402-01") -> ShamkhMetrics:
    """Return a fully-populated ShamkhMetrics."""
    return ShamkhMetrics(
        month=month,
        production=52.0,
        new_orders=48.0,
        sales=50.0,
        raw_materials_inv=47.0,
        final_goods_inv=45.0,
        input_price=75.0,
        production_expectations=55.0,
        employment=49.0,
        exports=44.0,
        delivery_speed=46.0,
        business_activity=51.0,
    )


def make_partial_metrics(month: str = "1402-01", **kwargs) -> ShamkhMetrics:
    """Return a partially-populated ShamkhMetrics."""
    return ShamkhMetrics(month=month, **kwargs)


# ------------------------------------------------------------------ #
#  Pytest fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def full_metrics():
    return make_full_metrics()


@pytest.fixture
def multi_month_metrics():
    """3 months of realistic data."""
    return [
        ShamkhMetrics(
            month="1402-01",
            production=52.0,
            new_orders=50.0,
            sales=51.0,
            raw_materials_inv=48.0,
            final_goods_inv=46.0,
            input_price=72.0,
            production_expectations=54.0,
            employment=50.0,
            exports=45.0,
            delivery_speed=47.0,
            business_activity=52.0,
        ),
        ShamkhMetrics(
            month="1402-02",
            production=48.0,
            new_orders=45.0,
            sales=47.0,
            raw_materials_inv=44.0,
            final_goods_inv=43.0,
            input_price=78.0,
            production_expectations=46.0,
            employment=47.0,
            exports=42.0,
            delivery_speed=44.0,
            business_activity=48.0,
        ),
        ShamkhMetrics(
            month="1402-03",
            production=44.0,
            new_orders=40.0,
            sales=42.0,
            raw_materials_inv=40.0,
            final_goods_inv=41.0,
            input_price=82.0,
            production_expectations=43.0,
            employment=44.0,
            exports=39.0,
            delivery_speed=41.0,
            business_activity=44.0,
        ),
    ]


@pytest.fixture
def recession_metrics():
    """Metrics clearly in deep recession (all values << 50)."""
    return ShamkhMetrics(
        month="1402-04",
        production=30.0,
        new_orders=28.0,
        sales=29.0,
        raw_materials_inv=35.0,
        final_goods_inv=33.0,
        input_price=85.0,
        production_expectations=32.0,
        employment=35.0,
        exports=25.0,
        delivery_speed=30.0,
        business_activity=31.0,
    )


@pytest.fixture
def boom_metrics():
    """Metrics clearly in boom (all values >> 50)."""
    return ShamkhMetrics(
        month="1402-05",
        production=68.0,
        new_orders=65.0,
        sales=66.0,
        raw_materials_inv=60.0,
        final_goods_inv=58.0,
        input_price=55.0,
        production_expectations=70.0,
        employment=63.0,
        exports=62.0,
        delivery_speed=61.0,
        business_activity=67.0,
    )


@pytest.fixture
def seed_csv(tmp_path) -> Path:
    """Write a minimal shamkh_historical.csv and return its path."""
    path = tmp_path / "shamkh_historical.csv"
    fieldnames = [
        "month",
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
        "pmi_total",
    ]
    rows = [
        dict(
            month="1402-01",
            production=52.0,
            new_orders=50.0,
            sales=51.0,
            raw_materials_inv=48.0,
            final_goods_inv=46.0,
            input_price=72.0,
            production_expectations=54.0,
            employment=50.0,
            exports=45.0,
            delivery_speed=47.0,
            business_activity=52.0,
            pmi_total=51.0,
        ),
        dict(
            month="1402-02",
            production=48.0,
            new_orders=45.0,
            sales=47.0,
            raw_materials_inv=44.0,
            final_goods_inv=43.0,
            input_price=78.0,
            production_expectations=46.0,
            employment=47.0,
            exports=42.0,
            delivery_speed=44.0,
            business_activity=48.0,
            pmi_total=46.7,
        ),
    ]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path
