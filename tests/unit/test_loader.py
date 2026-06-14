"""Unit tests for data loader."""

import csv
import pytest
from pathlib import Path

from pmi_analyzer.data.loader import load_historical, append_record
from pmi_analyzer.types import ShamkhMetrics


def write_csv(path: Path, rows: list) -> None:
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
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestLoadHistorical:
    def test_loads_records(self, tmp_path):
        csv_path = tmp_path / "shamkh.csv"
        write_csv(
            csv_path,
            [
                {
                    "month": "1402-01",
                    "production": "50.0",
                    "new_orders": "48.0",
                    "sales": "",
                    "raw_materials_inv": "",
                    "final_goods_inv": "",
                    "input_price": "",
                    "production_expectations": "",
                    "employment": "",
                    "exports": "",
                    "delivery_speed": "",
                    "business_activity": "",
                    "pmi_total": "49.0",
                },
            ],
        )
        metrics = load_historical(csv_path)
        assert len(metrics) == 1
        assert metrics[0].month == "1402-01"
        assert metrics[0].production == 50.0
        assert metrics[0].pmi_total == 49.0

    def test_sorts_by_month_ascending(self, tmp_path):
        csv_path = tmp_path / "shamkh.csv"
        write_csv(
            csv_path,
            [
                {
                    "month": "1402-03",
                    "production": "46.0",
                    "new_orders": "",
                    "sales": "",
                    "raw_materials_inv": "",
                    "final_goods_inv": "",
                    "input_price": "",
                    "production_expectations": "",
                    "employment": "",
                    "exports": "",
                    "delivery_speed": "",
                    "business_activity": "",
                    "pmi_total": "",
                },
                {
                    "month": "1402-01",
                    "production": "55.0",
                    "new_orders": "",
                    "sales": "",
                    "raw_materials_inv": "",
                    "final_goods_inv": "",
                    "input_price": "",
                    "production_expectations": "",
                    "employment": "",
                    "exports": "",
                    "delivery_speed": "",
                    "business_activity": "",
                    "pmi_total": "",
                },
            ],
        )
        metrics = load_historical(csv_path)
        assert metrics[0].month == "1402-01"
        assert metrics[1].month == "1402-03"

    def test_raises_if_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_historical(tmp_path / "nonexistent.csv")

    def test_handles_empty_floats(self, tmp_path):
        csv_path = tmp_path / "shamkh.csv"
        write_csv(
            csv_path,
            [
                {
                    "month": "1402-01",
                    "production": "",
                    "new_orders": "",
                    "sales": "",
                    "raw_materials_inv": "",
                    "final_goods_inv": "",
                    "input_price": "",
                    "production_expectations": "",
                    "employment": "",
                    "exports": "",
                    "delivery_speed": "",
                    "business_activity": "",
                    "pmi_total": "49.0",
                },
            ],
        )
        metrics = load_historical(csv_path)
        assert metrics[0].production is None
        assert metrics[0].pmi_total == 49.0


class TestAppendRecord:
    def test_appends_new_month(self, tmp_path):
        csv_path = tmp_path / "shamkh.csv"
        write_csv(
            csv_path,
            [
                {
                    "month": "1402-01",
                    "production": "50.0",
                    "new_orders": "",
                    "sales": "",
                    "raw_materials_inv": "",
                    "final_goods_inv": "",
                    "input_price": "",
                    "production_expectations": "",
                    "employment": "",
                    "exports": "",
                    "delivery_speed": "",
                    "business_activity": "",
                    "pmi_total": "49.0",
                },
            ],
        )
        new_record = ShamkhMetrics(month="1402-02", pmi_total=47.0)
        append_record(new_record, csv_path)
        metrics = load_historical(csv_path)
        assert len(metrics) == 2
        assert any(m.month == "1402-02" for m in metrics)

    def test_skips_duplicate_month(self, tmp_path):
        csv_path = tmp_path / "shamkh.csv"
        write_csv(
            csv_path,
            [
                {
                    "month": "1402-01",
                    "production": "50.0",
                    "new_orders": "",
                    "sales": "",
                    "raw_materials_inv": "",
                    "final_goods_inv": "",
                    "input_price": "",
                    "production_expectations": "",
                    "employment": "",
                    "exports": "",
                    "delivery_speed": "",
                    "business_activity": "",
                    "pmi_total": "49.0",
                },
            ],
        )
        duplicate = ShamkhMetrics(month="1402-01", pmi_total=99.0)
        append_record(duplicate, csv_path)
        metrics = load_historical(csv_path)
        assert len(metrics) == 1
        assert metrics[0].pmi_total == 49.0  # original unchanged
