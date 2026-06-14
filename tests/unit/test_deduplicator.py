"""Unit tests for Deduplicator."""

from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.scraper.deduplicator import Deduplicator


def make_metric(month: str, production: float = None, new_orders: float = None) -> ShamkhMetrics:
    return ShamkhMetrics(month=month, production=production, new_orders=new_orders)


class TestDeduplicator:
    dedup = Deduplicator()

    def test_deduplicates_same_month(self):
        metrics = [
            make_metric("1402-01", production=50.0),
            make_metric("1402-01", production=50.0, new_orders=48.0),
        ]
        result = self.dedup.run(metrics)
        assert len(result) == 1

    def test_keeps_most_complete_record(self):
        metrics = [
            make_metric("1402-01", production=50.0),
            make_metric("1402-01", production=50.0, new_orders=48.0),
        ]
        result = self.dedup.run(metrics)
        assert result[0].new_orders == 48.0

    def test_sorts_by_month_ascending(self):
        metrics = [
            make_metric("1402-03", production=46.0),
            make_metric("1402-01", production=55.0),
            make_metric("1402-02", production=50.0),
        ]
        result = self.dedup.run(metrics)
        assert [m.month for m in result] == ["1402-01", "1402-02", "1402-03"]

    def test_single_record_per_month_unchanged(self):
        metrics = [
            make_metric("1402-01", production=50.0),
            make_metric("1402-02", production=48.0),
        ]
        result = self.dedup.run(metrics)
        assert len(result) == 2
