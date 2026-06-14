"""Phase 4 - Monthly auto-updater.

Checks if a new Shamkh report is available, downloads and parses it,
then appends the result to shamkh_historical.csv.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pmi_analyzer.scraper.archive_scraper import ArchiveScraper, ReportLink
from pmi_analyzer.scraper.batch_downloader import BatchDownloader
from pmi_analyzer.scraper.batch_parser import BatchParser
from pmi_analyzer.data.loader import load_historical, append_record
from pmi_analyzer.types import ShamkhMetrics

logger = logging.getLogger(__name__)


@dataclass
class UpdateResult:
    """Result of a monthly update run."""
    status: str            # 'new' | 'already_up_to_date' | 'failed'
    month: Optional[str]   # month label if new record found
    metrics: Optional[ShamkhMetrics] = None
    error: Optional[str] = None

    @property
    def is_new(self) -> bool:
        return self.status == "new"


class MonthlyUpdater:
    """Download and append the latest Shamkh report to historical CSV.

    Usage::

        updater = MonthlyUpdater()
        result = updater.run()
        if result.is_new:
            print(f"New data: {result.month}  PMI={result.metrics.pmi_total}")
        else:
            print("Already up to date.")
    """

    def __init__(
        self,
        csv_path: Path = None,
        pdf_dir: Path = Path("data/pdfs"),
        delay: float = 1.0,
    ):
        if csv_path is None:
            csv_path = Path(__file__).parent.parent.parent / "data" / "shamkh_historical.csv"
        self.csv_path = csv_path
        self.pdf_dir = pdf_dir
        self.delay = delay

        self._scraper = ArchiveScraper(delay=delay)
        self._downloader = BatchDownloader(pdf_dir=pdf_dir, delay=delay)
        self._parser = BatchParser()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def run(self) -> UpdateResult:
        """Run one update cycle.

        1. Discover the latest report link.
        2. Check if we already have that month.
        3. If not, download + parse + append.

        Returns:
            UpdateResult with status 'new', 'already_up_to_date', or 'failed'.
        """
        try:
            # Step 1: find the latest report link
            logger.info("[Updater] Discovering latest report link...")
            latest_link = self._get_latest_link()
            if latest_link is None:
                return UpdateResult(status="failed", month=None,
                                    error="Could not discover any report links.")

            logger.info(f"[Updater] Latest link: period={latest_link.period_label} pdf={latest_link.pdf_url}")

            # Step 2: check if we already have this month
            existing_months = self._existing_months()
            if latest_link.period_label and self._month_exists(latest_link.period_label, existing_months):
                logger.info(f"[Updater] Already up to date ({latest_link.period_label}).")
                return UpdateResult(status="already_up_to_date", month=latest_link.period_label)

            # Step 3a: resolve PDF URL if missing
            if not latest_link.pdf_url:
                logger.info("[Updater] Resolving PDF URL...")
                links = self._scraper.resolve_missing_pdfs([latest_link])
                latest_link = links[0]
                if not latest_link.pdf_url:
                    return UpdateResult(status="failed", month=latest_link.period_label,
                                        error="Could not resolve PDF URL.")

            # Step 3b: download
            logger.info(f"[Updater] Downloading: {latest_link.pdf_url}")
            download_results = self._downloader.download_all([latest_link], skip_existing=False)
            _, pdf_path = download_results[0]
            if not pdf_path or not pdf_path.exists():
                return UpdateResult(status="failed", month=latest_link.period_label,
                                    error=f"Download failed: {latest_link.pdf_url}")

            # Step 3c: parse
            logger.info(f"[Updater] Parsing: {pdf_path.name}")
            metrics = self._parser.parse_single(pdf_path, month=latest_link.period_label)
            if metrics is None:
                return UpdateResult(status="failed", month=latest_link.period_label,
                                    error=f"Parse failed: {pdf_path.name}")

            # Step 3d: append to CSV
            logger.info(f"[Updater] Appending: month={metrics.month} pmi={metrics.pmi_total}")
            append_record(metrics, self.csv_path)

            logger.info(f"[Updater] Done. New record: {metrics.month}")
            return UpdateResult(status="new", month=metrics.month, metrics=metrics)

        except Exception as e:
            logger.exception("[Updater] Unexpected error")
            return UpdateResult(status="failed", month=None, error=str(e))

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _get_latest_link(self) -> Optional[ReportLink]:
        """Discover links and return the one with the highest period_number."""
        links = self._scraper.discover_all()
        if not links:
            return None
        # discover_all() already sorts newest-first
        return links[0]

    def _existing_months(self) -> set:
        """Return set of month strings already in the CSV."""
        try:
            return {m.month for m in load_historical(self.csv_path)}
        except FileNotFoundError:
            return set()

    def _month_exists(self, period_label: str, existing_months: set) -> bool:
        """Check if period_label matches any existing month (fuzzy)."""
        label_lower = period_label.strip().lower()
        for m in existing_months:
            if label_lower in m.lower() or m.lower() in label_lower:
                return True
        return False
