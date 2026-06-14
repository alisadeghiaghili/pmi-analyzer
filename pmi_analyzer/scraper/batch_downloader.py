"""Phase 2a - Batch download all discovered PDFs."""

import time
import logging
from pathlib import Path
from typing import List, Tuple

import requests

from pmi_analyzer.scraper.archive_scraper import ReportLink

logger = logging.getLogger(__name__)

DEFAULT_PDF_DIR = Path("data/pdfs")


class BatchDownloader:
    """Download all PDFs discovered in Phase 1.

    Usage::

        downloader = BatchDownloader()
        results = downloader.download_all(links)
        # results: list of (ReportLink, local_path | None)
    """

    def __init__(self, pdf_dir: Path = DEFAULT_PDF_DIR, delay: float = 1.5, timeout: int = 30):
        self.pdf_dir = pdf_dir
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (compatible; pmi-analyzer/1.0; "
                "+https://github.com/alisadeghiaghili/pmi-analyzer)"
            )
        })

    def download_all(
        self,
        links: List[ReportLink],
        skip_existing: bool = True,
    ) -> List[Tuple[ReportLink, Path]]:
        """Download every PDF in links.

        Args:
            links: Output of ArchiveScraper.discover_all() (pdf_url must be set).
            skip_existing: If True, skip already-downloaded files.

        Returns:
            List of (ReportLink, local_path). local_path is None if download failed.
        """
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        has_pdf = [lnk for lnk in links if lnk.pdf_url]
        no_pdf = len(links) - len(has_pdf)

        logger.info(f"[Phase 2a] Downloading {len(has_pdf)} PDFs ({no_pdf} skipped - no URL)")

        results: List[Tuple[ReportLink, Path]] = []

        for i, lnk in enumerate(has_pdf, 1):
            local_path = self._local_path(lnk)

            if skip_existing and local_path.exists():
                logger.debug(f"  [{i}/{len(has_pdf)}] Skip (exists): {local_path.name}")
                results.append((lnk, local_path))
                continue

            logger.info(f"  [{i}/{len(has_pdf)}] Downloading: {lnk.pdf_url}")
            path = self._download(lnk.pdf_url, local_path)
            results.append((lnk, path))

            if path:
                logger.info(f"    Saved -> {path.name} ({path.stat().st_size // 1024} KB)")
            else:
                logger.warning(f"    Failed: {lnk.pdf_url}")

            time.sleep(self.delay)

        ok = sum(1 for _, p in results if p and p.exists())
        logger.info(f"[Phase 2a] Done: {ok}/{len(has_pdf)} downloaded successfully")
        return results

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _local_path(self, lnk: ReportLink) -> Path:
        """Build a safe local filename from period info or URL."""
        if lnk.period_number:
            name = f"shamkh_period_{lnk.period_number:03d}.pdf"
        elif lnk.period_label:
            safe = lnk.period_label.replace(" ", "_").replace("/", "-")
            name = f"shamkh_{safe}.pdf"
        else:
            # fallback: last segment of URL
            name = lnk.pdf_url.rstrip("/").split("/")[-1]
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
        return self.pdf_dir / name

    def _download(self, url: str, dest: Path) -> Path:
        """HTTP GET url -> dest file. Returns dest on success, None on error."""
        try:
            resp = self.session.get(url, timeout=self.timeout, stream=True)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return dest
        except requests.RequestException as e:
            logger.warning(f"  Download error ({url}): {e}")
            return None
