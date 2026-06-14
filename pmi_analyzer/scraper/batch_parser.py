"""Phase 2b - Batch parse all downloaded PDFs into ShamkhMetrics."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from pmi_analyzer.scraper.archive_scraper import ReportLink
from pmi_analyzer.parser.pdf_parser import PDFParser
from pmi_analyzer.types import ShamkhMetrics

logger = logging.getLogger(__name__)


class BatchParser:
    """Parse all downloaded PDFs and collect ShamkhMetrics.

    Usage::

        parser = BatchParser()
        all_metrics = parser.parse_all(download_results)
    """

    def __init__(self):
        self.pdf_parser = PDFParser()

    def parse_all(
        self,
        download_results: List[Tuple[ReportLink, Optional[Path]]],
    ) -> List[ShamkhMetrics]:
        """Parse all successfully downloaded PDFs.

        Args:
            download_results: Output of BatchDownloader.download_all().

        Returns:
            List of ShamkhMetrics, one per successfully parsed PDF.
            Failures are logged and skipped.
        """
        valid = [(lnk, p) for lnk, p in download_results if p and p.exists()]
        logger.info(f"[Phase 2b] Parsing {len(valid)} PDFs...")

        all_metrics: List[ShamkhMetrics] = []
        failed: List[str] = []

        for i, (lnk, pdf_path) in enumerate(valid, 1):
            logger.debug(f"  [{i}/{len(valid)}] Parsing: {pdf_path.name}")
            try:
                # Use period_label as month hint if available
                metrics_list = self.pdf_parser.parse(
                    pdf_path,
                    month=lnk.period_label or pdf_path.stem,
                )
                for m in metrics_list:
                    # Attach period_number for sorting
                    if lnk.period_number and not hasattr(m, '_period_number'):
                        object.__setattr__(m, '_period_number', lnk.period_number) \
                            if hasattr(m, '__dataclass_fields__') else None
                all_metrics.extend(metrics_list)
                logger.debug(f"    OK - month={metrics_list[0].month if metrics_list else '?'}")
            except Exception as e:
                logger.warning(f"    FAILED ({pdf_path.name}): {e}")
                failed.append(str(pdf_path))

        ok = len(all_metrics)
        logger.info(f"[Phase 2b] Parsed: {ok} records, Failed: {len(failed)}")

        if failed:
            logger.warning("  Failed PDFs:")
            for f in failed:
                logger.warning(f"    {f}")

        # Sort by month ascending
        all_metrics.sort(key=lambda m: m.month)
        return all_metrics

    def parse_single(self, pdf_path: Path, month: Optional[str] = None) -> Optional[ShamkhMetrics]:
        """Parse a single PDF and return the first ShamkhMetrics (or None).

        Args:
            pdf_path: Path to PDF file.
            month: Optional month label override.

        Returns:
            First ShamkhMetrics from the PDF, or None on failure.
        """
        try:
            results = self.pdf_parser.parse(pdf_path, month=month)
            return results[0] if results else None
        except Exception as e:
            logger.warning(f"parse_single failed ({pdf_path}): {e}")
            return None
