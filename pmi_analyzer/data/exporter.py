"""Export Shamkh data to various formats (CSV, SQL, JSON, Excel).

This module provides functions to export parsed PMI (Shamkh) data to multiple
formats suitable for database import, web APIs, and manual analysis.

Typical usage::

    from pmi_analyzer.parser.pdf_parser import PDFParser
    from pmi_analyzer.data.exporter import export_to_csv, export_to_sql

    parser = PDFParser()
    results = parser.parse(Path("data/pdfs/report.pdf"))

    export_to_csv(results, Path("output/data.csv"))
    export_to_sql(results, Path("output/data.sql"))
"""

import csv
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd

from pmi_analyzer.types import ShamkhMetrics

# Column definitions for consistent schema across formats
COLUMNS: List[str] = [
    "month",
    "pmi_total",
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


def metrics_to_dataframe(metrics: List[ShamkhMetrics]) -> pd.DataFrame:
    """Convert a list of ShamkhMetrics to a unified DataFrame.

    Creates a pandas DataFrame with all PMI indicators as columns, ready for
    export to CSV, SQL, JSON, or Excel. None values are preserved as NaN.

    Args:
        metrics: List of parsed ShamkhMetrics objects. Each object contains
            month identifier and optional indicator values (0-100 scale).

    Returns:
        A pandas DataFrame with columns matching the COLUMNS constant.
        Empty DataFrame if metrics list is empty.

    Example:
        >>> from pmi_analyzer.types import ShamkhMetrics
        >>> from pmi_analyzer.data.exporter import metrics_to_dataframe
        >>> m = ShamkhMetrics(month="1405-03", pmi_total=45.9, production=48.2)
        >>> df = metrics_to_dataframe([m])
        >>> df.columns.tolist()[:3]
        ['month', 'pmi_total', 'production']
        >>> df.iloc[0]["pmi_total"]
        45.9
    """
    rows = []
    for m in metrics:
        rows.append(
            {
                "month": m.month,
                "pmi_total": m.pmi_total,
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
    return pd.DataFrame(rows)


def export_to_csv(
    metrics: List[ShamkhMetrics],
    output_path: Path,
    include_calculated: bool = False,
) -> Path:
    """Export ShamkhMetrics list to a unified CSV file.

    Generates a CSV file with UTF-8 BOM encoding for Excel compatibility.
    The file contains one row per month with all indicator values.

    Args:
        metrics: List of parsed ShamkhMetrics objects to export.
        output_path: Path for the output CSV file. Parent directories
            are created automatically if they don't exist.
        include_calculated: If True, includes calculated metrics (trends,
            composites, rolling means) in the export. Defaults to False.

    Returns:
        Path to the created CSV file.

    Raises:
        OSError: If the output directory cannot be created.

    Example:
        >>> from pathlib import Path
        >>> from pmi_analyzer.parser.pdf_parser import PDFParser
        >>> from pmi_analyzer.data.exporter import export_to_csv
        >>> parser = PDFParser()
        >>> results = parser.parse(Path("data/pdfs/report.pdf"))
        >>> export_to_csv(results, Path("output/pmi_data.csv"))
        PosixPath('output/pmi_data.csv')
    """
    df = metrics_to_dataframe(metrics)

    if include_calculated:
        from pmi_analyzer.metrics.calculator import MetricsCalculator

        calc = MetricsCalculator()
        df = calc.calculate(metrics)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to CSV with UTF-8 BOM for Excel compatibility
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return output_path


def export_to_sql(
    metrics: List[ShamkhMetrics],
    output_path: Path,
    table_name: str = "shamkh_metrics",
    include_calculated: bool = False,
) -> Path:
    """Export ShamkhMetrics list to a SQL file with CREATE TABLE and INSERT statements.

    Generates a complete SQL script that can be executed directly on most
    relational databases (PostgreSQL, MySQL, SQLite). Includes table creation
    and data insertion.

    Args:
        metrics: List of parsed ShamkhMetrics objects to export.
        output_path: Path for the output SQL file. Parent directories
            are created automatically if they don't exist.
        table_name: Name of the database table. Defaults to "shamkh_metrics".
        include_calculated: If True, includes calculated metrics (trends,
            composites, rolling means) in the export. Defaults to False.

    Returns:
        Path to the created SQL file.

    Raises:
        OSError: If the output directory cannot be created.

    Example:
        >>> from pathlib import Path
        >>> from pmi_analyzer.parser.pdf_parser import PDFParser
        >>> from pmi_analyzer.data.exporter import export_to_sql
        >>> parser = PDFParser()
        >>> results = parser.parse(Path("data/pdfs/report.pdf"))
        >>> export_to_sql(results, Path("output/pmi_data.sql"), table_name="pmi")
        PosixPath('output/pmi_data.sql')
    """
    df = metrics_to_dataframe(metrics)

    if include_calculated:
        from pmi_analyzer.metrics.calculator import MetricsCalculator

        calc = MetricsCalculator()
        df = calc.calculate(metrics)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Column definitions for SQL
    sql_columns: dict[str, str] = {
        "month": "VARCHAR(10) PRIMARY KEY",
        "pmi_total": "DECIMAL(5,2)",
        "production": "DECIMAL(5,2)",
        "new_orders": "DECIMAL(5,2)",
        "sales": "DECIMAL(5,2)",
        "raw_materials_inv": "DECIMAL(5,2)",
        "final_goods_inv": "DECIMAL(5,2)",
        "input_price": "DECIMAL(5,2)",
        "production_expectations": "DECIMAL(5,2)",
        "employment": "DECIMAL(5,2)",
        "exports": "DECIMAL(5,2)",
        "delivery_speed": "DECIMAL(5,2)",
        "business_activity": "DECIMAL(5,2)",
    }

    # Add extra columns from calculated DataFrame
    for col in df.columns:
        if col not in sql_columns:
            sql_columns[col] = "TEXT"

    lines: list[str] = []

    # CREATE TABLE statement
    col_defs = [f"    {col} {dtype}" for col, dtype in sql_columns.items() if col in df.columns]
    lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
    lines.append(",\n".join(col_defs))
    lines.append(");\n")

    # INSERT statements
    for _, row in df.iterrows():
        values: list[str] = []
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                values.append("NULL")
            elif isinstance(val, str):
                values.append(f"'{val.replace(chr(39), chr(39)*2)}'")  # escape single quotes
            else:
                values.append(str(val))

        cols = ", ".join(df.columns)
        vals = ", ".join(values)
        lines.append(f"INSERT INTO {table_name} ({cols}) VALUES ({vals});")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    return output_path


def export_to_json(
    metrics: List[ShamkhMetrics],
    output_path: Path,
    include_calculated: bool = False,
    indent: int = 2,
) -> Path:
    """Export ShamkhMetrics list to a JSON file.

    Generates a JSON array where each element represents one month's PMI data.
    None values are converted to JSON null.

    Args:
        metrics: List of parsed ShamkhMetrics objects to export.
        output_path: Path for the output JSON file. Parent directories
            are created automatically if they don't exist.
        include_calculated: If True, includes calculated metrics (trends,
            composites, rolling means) in the export. Defaults to False.
        indent: JSON indentation level. Defaults to 2 spaces.

    Returns:
        Path to the created JSON file.

    Raises:
        OSError: If the output directory cannot be created.

    Example:
        >>> from pathlib import Path
        >>> from pmi_analyzer.parser.pdf_parser import PDFParser
        >>> from pmi_analyzer.data.exporter import export_to_json
        >>> parser = PDFParser()
        >>> results = parser.parse(Path("data/pdfs/report.pdf"))
        >>> export_to_json(results, Path("output/pmi_data.json"))
        PosixPath('output/pmi_data.json')
    """
    df = metrics_to_dataframe(metrics)

    if include_calculated:
        from pmi_analyzer.metrics.calculator import MetricsCalculator

        calc = MetricsCalculator()
        df = calc.calculate(metrics)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert DataFrame to list of dicts, handling NaN values
    records = df.where(df.notna(), None).to_dict(orient="records")

    output_path.write_text(
        json.dumps(records, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


def export_to_excel(
    metrics: List[ShamkhMetrics],
    output_path: Path,
    include_calculated: bool = False,
    sheet_name: str = "PMI Data",
) -> Path:
    """Export ShamkhMetrics list to an Excel file.

    Generates an .xlsx file with a single worksheet containing all PMI data.
    Requires the openpyxl package to be installed.

    Args:
        metrics: List of parsed ShamkhMetrics objects to export.
        output_path: Path for the output Excel file (.xlsx). Parent
            directories are created automatically if they don't exist.
        include_calculated: If True, includes calculated metrics (trends,
            composites, rolling means) in the export. Defaults to False.
        sheet_name: Name of the worksheet. Defaults to "PMI Data".

    Returns:
        Path to the created Excel file.

    Raises:
        OSError: If the output directory cannot be created.
        ImportError: If openpyxl is not installed.

    Example:
        >>> from pathlib import Path
        >>> from pmi_analyzer.parser.pdf_parser import PDFParser
        >>> from pmi_analyzer.data.exporter import export_to_excel
        >>> parser = PDFParser()
        >>> results = parser.parse(Path("data/pdfs/report.pdf"))
        >>> export_to_excel(results, Path("output/pmi_data.xlsx"))
        PosixPath('output/pmi_data.xlsx')
    """
    df = metrics_to_dataframe(metrics)

    if include_calculated:
        from pmi_analyzer.metrics.calculator import MetricsCalculator

        calc = MetricsCalculator()
        df = calc.calculate(metrics)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to Excel
    df.to_excel(output_path, index=False, sheet_name=sheet_name)

    return output_path


def merge_with_historical(
    new_metrics: List[ShamkhMetrics],
    historical_csv: Path,
) -> pd.DataFrame:
    """Merge new parsed data with historical CSV, avoiding duplicates.

    Combines newly parsed PMI data with an existing historical CSV file.
    If a month already exists in the historical data, the new value replaces it.
    The result is sorted chronologically by month.

    Args:
        new_metrics: Newly parsed ShamkhMetrics objects to merge.
        historical_csv: Path to existing historical CSV file. If the file
            doesn't exist, only the new metrics are returned.

    Returns:
        Merged DataFrame sorted by month ascending. Contains all columns
        from the historical CSV plus any new indicator columns.

    Example:
        >>> from pathlib import Path
        >>> from pmi_analyzer.types import ShamkhMetrics
        >>> from pmi_analyzer.data.exporter import merge_with_historical
        >>> new = [ShamkhMetrics(month="1405-03", pmi_total=45.9)]
        >>> df = merge_with_historical(new, Path("data/shamkh_historical.csv"))
        >>> len(df) > 0
        True
    """
    # Load existing data
    if historical_csv.exists():
        existing_df = pd.read_csv(historical_csv, encoding="utf-8-sig")
    else:
        existing_df = pd.DataFrame()

    # Convert new metrics to DataFrame
    new_df = metrics_to_dataframe(new_metrics)

    if existing_df.empty:
        return new_df.sort_values("month").reset_index(drop=True)

    # Merge: append new rows, drop duplicates by month (keep latest)
    merged = pd.concat([existing_df, new_df], ignore_index=True)
    merged = merged.drop_duplicates(subset=["month"], keep="last")
    merged = merged.sort_values("month").reset_index(drop=True)

    return merged
