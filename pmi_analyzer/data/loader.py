"""Load historical Shamkh data from the seed CSV."""

import csv
from pathlib import Path
from typing import List, Optional

from pmi_analyzer.types import ShamkhMetrics

DEFAULT_CSV = Path(__file__).parent.parent.parent / "data" / "shamkh_historical.csv"


def load_historical(path: Path = DEFAULT_CSV) -> List[ShamkhMetrics]:
    """Load all historical Shamkh records from the seed CSV.

    Args:
        path: Path to shamkh_historical.csv

    Returns:
        List of ShamkhMetrics sorted by month ascending.

    Raises:
        FileNotFoundError: If CSV does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Historical data not found: {path}\n"
            "Run: python scripts/phase2_download_and_parse.py"
        )

    metrics: List[ShamkhMetrics] = []

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(_row_to_metrics(row))

    metrics.sort(key=lambda m: m.month)
    return metrics


def append_record(record: ShamkhMetrics, path: Path = DEFAULT_CSV) -> None:
    """Append a new monthly record to the historical CSV.

    Skips if a record for the same month already exists.

    Args:
        record: New ShamkhMetrics to append.
        path: Path to shamkh_historical.csv
    """
    existing = load_historical(path) if path.exists() else []
    existing_months = {m.month for m in existing}

    if record.month in existing_months:
        return  # already exists, skip

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

    write_header = not path.exists()
    with open(path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow({k: getattr(record, k, "") or "" for k in fieldnames})


def _row_to_metrics(row: dict) -> ShamkhMetrics:
    """Convert a CSV row dict to ShamkhMetrics."""

    def _float(val: str) -> Optional[float]:
        val = val.strip()
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    return ShamkhMetrics(
        month=row["month"].strip(),
        production=_float(row.get("production", "")),
        new_orders=_float(row.get("new_orders", "")),
        sales=_float(row.get("sales", "")),
        raw_materials_inv=_float(row.get("raw_materials_inv", "")),
        final_goods_inv=_float(row.get("final_goods_inv", "")),
        input_price=_float(row.get("input_price", "")),
        production_expectations=_float(row.get("production_expectations", "")),
        employment=_float(row.get("employment", "")),
        exports=_float(row.get("exports", "")),
        delivery_speed=_float(row.get("delivery_speed", "")),
        business_activity=_float(row.get("business_activity", "")),
        pmi_total=_float(row.get("pmi_total", "")),
    )
