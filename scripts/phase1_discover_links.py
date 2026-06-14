"""Phase 1 - Discover all historical Shamkh PDF links.

Run once to build data/report_links.json:

    python scripts/phase1_discover_links.py
    python scripts/phase1_discover_links.py --resolve --verbose

Options:
    --resolve   Visit each article page to find missing PDF URLs (slower)
    --verbose   Enable DEBUG logging
    --output    Output JSON path (default: data/report_links.json)
    --delay     Seconds between requests (default: 1.0)
"""

import argparse
import logging
from pathlib import Path

from pmi_analyzer.scraper.archive_scraper import ArchiveScraper
from pmi_analyzer.scraper.link_store import save_links


def main():
    parser = argparse.ArgumentParser(description="Phase 1: Discover Shamkh PDF links")
    parser.add_argument("--resolve", action="store_true",
                        help="Visit each article page to resolve missing PDF URLs")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable DEBUG logging")
    parser.add_argument("--output", default="data/report_links.json",
                        help="Output JSON path (default: data/report_links.json)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between requests (default: 1.0)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    output_path = Path(args.output)
    scraper = ArchiveScraper(delay=args.delay)

    print("\n=== Phase 1: Discovering Shamkh report links ===")
    links = scraper.discover_all()

    if args.resolve:
        print("\n=== Phase 1b: Resolving missing PDF URLs ===")
        links = scraper.resolve_missing_pdfs(links)

    save_links(links, output_path)

    with_pdf = sum(1 for lnk in links if lnk.pdf_url)
    without_pdf = len(links) - with_pdf

    print(f"\n✅ Saved {len(links)} links -> {output_path}")
    print(f"   PDF found   : {with_pdf}")
    print(f"   PDF missing : {without_pdf}")
    print("\nSample:")
    for lnk in links[:5]:
        print(f"  {lnk.period_label or 'unknown':20s}  {lnk.pdf_url or '(no pdf yet)'}")


if __name__ == "__main__":
    main()
