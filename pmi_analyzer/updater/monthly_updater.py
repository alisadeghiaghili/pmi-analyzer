"""Phase 4 - Monthly auto-updater.

Checks if a new Shamkh report is available, downloads and parses it,
then appends the result to shamkh_historical.csv.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pmi_analyzer.calendar import is_canonical_month, normalize_month_id
from pmi_analyzer.data.loader import append_record, load_historical
from pmi_analyzer.scraper.archive_scraper import ArchiveScraper, ReportLink
from pmi_analyzer.scraper.batch_downloader import BatchDownloader
from pmi_analyzer.scraper.batch_parser import BatchParser
from pmi_analyzer.types import ShamkhMetrics

logger = logging.getLogger(__name__)


@dataclass
class UpdateResult:
    """Result of a monthly update run."""

    status: str  # 'new' | 'already_up_to_date' | 'failed'
    month: Optional[str]  # month label if new record found
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
                return UpdateResult(
                    status="failed", month=None, error="Could not discover any report links."
                )

            logger.info(
                f"[Updater] Latest link: period={latest_link.period_label} pdf={latest_link.pdf_url}"
            )

            # Step 2: check if we already have this month
            existing_months = self._existing_months()
            label_month = normalize_month_id(latest_link.period_label)
            if label_month and self._month_exists(label_month, existing_months):
                logger.info(f"[Updater] Already up to date ({label_month}).")
                return UpdateResult(status="already_up_to_date", month=label_month)

            # Step 3a: resolve PDF URL if missing
            if not latest_link.pdf_url:
                logger.info("[Updater] Resolving PDF URL...")
                links = self._scraper.resolve_missing_pdfs([latest_link])
                latest_link = links[0]
                if not latest_link.pdf_url:
                    return UpdateResult(
                        status="failed",
                        month=latest_link.period_label,
                        error="Could not resolve PDF URL.",
                    )

            # Step 3b: download
            logger.info(f"[Updater] Downloading: {latest_link.pdf_url}")
            download_results = self._downloader.download_all([latest_link], skip_existing=False)
            _, pdf_path = download_results[0]
            if not pdf_path or not pdf_path.exists():
                return UpdateResult(
                    status="failed",
                    month=latest_link.period_label,
                    error=f"Download failed: {latest_link.pdf_url}",
                )

            # Step 3c: parse
            logger.info(f"[Updater] Parsing: {pdf_path.name}")
            metrics = self._parser.parse_single(pdf_path, month=label_month)
            if metrics is None:
                return UpdateResult(
                    status="failed",
                    month=latest_link.period_label,
                    error=f"Parse failed: {pdf_path.name}",
                )

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

    def _month_exists(self, month_id: str, existing_months: set) -> bool:
        """Check whether a canonical month id is already stored.

        Args:
            month_id: Canonical ``YYYY-MM`` identifier.
            existing_months: Month ids already present in the historical CSV.

        Returns:
            True on exact canonical match; Persian labels are normalised first.
        """
        candidate = normalize_month_id(month_id) if not is_canonical_month(month_id) else month_id
        if not candidate:
            return False
        normalized_existing = set()
        for m in existing_months:
            if is_canonical_month(m):
                normalized_existing.add(m)
            else:
                alt = normalize_month_id(m)
                if alt:
                    normalized_existing.add(alt)
        return candidate in normalized_existing
