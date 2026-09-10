"""Rebuild historical CSV from local ICCIMA PDFs + existing canonical rows.

Usage:
    python scripts/rebuild_from_local_pdfs.py --pdf-dir ../pmi-analyzer/_pdf_probe
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pmi_analyzer.cli import _sanitize_metrics
from pmi_analyzer.data.loader import append_record, load_historical, rewrite_historical
from pmi_analyzer.parser.pdf_parser import PDFParser

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("rebuild")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild shamkh_historical.csv from local PDFs")
    parser.add_argument("--csv", default="data/shamkh_historical.csv")
    parser.add_argument("--pdf-dir", required=True, help="Directory containing Shamkh PDFs")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    pdf_dir = Path(args.pdf_dir)
    rewrite_historical(csv_path)
    existing = {m.month for m in load_historical(csv_path)} if csv_path.exists() else set()
    logger.info("Existing canonical months: %s", sorted(existing))

    pdf_parser = PDFParser()
    added = 0
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        logger.info("Parsing %s", pdf.name)
        raw = pdf_parser.parse(pdf)
        clean = _sanitize_metrics(raw)
        for m in clean:
            if m.month in existing:
                logger.info("  skip existing %s", m.month)
                continue
            if m.pmi_total is None and not m.production:
                logger.warning("  skip low-quality %s (no headline/production)", m.month)
                continue
            if m.production is None and (m.pmi_total is None or m.pmi_total < 35.0):
                logger.warning("  skip low-quality %s (no production, weak headline)", m.month)
                continue
            append_record(m, csv_path)
            existing.add(m.month)
            added += 1
            logger.info("  wrote %s pmi=%s prod=%s", m.month, m.pmi_total, m.production)

    logger.info("Added %d new month(s)", added)
    rewrite_historical(csv_path)
    for m in load_historical(csv_path):
        logger.info("  %s pmi=%s", m.month, m.pmi_total)


if __name__ == "__main__":
    main()
