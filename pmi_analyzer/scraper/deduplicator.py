"""Deduplicate and validate a list of ShamkhMetrics after batch parsing."""

import logging
from typing import List

from pmi_analyzer.types import ShamkhMetrics

logger = logging.getLogger(__name__)


class Deduplicator:
    """Remove duplicate months and flag incomplete records.

    Usage::

        dedup = Deduplicator()
        clean = dedup.run(raw_metrics)
    """

    def run(self, metrics: List[ShamkhMetrics]) -> List[ShamkhMetrics]:
        """Deduplicate by month, keep the most complete record per month.

        Args:
            metrics: Raw list (may have duplicates and empty records).

        Returns:
            Clean list sorted by month ascending.
        """
        logger.info(f"[Dedup] Input: {len(metrics)} records")

        # Group by month
        by_month: dict = {}
        for m in metrics:
            if m.month not in by_month:
                by_month[m.month] = []
            by_month[m.month].append(m)

        # Keep the most complete record per month
        clean: List[ShamkhMetrics] = []
        for month, records in sorted(by_month.items()):
            best = max(records, key=self._completeness_score)
            clean.append(best)

        # Log incomplete records
        incomplete = [m for m in clean if not m.is_complete()]
        if incomplete:
            logger.warning(f"[Dedup] {len(incomplete)} months have incomplete data:")
            for m in incomplete:
                missing = self._missing_fields(m)
                logger.warning(f"  {m.month}: missing {missing}")

        logger.info(f"[Dedup] Output: {len(clean)} unique months")
        return clean

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _completeness_score(self, m: ShamkhMetrics) -> int:
        """Count non-None fields (higher = more complete)."""
        fields = [
            "production", "new_orders", "sales", "raw_materials_inv",
            "final_goods_inv", "input_price", "production_expectations",
            "employment", "exports", "delivery_speed", "business_activity",
        ]
        return sum(1 for f in fields if getattr(m, f, None) is not None)

    def _missing_fields(self, m: ShamkhMetrics) -> List[str]:
        """Return list of missing field names."""
        fields = [
            "production", "new_orders", "sales", "raw_materials_inv",
            "final_goods_inv", "input_price", "production_expectations",
            "employment", "exports", "delivery_speed", "business_activity",
        ]
        return [f for f in fields if getattr(m, f, None) is None]
