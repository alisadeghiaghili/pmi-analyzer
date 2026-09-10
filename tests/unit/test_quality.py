"""Tests for Shamkh plausibility quality gates."""

from __future__ import annotations

from pmi_analyzer.quality import (
    is_plausible_headline,
    is_plausible_indicator,
    scrub_implausible,
)
from pmi_analyzer.types import ShamkhMetrics


class TestPlausibility:
    def test_headline_bounds(self):
        assert is_plausible_headline(None) is True
        assert is_plausible_headline(45.9) is True
        assert is_plausible_headline(20.0) is True
        assert is_plausible_headline(85.0) is True
        assert is_plausible_headline(1.0) is False
        assert is_plausible_headline(150.0) is False

    def test_indicator_bounds(self):
        assert is_plausible_indicator(78.2) is True
        assert is_plausible_indicator(14.0) is False
        assert is_plausible_indicator(6.0) is False

    def test_scrub_nulls_artifacts_only(self):
        m = ShamkhMetrics(
            month="1404-11",
            pmi_total=1.0,
            production=48.2,
            input_price=6.0,
            sales=70.7,
        )
        clean = scrub_implausible(m)
        assert clean.month == "1404-11"
        assert clean.pmi_total is None
        assert clean.production == 48.2
        assert clean.input_price is None
        assert clean.sales == 70.7
