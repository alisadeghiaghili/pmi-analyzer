"""Phase 4 - Run monthly update.

Checks for a new Shamkh report and appends it to shamkh_historical.csv.

Usage:
    python scripts/phase4_monthly_update.py
    python scripts/phase4_monthly_update.py --verbose
    python scripts/phase4_monthly_update.py --csv data/shamkh_historical.csv

Typically run via cron or GitHub Actions once a month.
"""

import argparse
import logging
import sys
from pathlib import Path

from pmi_analyzer.updater.monthly_updater import MonthlyUpdater


def main():
    parser = argparse.ArgumentParser(description="Phase 4: Monthly Shamkh auto-updater")
    parser.add_argument("--csv", default=None, help="Path to shamkh_historical.csv")
    parser.add_argument("--pdf-dir", default="data/pdfs", help="Directory for PDFs")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    updater = MonthlyUpdater(
        csv_path=Path(args.csv) if args.csv else None,
        pdf_dir=Path(args.pdf_dir),
        delay=args.delay,
    )

    print("\n=== Phase 4: Monthly Shamkh Update ===")
    result = updater.run()

    if result.is_new:
        m = result.metrics
        print(f"\n\u2705 New record added!")
        print(f"   Month          : {m.month}")
        print(f"   PMI Total      : {m.pmi_total}")
        print(f"   Production     : {m.production}")
        print(f"   New Orders     : {m.new_orders}")
        print(f"   Employment     : {m.employment}")
        sys.exit(0)

    elif result.status == "already_up_to_date":
        print(f"\n\u2139\ufe0f  Already up to date ({result.month})")
        sys.exit(0)

    else:
        print(f"\n\u274c Failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
