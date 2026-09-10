"""Jalali month identity helpers for Shamkh historical records.

Canonical month id format is ``YYYY-MM`` (e.g. ``1404-10``). Scraper labels,
PDF titles, and filenames arrive as Persian text and must be normalised before
they are used as CSV keys or sort keys.
"""

from __future__ import annotations

import re
from typing import Optional

__all__ = [
    "CANONICAL_MONTH_RE",
    "MONTH_NAME_TO_NUM",
    "is_canonical_month",
    "month_sort_key",
    "normalize_month_id",
]

MONTH_NAME_TO_NUM: dict[str, str] = {
    "فروردین": "01",
    "اردیبهشت": "02",
    "خرداد": "03",
    "تیر": "04",
    "مرداد": "05",
    "شهریور": "06",
    "مهر": "07",
    "آبان": "08",
    "آذر": "09",
    "دی": "10",
    "بهمن": "11",
    "اسفند": "12",
}

CANONICAL_MONTH_RE = re.compile(r"^(1[34]\d{2})-(0[1-9]|1[0-2]|\?\?)$")
_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
_LETTER = r"[\u0600-\u06FF]"
_YEAR = r"(1[34]\d{2})"


def is_canonical_month(value: str) -> bool:
    """Return True when *value* is a canonical ``YYYY-MM`` month id.

    Args:
        value: Candidate month identifier.

    Returns:
        True for ids like ``1404-10`` or ``1404-??``.

    Example:
        >>> is_canonical_month("1404-10")
        True
        >>> is_canonical_month("دی")
        False
    """
    return bool(value) and bool(CANONICAL_MONTH_RE.match(value.strip()))


def _month_token_pattern(name: str) -> re.Pattern[str]:
    """Build a word-boundary month-name pattern.

    Args:
        name: Persian Jalali month name.

    Returns:
        Compiled regex that rejects substring hits inside RTL gibberish.
    """
    return re.compile(rf"(?<!{_LETTER}){re.escape(name)}(?!{_LETTER})")


def normalize_month_id(raw: Optional[str], *, default_year: Optional[int] = None) -> Optional[str]:
    """Normalise a free-form month label to ``YYYY-MM``.

    Accepts canonical ids, Persian labels (``دی ۱۴۰۴``), and mixed text.
    Bare month names without a year return None unless *default_year* is set.

    Args:
        raw: Raw label from scraper, filename, or PDF text.
        default_year: Jalali year to attach when the label has a month only.

    Returns:
        Canonical month id, or None when the label cannot be trusted.

    Example:
        >>> normalize_month_id("دی ۱۴۰۴")
        '1404-10'
        >>> normalize_month_id("1404-10")
        '1404-10'
        >>> normalize_month_id("دیدج", default_year=1405) is None
        True
    """
    if raw is None:
        return None
    text = str(raw).strip().translate(_DIGIT_MAP)
    if not text:
        return None
    if is_canonical_month(text):
        return text

    year_m = re.search(_YEAR, text)
    year_in_text = year_m.group(1) if year_m else None

    found_num: Optional[str] = None
    for name, num in MONTH_NAME_TO_NUM.items():
        if _month_token_pattern(name).search(text):
            found_num = num
            break

    if found_num and year_in_text:
        return f"{year_in_text}-{found_num}"
    if found_num and default_year:
        return f"{default_year}-{found_num}"
    if year_in_text and not found_num:
        return f"{year_in_text}-??"
    return None


def month_sort_key(month_id: str) -> tuple[int, int]:
    """Return a chronological sort key for a month id.

    Args:
        month_id: Canonical or near-canonical month id.

    Returns:
        ``(year, month_number)``; unknown month numbers sort last within year.

    Example:
        >>> month_sort_key("1404-10") < month_sort_key("1404-11")
        True
    """
    m = CANONICAL_MONTH_RE.match((month_id or "").strip())
    if not m:
        return (0, 99)
    year = int(m.group(1))
    mon = m.group(2)
    return (year, 99 if mon == "??" else int(mon))
