"""SQL export upsert behaviour."""

from __future__ import annotations

from pathlib import Path

from pmi_analyzer.data.exporter import export_to_sql
from pmi_analyzer.types import ShamkhMetrics


def test_sql_export_uses_on_conflict_upsert(tmp_path: Path) -> None:
    metrics = [
        ShamkhMetrics(month="1404-10", pmi_total=46.0, production=48.0),
        ShamkhMetrics(month="1404-11", pmi_total=47.0, production=49.0),
    ]
    out = tmp_path / "pmi.sql"
    export_to_sql(metrics, out)
    text = out.read_text(encoding="utf-8")
    assert "ON CONFLICT (month) DO UPDATE" in text
    assert text.count("ON CONFLICT (month) DO UPDATE") == 2
    assert "CREATE TABLE IF NOT EXISTS" in text
