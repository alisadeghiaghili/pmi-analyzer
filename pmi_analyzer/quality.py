"""Plausibility gates for Shamkh indicator values.

Extraction from live ICCIMA PDFs occasionally yields artefacts (``1.0``,
``14.0``) that are inside the theoretical ``[0, 100]`` range but outside
the range observed for Iran's national Shamkh series. These helpers strip
or reject such values so contaminated rows never enter the historical store.
"""

from __future__ import annotations

from typing import List, Optional

from pmi_analyzer.types import ShamkhMetrics

__all__ = [
    "HEADLINE_RANGE",
    "INDICATOR_RANGE",
    "is_plausible_headline",
    "is_plausible_indicator",
    "scrub_implausible",
]

# National Shamkh headline has stayed well inside this band since 2019.
HEADLINE_RANGE: tuple[float, float] = (20.0, 85.0)

# Sub-indicators can swing wider (esp. input price) but not to single digits.
INDICATOR_RANGE: tuple[float, float] = (15.0, 98.0)

_NUMERIC_FIELDS: tuple[str, ...] = (
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
)


def is_plausible_headline(value: Optional[float]) -> bool:
    """Return True when a headline PMI value looks like real Shamkh data.

    Args:
        value: Candidate ``pmi_total``.

    Returns:
        True if None (unknown) or inside :data:`HEADLINE_RANGE`.

    Example:
        >>> is_plausible_headline(45.9)
        True
        >>> is_plausible_headline(1.0)
        False
    """
    if value is None:
        return True
    lo, hi = HEADLINE_RANGE
    return lo <= value <= hi


def is_plausible_indicator(value: Optional[float], *, field: str = "") -> bool:
    """Return True when a sub-indicator value is extraction-plausible.

    Args:
        value: Candidate indicator value.
        field: Optional field name (reserved for future per-field bands).

    Returns:
        True if None or inside :data:`INDICATOR_RANGE`.
    """
    if value is None:
        return True
    lo, hi = INDICATOR_RANGE
    return lo <= value <= hi


def scrub_implausible(metrics: ShamkhMetrics) -> ShamkhMetrics:
    """Null out implausible indicator values in-place-safe copy.

    Args:
        metrics: Parsed metrics instance.

    Returns:
        New :class:`ShamkhMetrics` with artefact values replaced by None.
        The month key is always preserved.
    """
    data = {
        "month": metrics.month,
        "pmi_total": metrics.pmi_total if is_plausible_headline(metrics.pmi_total) else None,
    }
    for field in _NUMERIC_FIELDS:
        val = getattr(metrics, field)
        data[field] = val if is_plausible_indicator(val, field=field) else None
    return ShamkhMetrics(**data)


def scrub_all(items: List[ShamkhMetrics]) -> List[ShamkhMetrics]:
    """Scrub a list of metrics.

    Args:
        items: Parsed metrics.

    Returns:
        New list with implausible values nulled out.
    """
    return [scrub_implausible(m) for m in items]
