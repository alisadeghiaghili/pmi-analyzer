"""Phase 2 - Download all PDFs and parse them into ShamkhMetrics.

Run after phase1_discover_links.py:

    python scripts/phase2_download_and_parse.py

Options:
    --links     Path to report_links.json  (default: data/report_links.json)
    --pdf-dir   Directory to store PDFs    (default: data/pdfs)
    --output    Output CSV path            (default: data/shamkh_raw.csv)
    --no-skip   Re-download existing PDFs
    --verbose   Enable DEBUG logging
    --delay     Seconds between requests   (default: 1.5)
"""

import argparse
import logging
import csv
from pathlib import Path
from dataclasses import asdict

from pmi_analyzer.scraper.link_store import load_links
from pmi_analyzer.scraper.batch_downloader import BatchDownloader
from pmi_analyzer.scraper.batch_parser import BatchParser
from pmi_analyzer.scraper.deduplicator import Deduplicator


DEFAULT_FIELDS = [
    "month", "production", "new_orders", "sales",
    "raw_materials_inv", "final_goods_inv", "input_price",
    "production_expectations", "employment", "exports",
    "delivery_speed", "business_activity",
]


def save_csv(metrics, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=DEFAULT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for m in metrics:
            row = {k: getattr(m, k, "") for k in DEFAULT_FIELDS}
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Download PDFs and parse to CSV")
    parser.add_argument("--links", default="data/report_links.json")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--output", default="data/shamkh_raw.csv")
    parser.add_argument("--no-skip", action="store_true", help="Re-download existing PDFs")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    links_path = Path(args.links)
    if not links_path.exists():
        print(f"ERROR: {links_path} not found. Run phase1_discover_links.py first.")
        return

    # Load links
    links = load_links(links_path)
    print(f"\n=== Phase 2: Processing {len(links)} report links ===")

    # 2a: Download
    print("\n--- 2a: Downloading PDFs ---")
    downloader = BatchDownloader(
        pdf_dir=Path(args.pdf_dir),
        delay=args.delay,
    )
    download_results = downloader.download_all(links, skip_existing=not args.no_skip)
    ok_downloads = sum(1 for _, p in download_results if p and p.exists())
    print(f"    Downloaded: {ok_downloads}/{len([l for l in links if l.pdf_url])}")

    # 2b: Parse
    print("\n--- 2b: Parsing PDFs ---")
    batch_parser = BatchParser()
    raw_metrics = batch_parser.parse_all(download_results)
    print(f"    Parsed: {len(raw_metrics)} records")

    # 2c: Deduplicate
    print("\n--- 2c: Deduplicating ---")
    dedup = Deduplicator()
    clean_metrics = dedup.run(raw_metrics)
    print(f"    Unique months: {len(clean_metrics)}")

    # Save CSV
    output_path = Path(args.output)
    save_csv(clean_metrics, output_path)
    print(f"\n✅ Saved {len(clean_metrics)} records -> {output_path}")

    # Summary
    complete = sum(1 for m in clean_metrics if m.is_complete())
    incomplete = len(clean_metrics) - complete
    print(f"   Complete records   : {complete}")
    print(f"   Incomplete records : {incomplete}")
    print("\nSample (first 3):")
    for m in clean_metrics[:3]:
        print(f"  {m.month:15s} production={m.production} new_orders={m.new_orders}")


if __name__ == "__main__":
    main()
