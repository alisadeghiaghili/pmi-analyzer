"""Integration tests against live ICCIMA Shamkh PDFs.

Skipped when fixture PDFs are not present (CI default). Locally, place
reports under ``_pdf_probe/`` or set ``PMI_REAL_PDF_DIR``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pmi_analyzer.calendar import normalize_month_id
from pmi_analyzer.metrics.validators import validate_metrics
from pmi_analyzer.parser.pdf_parser import PDFParser
from pmi_analyzer.types import ShamkhMetrics

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "_pdf_probe"
PDF_DIR = Path(os.environ.get("PMI_REAL_PDF_DIR", DEFAULT_DIR))

EXPECTED: dict[str, str] = {
    "خرداد.pdf": "1405-03",
    "تیر405.pdf": "1405-04",
    "شامخ-اردیبهشت-1405.pdf": "1405-02",
    "شامخ-بهمن-1404.pdf": "1404-11",
    "شامخ-فروردین-1405.pdf": "1405-01",
}

# Headline PMI verified against the printed summary table on page 4.
KNOWN_HEADLINE: dict[str, float] = {
    "خرداد.pdf": 45.9,
}


def _available() -> list[str]:
    return [n for n in EXPECTED if (PDF_DIR / n).exists()]


pytestmark = pytest.mark.skipif(
    not _available(),
    reason="Real ICCIMA PDFs not present (set PMI_REAL_PDF_DIR or add _pdf_probe/)",
)


@pytest.mark.parametrize("filename", sorted(EXPECTED.keys()))
def test_real_pdf_month_identity(filename: str) -> None:
    path = PDF_DIR / filename
    if not path.exists():
        pytest.skip(f"missing {filename}")
    metrics = PDFParser().parse(path)[0]
    assert metrics.month == EXPECTED[filename]


@pytest.mark.parametrize("filename", sorted(EXPECTED.keys()))
def test_real_pdf_filename_normalises_to_same_month(filename: str) -> None:
    path = PDF_DIR / filename
    if not path.exists():
        pytest.skip(f"missing {filename}")
    from_name = normalize_month_id(path.stem)
    metrics = PDFParser().parse(path)[0]
    if from_name is not None:
        assert from_name == metrics.month


@pytest.mark.parametrize("filename", sorted(EXPECTED.keys()))
def test_real_pdf_metrics_pass_validator_and_are_plausible(filename: str) -> None:
    path = PDF_DIR / filename
    if not path.exists():
        pytest.skip(f"missing {filename}")
    metrics = PDFParser().parse(path)[0]
    validate_metrics([metrics])
    assert metrics.month == EXPECTED[filename]

    numeric = [
        v
        for v in (
            metrics.pmi_total,
            metrics.production,
            metrics.new_orders,
            metrics.sales,
            metrics.input_price,
            metrics.employment,
        )
        if v is not None
    ]
    assert numeric, "expected at least one numeric indicator"
    for v in numeric:
        assert 0.0 <= v <= 100.0


def test_khordad_headline_matches_published_summary() -> None:
    path = PDF_DIR / "خرداد.pdf"
    if not path.exists():
        pytest.skip("missing خرداد.pdf")
    metrics = PDFParser().parse(path)[0]
    assert metrics.month == "1405-03"
    assert metrics.pmi_total == pytest.approx(KNOWN_HEADLINE["خرداد.pdf"], abs=0.05)


def test_explicit_month_override_wins() -> None:
    path = PDF_DIR / "خرداد.pdf"
    if not path.exists():
        pytest.skip("missing خرداد.pdf")
    metrics = PDFParser().parse(path, month="1405-03")[0]
    assert isinstance(metrics, ShamkhMetrics)
    assert metrics.month == "1405-03"
