"""Downloader for Shamkh (PMI) reports from iccima.ir.

Strategy (tried in order):
  0. Reports listing page (/گزارش-ها/) – most reliable; lists all posts
  1. WordPress REST API       – fastest, no HTML parsing needed
  2. Site-search scrape       – fallback; Elementor-aware selectors
  3. Candidate URL probe      – HEAD-probes confirmed WP upload paths
  4. Shamekh category page    – scrapes the dedicated category listing

Confirmed upload path pattern (from live site, June 2026):
  wp-content/uploads/{gregorian_year}/{greg_month:02d}/{jalali_year_2d}-{shamsi_name}.pdf
  e.g. wp-content/uploads/2026/06/405-فروردین.pdf
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

# Shamsi month index (1-based) → Gregorian month(s) of upload.
# Reports are typically published 1-3 months after the reference month.
_SHAMSI_TO_GREGORIAN_UPLOAD: dict[int, list[int]] = {
    1: [4, 5, 6],   # فروردین  → Apr-Jun  (confirmed: 2026/06)
    2: [5, 6, 7],   # اردیبهشت → May-Jul
    3: [6, 7, 8],   # خرداد    → Jun-Aug
    4: [7, 8, 9],   # تیر      → Jul-Sep
    5: [8, 9, 10],  # مرداد    → Aug-Oct
    6: [9, 10, 11], # شهریور   → Sep-Nov
    7: [10, 11, 12],# مهر      → Oct-Dec
    8: [11, 12, 1], # آبان     → Nov-Jan
    9: [12, 1, 2],  # آذر      → Dec-Feb
    10: [1, 2, 3],  # دی       → Jan-Mar
    11: [2, 3, 4],  # بهمن     → Feb-Apr
    12: [3, 4, 5],  # اسفند    → Mar-May
}

_PDF_RE = re.compile(r"\.pdf$", re.IGNORECASE)
_SHAMKH_RE = re.compile(r"شامخ|shamekh|shamkh|pmi", re.IGNORECASE)

# Elementor post link selectors (most-specific first)
_ELEMENTOR_POST_LINK_SELECTORS = [
    ".elementor-post__title a",
    ".elementor-post .elementor-post__title a",
    "h2.elementor-heading-title a",
    "h3.elementor-heading-title a",
    ".elementor-widget-heading a",
    "h2.entry-title a",
    "h3.entry-title a",
    "article a[href]",
]


def _current_shamsi() -> tuple[int, int]:
    """Return (shamsi_year, shamsi_month) for today."""
    try:
        import jdatetime
        today = jdatetime.date.today()
        return today.year, today.month
    except ImportError:
        pass
    import datetime
    today = datetime.date.today()
    g_year, g_month = today.year, today.month
    shamsi_year = g_year - 621 if g_month >= 4 else g_year - 622
    shamsi_month = ((g_month + 8) % 12) + 1
    return shamsi_year, shamsi_month


def _candidate_urls(base_url: str) -> list[str]:
    """
    Generate plausible PDF upload URLs for the last ~3 Shamsi months.

    Confirmed pattern from iccima.ir (June 2026):
      /wp-content/uploads/2026/06/405-فروردین.pdf

    i.e.  {jalali_year_last3digits}-{shamsi_month_name}.pdf
    """
    import datetime

    sy, sm = _current_shamsi()
    today = datetime.date.today()
    g_year = today.year

    candidates: list[str] = []

    for delta in range(4):  # current + 3 months back
        month_idx = sm - delta
        year = sy
        if month_idx <= 0:
            month_idx += 12
            year -= 1

        month_name = _SHAMSI_MONTHS[month_idx - 1]
        upload_months = _SHAMSI_TO_GREGORIAN_UPLOAD.get(month_idx, [today.month])

        # Year offset: if shamsi month rolled back to previous year, upload
        # year might also be off by one.
        for year_offset in [0, -1]:
            upload_year = g_year + year_offset
            # short year: last 3 digits (e.g. 1405 -> "405")
            year_short = str(year)[-3:]
            year_full = str(year)

            for um in upload_months:
                for fname in [
                    # Confirmed pattern: 405-فروردین.pdf
                    f"{year_short}-{month_name}.pdf",
                    # Variants observed in older reports
                    f"shamekh-{month_name}-{year_full}.pdf",
                    f"شامخ-{month_name}-{year_full}.pdf",
                    f"شاخص-مدیران-خرید-{month_name}-{year_full}.pdf",
                    f"shamekh-{year_full}.pdf",
                ]:
                    candidates.append(
                        f"{base_url}/wp-content/uploads/{upload_year}/{um:02d}/{fname}"
                    )

    return candidates


# ---------------------------------------------------------------------------
# Downloader class
# ---------------------------------------------------------------------------


class ICCIMADownloader:
    """Download the latest Shamkh PDF report from iccima.ir."""

    WP_API = "https://iccima.ir/wp-json/wp/v2/posts"
    SEARCH_URL = "https://iccima.ir/?s=%D8%B4%D8%A7%D9%85%D8%AE"  # ?s=شامخ
    REPORTS_URL = "https://iccima.ir/گزارش-ها/"  # reports listing page
    CATEGORY_URL = "https://iccima.ir/category/reports/statistics-center-reports/shamekh/"

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

        Returns:
            Path to saved PDF file.

        Raises:
            DownloadError: if all strategies fail.
        """
        pdf_url = (
            self._find_via_candidate_urls()       # Strategy 3 first – fastest
            or self._find_via_reports_page()      # Strategy 0
            or self._find_via_wp_api()            # Strategy 1
            or self._find_via_search_page()       # Strategy 2
            or self._find_via_category_page()     # Strategy 4
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
            self._find_via_candidate_urls()
            or self._find_via_reports_page()
            or self._find_via_wp_api()
            or self._find_via_search_page()
            or self._find_via_category_page()
        )

    # ------------------------------------------------------------------
    # Strategy 0: Reports listing page (iccima.ir/گزارش-ها/)
    # ------------------------------------------------------------------

    def _find_via_reports_page(self) -> Optional[str]:
        """Scrape the reports listing page which shows all PMI posts."""
        try:
            resp = self.session.get(self.REPORTS_URL, timeout=self.config.timeout)
            resp.raise_for_status()
        except Exception as exc:
            logger.debug(f"Reports page unavailable: {exc}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find links whose text or href contains شامخ / PMI
        post_urls: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text()
            if _SHAMKH_RE.search(text + href):
                full_url = urljoin(self.config.base_url, href)
                if full_url not in post_urls and not _PDF_RE.search(href):
                    post_urls.append(full_url)

        logger.debug(f"Strategy 0: {len(post_urls)} post(s) found on reports page")

        for post_url in post_urls[:5]:
            try:
                pr = self.session.get(post_url, timeout=self.config.timeout)
                pr.raise_for_status()
                pr_soup = BeautifulSoup(pr.text, "html.parser")
                pdf = self._first_pdf_link(pr_soup, self.config.base_url)
                if pdf:
                    logger.debug(f"Strategy 0 found: {pdf}")
                    return pdf
                time.sleep(0.3)
            except Exception:
                continue

        return None

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
    # Strategy 2: Site search page scrape (Elementor-aware)
    # ------------------------------------------------------------------

    def _find_via_search_page(self) -> Optional[str]:
        """Scrape iccima.ir search results using Elementor-aware selectors."""
        try:
            resp = self.session.get(self.SEARCH_URL, timeout=self.config.timeout)
            resp.raise_for_status()
        except Exception as exc:
            logger.debug(f"Search page unavailable: {exc}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        pdf = self._first_pdf_link(soup, self.config.base_url)
        if pdf:
            return pdf

        post_links: list[str] = []
        for selector in _ELEMENTOR_POST_LINK_SELECTORS:
            for a in soup.select(selector)[:5]:
                href = a.get("href", "")
                if href and _SHAMKH_RE.search(a.get_text() + href):
                    full_url = urljoin(self.config.base_url, href)
                    if full_url not in post_links:
                        post_links.append(full_url)

        for article_url in post_links[:5]:
            try:
                ar = self.session.get(article_url, timeout=self.config.timeout)
                ar.raise_for_status()
                ar_soup = BeautifulSoup(ar.text, "html.parser")
                pdf = self._first_pdf_link(ar_soup, self.config.base_url)
                if pdf:
                    return pdf
                time.sleep(0.5)
            except Exception:
                continue

        return None

    # ------------------------------------------------------------------
    # Strategy 3: Candidate URL probe (HIGHEST PRIORITY – called first)
    # ------------------------------------------------------------------

    def _find_via_candidate_urls(self) -> Optional[str]:
        """HEAD-probe a list of predictable WP upload paths.

        Confirmed pattern (June 2026):
          /wp-content/uploads/2026/06/405-فروردین.pdf
        """
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
    # Strategy 4: Shamekh category page scrape
    # ------------------------------------------------------------------

    def _find_via_category_page(self) -> Optional[str]:
        """Scrape the dedicated shamekh category listing page."""
        try:
            resp = self.session.get(self.CATEGORY_URL, timeout=self.config.timeout)
            resp.raise_for_status()
        except Exception as exc:
            logger.debug(f"Category page unavailable: {exc}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        post_urls: list[str] = []
        for selector in _ELEMENTOR_POST_LINK_SELECTORS:
            for a in soup.select(selector):
                href = a.get("href", "")
                if href:
                    full_url = urljoin(self.config.base_url, href)
                    if full_url not in post_urls:
                        post_urls.append(full_url)
            if post_urls:
                break

        if not post_urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if _SHAMKH_RE.search(href) and href.startswith(self.config.base_url):
                    if href not in post_urls:
                        post_urls.append(href)

        for post_url in post_urls[:5]:
            try:
                pr = self.session.get(post_url, timeout=self.config.timeout)
                pr.raise_for_status()
                pr_soup = BeautifulSoup(pr.text, "html.parser")

                for a in pr_soup.select("a.elementor-button"):
                    href = a.get("href", "")
                    if _PDF_RE.search(href):
                        return urljoin(self.config.base_url, href)

                for content_sel in [
                    ".elementor-widget-container",
                    ".entry-content",
                    ".post-content",
                ]:
                    content_div = pr_soup.select_one(content_sel)
                    if content_div:
                        pdf = self._first_pdf_link(content_div, self.config.base_url)
                        if pdf:
                            return pdf

                time.sleep(0.5)
            except Exception:
                continue

        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _first_pdf_link(self, soup, base: str) -> Optional[str]:
        """Return the first .pdf href in *soup* that looks like a Shamkh report."""
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if _PDF_RE.search(href) and _SHAMKH_RE.search(href):
                return urljoin(base, href)
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

        url_filename = Path(pdf_url.split("?")[0]).name or "shamkh_latest.pdf"
        output_path = self.config.output_dir / url_filename

        with open(output_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)

        logger.info(f"Saved: {output_path}")
        return output_path
