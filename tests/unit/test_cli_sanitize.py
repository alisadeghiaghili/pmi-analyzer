"""Tests for CLI metric sanitisation (dedup + validation)."""

from __future__ import annotations

from pmi_analyzer.cli import _sanitize_metrics
from pmi_analyzer.types import ShamkhMetrics


class TestSanitizeMetrics:
    def test_drops_non_canonical_month(self):
        raw = [ShamkhMetrics(month="دی", pmi_total=40.0)]
        assert _sanitize_metrics(raw) == []

    def test_deduplicates_keeping_most_complete(self):
        sparse = ShamkhMetrics(month="1404-10", pmi_total=46.0)
        full = ShamkhMetrics(
            month="1404-10",
            pmi_total=46.0,
            production=48.0,
            new_orders=44.0,
            sales=45.0,
        )
        clean = _sanitize_metrics([sparse, full])
        assert len(clean) == 1
        assert clean[0].production == 48.0

    def test_drops_out_of_range_values(self):
        bad = ShamkhMetrics(month="1404-10", pmi_total=150.0)
        assert _sanitize_metrics([bad]) == []

    def test_keeps_valid_record(self):
        good = ShamkhMetrics(month="1404-10", pmi_total=48.2)
        clean = _sanitize_metrics([good])
        assert len(clean) == 1
        assert clean[0].month == "1404-10"
