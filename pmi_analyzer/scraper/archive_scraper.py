"""Historical archive scraper for Shamkh (PMI) reports.

Phase 1: Discover all PDF links from otaghiranonline.ir and iccima.ir archives.
"""

import re
import time
import logging
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ReportLink:
    """A discovered Shamkh report with its PDF URL and metadata."""

    title: str
    page_url: str
    pdf_url: Optional[str]
    period_label: Optional[str]  # e.g. 'دی ۱۴۰۴'
    period_number: Optional[int]  # e.g. 88

    def __repr__(self) -> str:
        return f"ReportLink(period={self.period_label!r}, pdf={self.pdf_url!r})"


class ArchiveScraper:
    """Scrape all historical Shamkh PDF links from known archive pages.

    Sources (in priority order):
      1. otaghiranonline.ir/tag/11491  - Otagh Iran Online, paginated
      2. iccima.ir  - WordPress search / category pages

    Usage::

        scraper = ArchiveScraper()
        links = scraper.discover_all()
        for link in links:
            print(link)
    """

    OTAGH_BASE = "https://otaghiranonline.ir"
    OTAGH_TAG_URL = "https://otaghiranonline.ir/tag/11491/{page}"
    OTAGH_MAX_PAGES = 20

    ICCIMA_BASE = "https://iccima.ir"
    ICCIMA_SEARCH_URL = "https://iccima.ir/?s=%D8%B4%D8%A7%D9%85%D8%AE"

    PERIOD_RE = re.compile(
        r"(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)"
        r"(?:\s*ماه)?\s*(\d{4})?"
    )
    PERIOD_NUM_RE = re.compile(r"دوره\s*(\d+)")
    PDF_HREF_RE = re.compile(r"\.pdf$", re.IGNORECASE)

    def __init__(self, delay: float = 1.0, timeout: int = 15):
        self.delay = delay
        self.timeout = timeout
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

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def discover_all(self) -> List[ReportLink]:
        """Discover all Shamkh report links from all sources.

        Returns:
            Deduplicated list of ReportLink, sorted newest-first.
        """
        links: List[ReportLink] = []

        logger.info("[Phase 1] Starting historical archive discovery...")

        otagh_links = self._scrape_otagh_archive()
        logger.info(f"  otaghiranonline.ir -> {len(otagh_links)} links")
        links.extend(otagh_links)

        iccima_links = self._scrape_iccima_archive()
        logger.info(f"  iccima.ir          -> {len(iccima_links)} links")
        links.extend(iccima_links)

        # Deduplicate by pdf_url or page_url
        seen: set = set()
        unique: List[ReportLink] = []
        for lnk in links:
            key = lnk.pdf_url or lnk.page_url
            if key not in seen:
                seen.add(key)
                unique.append(lnk)

        unique.sort(key=lambda x: x.period_number or 0, reverse=True)
        logger.info(f"[Phase 1] Total unique reports found: {len(unique)}")
        return unique

    def resolve_missing_pdfs(self, links: List[ReportLink]) -> List[ReportLink]:
        """Phase 1b: Visit each article page to find missing PDF URLs.

        Args:
            links: Output of discover_all()

        Returns:
            Same list with pdf_url filled where possible.
        """
        missing = [lnk for lnk in links if lnk.pdf_url is None]
        logger.info(f"[Phase 1b] Resolving PDFs for {len(missing)} links...")

        for lnk in missing:
            logger.debug(f"  Resolving: {lnk.page_url}")
            pdf = self._resolve_pdf_from_page(lnk.page_url)
            if pdf:
                lnk.pdf_url = pdf
                logger.debug(f"  Found: {pdf}")
            else:
                logger.warning(f"  No PDF at: {lnk.page_url}")
            time.sleep(self.delay)

        resolved = sum(1 for lnk in links if lnk.pdf_url)
        logger.info(f"[Phase 1b] Resolved: {resolved}/{len(links)}")
        return links

    # ------------------------------------------------------------------ #
    #  Source 1: otaghiranonline.ir
    # ------------------------------------------------------------------ #

    def _scrape_otagh_archive(self) -> List[ReportLink]:
        links: List[ReportLink] = []
        for page_num in range(self.OTAGH_MAX_PAGES):
            url = self.OTAGH_TAG_URL.format(page=page_num)
            logger.debug(f"  Fetching otaghiran page {page_num}: {url}")
            soup = self._get_soup(url)
            if soup is None:
                break
            items = soup.select("article, .news-item, .post, li.item")
            if not items:
                items = soup.find_all("a", href=True)
            page_links = self._extract_links_from_items(items, self.OTAGH_BASE)
            if not page_links:
                logger.debug(f"  No items on page {page_num}, stopping.")
                break
            links.extend(page_links)
            time.sleep(self.delay)
        return links

    # ------------------------------------------------------------------ #
    #  Source 2: iccima.ir (WordPress)
    # ------------------------------------------------------------------ #

    def _scrape_iccima_archive(self) -> List[ReportLink]:
        links: List[ReportLink] = []
        page_num = 1
        while True:
            url = (
                self.ICCIMA_SEARCH_URL
                if page_num == 1
                else f"{self.ICCIMA_SEARCH_URL}&paged={page_num}"
            )
            logger.debug(f"  Fetching iccima page {page_num}: {url}")
            soup = self._get_soup(url)
            if soup is None:
                break
            items = soup.select("article, .post, h2.entry-title, .search-result")
            if not items:
                break
            page_links = self._extract_links_from_items(items, self.ICCIMA_BASE)
            if not page_links:
                break
            links.extend(page_links)
            next_btn = soup.select_one("a.next, .nav-next a, a[rel='next']")
            if not next_btn:
                break
            page_num += 1
            time.sleep(self.delay)
        return links

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _extract_links_from_items(self, items, base_url: str) -> List[ReportLink]:
        links: List[ReportLink] = []
        for item in items:
            anchor = item if item.name == "a" else item.find("a", href=True)
            if not anchor:
                continue
            href = anchor.get("href", "")
            title = anchor.get_text(strip=True)
            if not self._is_shamkh_related(title, href):
                continue
            page_url = urljoin(base_url, href)
            pdf_url = self._find_pdf_in_element(item, base_url)
            period_label, period_number = self._extract_period(title)
            links.append(
                ReportLink(
                    title=title,
                    page_url=page_url,
                    pdf_url=pdf_url,
                    period_label=period_label,
                    period_number=period_number,
                )
            )
        return links

    def _find_pdf_in_element(self, element, base_url: str) -> Optional[str]:
        if element.name == "a":
            href = element.get("href", "")
            if self.PDF_HREF_RE.search(href):
                return urljoin(base_url, href)
            return None
        for a in element.find_all("a", href=True):
            href = a["href"]
            if self.PDF_HREF_RE.search(href):
                return urljoin(base_url, href)
        return None

    def _resolve_pdf_from_page(self, page_url: str) -> Optional[str]:
        soup = self._get_soup(page_url)
        if soup is None:
            return None
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if self.PDF_HREF_RE.search(href):
                return urljoin(base, href)
        return None

    def _is_shamkh_related(self, title: str, href: str) -> bool:
        keywords = ["شامخ", "pmi", "مدیران خرید", "شاخص مدیران"]
        combined = (title + " " + href).lower()
        return any(kw in combined for kw in keywords)

    def _extract_period(self, text: str):
        period_label = None
        period_number = None
        match = self.PERIOD_RE.search(text)
        if match:
            month = match.group(1)
            year = match.group(2) or ""
            period_label = f"{month} {year}".strip()
        num_match = self.PERIOD_NUM_RE.search(text)
        if num_match:
            period_number = int(num_match.group(1))
        return period_label, period_number

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            logger.warning(f"  HTTP error for {url}: {e}")
            return None
