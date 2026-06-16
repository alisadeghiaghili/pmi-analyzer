"""Downloader for Shamkh (PMI) reports from iccima.ir.

Strategy (tried in order):
  1. WordPress REST API  – fastest, no HTML parsing needed
  2. Site-search scrape  – fallback when REST is blocked/unavailable
  3. Candidate URL probe – last resort; tries predictable WP upload paths
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from pmi_analyzer.types import DownloadConfig
from pmi_analyzer.exceptions import DownloadError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persian month helpers
# ---------------------------------------------------------------------------

_SHAMSI_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]

# Rough mapping: Shamsi month index (1-based) → Gregorian month(s) of upload.
# Reports are typically published 1-3 months after the reference month.
_SHAMSI_TO_GREGORIAN_UPLOAD: dict[int, list[int]] = {
    1: [4, 5],  # فروردین  → Apr-May
    2: [5, 6],  # اردیبهشت → May-Jun
    3: [6, 7],  # خرداد    → Jun-Jul
    4: [7, 8],  # تیر      → Jul-Aug
    5: [8, 9],  # مرداد    → Aug-Sep
    6: [9, 10],  # شهریور   → Sep-Oct
    7: [10, 11],  # مهر      → Oct-Nov
    8: [11, 12],  # آبان     → Nov-Dec
    9: [1, 2],  # آذر      → Jan-Feb  (year +1)
    10: [2, 3],  # دی       → Feb-Mar
    11: [3, 4],  # بهمن     → Mar-Apr
    12: [4, 5],  # اسفند    → Apr-May
}

_PDF_RE = re.compile(r"\.pdf$", re.IGNORECASE)
_SHAMKH_RE = re.compile(r"شامخ|shamekh|shamkh", re.IGNORECASE)


def _current_shamsi() -> tuple[int, int]:
    """Return (shamsi_year, shamsi_month) for today using jdatetime if available."""
    try:
        import jdatetime

        today = jdatetime.date.today()
        return today.year, today.month
    except ImportError:
        pass
    # Rough fallback without jdatetime
    import datetime

    today = datetime.date.today()
    g_year, g_month = today.year, today.month
    shamsi_year = g_year - 621 if g_month >= 4 else g_year - 622
    shamsi_month = ((g_month + 8) % 12) + 1
    return shamsi_year, shamsi_month


def _candidate_urls(base_url: str) -> list[str]:
    """Generate plausible PDF upload URLs for the last ~3 Shamsi months."""
    import datetime

    sy, sm = _current_shamsi()
    today = datetime.date.today()

    candidates: list[str] = []
    for delta in range(3):  # current month and 2 months back
        month_idx = sm - delta
        year = sy
        if month_idx <= 0:
            month_idx += 12
            year -= 1

        month_name = _SHAMSI_MONTHS[month_idx - 1]
        upload_months = _SHAMSI_TO_GREGORIAN_UPLOAD.get(month_idx, [today.month])
        upload_year = today.year

        for um in upload_months:
            for fname in [
                f"شامخ-{month_name}-{year}.pdf",
                f"شاخص-مدیران-خرید-{month_name}-{year}.pdf",
                f"shamekh-{year}.pdf",
                f"shamekh-{month_name}-{year}.pdf",
            ]:
                candidates.append(f"{base_url}/wp-content/uploads/{upload_year}/{um:02d}/{fname}")

    return candidates


# ---------------------------------------------------------------------------
# Downloader class
# ---------------------------------------------------------------------------


class ICCIMADownloader:
    """Download the latest Shamkh PDF report from iccima.ir."""

    WP_API = "https://iccima.ir/wp-json/wp/v2/posts"
    SEARCH_URL = "https://iccima.ir/?s=%D8%B4%D8%A7%D9%85%D8%AE"  # ?s=شامخ

    def __init__(self, config: DownloadConfig | None = None) -> None:
        self.config = config or DownloadConfig()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; pmi-analyzer/1.0; "
                    "+https://github.com/alisadeghiaghili/pmi-analyzer)"
                ),
                "Accept-Language": "fa,en;q=0.9",
            }
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download_latest(self) -> Path:
        """Download the latest Shamkh report PDF.

        Tries three strategies in order:
          1. WordPress REST API
          2. Site search page scrape
          3. Candidate URL probe

        Returns:
            Path to saved PDF file.

        Raises:
            DownloadError: if all strategies fail.
        """
        pdf_url = (
            self._find_via_wp_api()
            or self._find_via_search_page()
            or self._find_via_candidate_urls()
        )

        if not pdf_url:
            raise DownloadError(
                "Could not find a Shamkh PDF on iccima.ir. "
                "The site structure may have changed again. "
                "Check https://iccima.ir manually and update the downloader."
            )

        logger.info(f"Found PDF: {pdf_url}")
        return self._download(pdf_url)

    def get_latest_url(self) -> Optional[str]:
        """Return the PDF URL without downloading. Useful for debugging."""
        return (
            self._find_via_wp_api()
            or self._find_via_search_page()
            or self._find_via_candidate_urls()
        )

    # ------------------------------------------------------------------
    # Strategy 1: WordPress REST API
    # ------------------------------------------------------------------

    def _find_via_wp_api(self) -> Optional[str]:
        """Query the WP REST API for the latest post mentioning شامخ."""
        try:
            resp = self.session.get(
                self.WP_API,
                params={"search": "شامخ", "per_page": 5, "orderby": "date", "order": "desc"},
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            posts = resp.json()
        except Exception as exc:
            logger.debug(f"WP API unavailable: {exc}")
            return None

        for post in posts:
            content = post.get("content", {}).get("rendered", "")
            soup = BeautifulSoup(content, "html.parser")
            pdf = self._first_pdf_link(soup, self.config.base_url)
            if pdf:
                logger.debug(f"Strategy 1 (WP API) found: {pdf}")
                return pdf

        return None

    # ------------------------------------------------------------------
    # Strategy 2: Site search page scrape
    # ------------------------------------------------------------------

    def _find_via_search_page(self) -> Optional[str]:
        """Scrape iccima.ir search results for a PDF link."""
        try:
            resp = self.session.get(self.SEARCH_URL, timeout=self.config.timeout)
            resp.raise_for_status()
        except Exception as exc:
            logger.debug(f"Search page unavailable: {exc}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # First pass: direct PDF anchors on the search results page
        pdf = self._first_pdf_link(soup, self.config.base_url)
        if pdf:
            logger.debug(f"Strategy 2 (search page direct) found: {pdf}")
            return pdf

        # Second pass: visit each article link and look for PDF inside
        for article_anchor in soup.select("article a[href], h2.entry-title a[href]")[:5]:
            article_url = urljoin(self.config.base_url, article_anchor["href"])
            if not _SHAMKH_RE.search(article_anchor.get_text() + article_url):
                continue
            try:
                ar = self.session.get(article_url, timeout=self.config.timeout)
                ar.raise_for_status()
                ar_soup = BeautifulSoup(ar.text, "html.parser")
                pdf = self._first_pdf_link(ar_soup, self.config.base_url)
                if pdf:
                    logger.debug(f"Strategy 2 (article page) found: {pdf}")
                    return pdf
                time.sleep(0.5)
            except Exception:
                continue

        return None

    # ------------------------------------------------------------------
    # Strategy 3: Candidate URL probe
    # ------------------------------------------------------------------

    def _find_via_candidate_urls(self) -> Optional[str]:
        """HEAD-probe a list of predictable WP upload paths."""
        for url in _candidate_urls(self.config.base_url):
            try:
                r = self.session.head(url, timeout=10, allow_redirects=True)
                if r.status_code == 200:
                    ct = r.headers.get("Content-Type", "")
                    if "pdf" in ct or _PDF_RE.search(url):
                        logger.debug(f"Strategy 3 (probe) found: {url}")
                        return url
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _first_pdf_link(self, soup: BeautifulSoup, base: str) -> Optional[str]:
        """Return the first .pdf href in *soup* that looks like a Shamkh report."""
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if _PDF_RE.search(href) and _SHAMKH_RE.search(href):
                return urljoin(base, href)
        # Relax: any PDF if the page is already shamkh-related
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if _PDF_RE.search(href):
                return urljoin(base, href)
        return None

    def _download(self, pdf_url: str) -> Path:
        """Stream-download *pdf_url* and save to output_dir."""
        try:
            resp = self.session.get(pdf_url, timeout=self.config.timeout, stream=True)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise DownloadError(f"Download failed: {exc}") from exc

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Derive a meaningful filename from the URL
        url_filename = Path(pdf_url.split("?")[0]).name or "shamkh_latest.pdf"
        output_path = self.config.output_dir / url_filename

        with open(output_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)

        logger.info(f"Saved: {output_path}")
        return output_path
