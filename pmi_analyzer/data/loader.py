"""Load historical Shamkh data from CSV files.

This module provides functions to load and append PMI (Shamkh) data
from CSV files. The CSV format uses UTF-8 with BOM encoding for
Excel compatibility.

Typical usage::

    from pmi_analyzer.data.loader import load_historical, append_record
    from pmi_analyzer.types import ShamkhMetrics

    # Load existing data
    metrics = load_historical(Path("data/shamkh_historical.csv"))

    # Append a new record
    new = ShamkhMetrics(month="1405-03", pmi_total=45.9)
    append_record(new, Path("data/shamkh_historical.csv"))
"""

import csv
from pathlib import Path
from typing import List, Optional, Tuple

from pmi_analyzer.calendar import is_canonical_month, month_sort_key
from pmi_analyzer.types import ShamkhMetrics

DEFAULT_CSV: Path = Path(__file__).parent.parent.parent / "data" / "shamkh_historical.csv"


def load_historical(path: Path = DEFAULT_CSV) -> List[ShamkhMetrics]:
    """Load all historical Shamkh records from a CSV file.

    Reads the CSV file and returns a list of ShamkhMetrics objects,
    sorted chronologically by month.

    Args:
        path: Path to the historical CSV file. Defaults to
            data/shamkh_historical.csv.

    Returns:
        List of ShamkhMetrics sorted by month ascending.

    Raises:
        FileNotFoundError: If the CSV file does not exist.

    Example:
        >>> from pathlib import Path
        >>> from pmi_analyzer.data.loader import load_historical
        >>> metrics = load_historical(Path("data/shamkh_historical.csv"))
        >>> len(metrics) > 0
        True
        >>> metrics[0].month < metrics[-1].month
        True
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

    metrics.sort(key=lambda m: month_sort_key(m.month))
    return metrics


def rewrite_historical(path: Path = DEFAULT_CSV) -> Tuple[int, int]:
    """Rewrite the historical CSV keeping only canonical month rows.

    Contaminated rows from the pre-1.1 parser (Persian month keys, identical
    sub-indicator spam) are dropped so downstream trend math stays valid.

    Args:
        path: Path to the historical CSV file.

    Returns:
        ``(kept, dropped)`` row counts.

    Example:
        >>> from pathlib import Path
        >>> kept, dropped = rewrite_historical(Path("data/shamkh_historical.csv"))
        >>> kept >= 0 and dropped >= 0
        True
    """
    if not path.exists():
        return (0, 0)

    rows: List[dict] = []
    kept = 0
    dropped = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            month = (row.get("month") or "").strip()
            if is_canonical_month(month):
                rows.append(row)
                kept += 1
            else:
                dropped += 1

    rows.sort(key=lambda r: month_sort_key((r.get("month") or "").strip()))
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return (kept, dropped)


def append_record(record: ShamkhMetrics, path: Path = DEFAULT_CSV) -> None:
    """Append a new monthly record to the historical CSV.

    If a record for the same month already exists, it is skipped.
    If the CSV file doesn't exist, it is created with headers.

    Args:
        record: New ShamkhMetrics object to append. ``month`` must be canonical.
        path: Path to the historical CSV file. Defaults to
            data/shamkh_historical.csv.

    Raises:
        ValueError: If ``record.month`` is not a canonical ``YYYY-MM`` id.

    Example:
        >>> from pathlib import Path
        >>> from pmi_analyzer.types import ShamkhMetrics
        >>> from pmi_analyzer.data.loader import append_record
        >>> new = ShamkhMetrics(month="1405-03", pmi_total=45.9)
        >>> append_record(new, Path("data/shamkh_historical.csv"))
    """
    if not is_canonical_month(record.month):
        raise ValueError(
            f"month must be canonical YYYY-MM, got {record.month!r}. "
            "Use pmi_analyzer.calendar.normalize_month_id() first."
        )

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
    """Convert a CSV row dictionary to a ShamkhMetrics object.

    Args:
        row: Dictionary with CSV column names as keys.

    Returns:
        ShamkhMetrics object with values from the CSV row.
    """

    def _float(val: object) -> Optional[float]:
        """Convert a CSV cell to float, returning None for empty/invalid values.

        Args:
            val: Raw cell value (str, None, or other).

        Returns:
            Parsed float, or None when the cell is missing or non-numeric.
        """
        if val is None:
            return None
        text = str(val).strip()
        if not text:
            return None
        try:
            return float(text)
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
