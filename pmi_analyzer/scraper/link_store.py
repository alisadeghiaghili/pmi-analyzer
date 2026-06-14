"""Persist and load discovered report links to/from JSON."""

import json
from pathlib import Path
from typing import List

from pmi_analyzer.scraper.archive_scraper import ReportLink

DEFAULT_PATH = Path("data/report_links.json")


def save_links(links: List[ReportLink], path: Path = DEFAULT_PATH) -> None:
    """Save ReportLink list to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "title": lnk.title,
            "page_url": lnk.page_url,
            "pdf_url": lnk.pdf_url,
            "period_label": lnk.period_label,
            "period_number": lnk.period_number,
        }
        for lnk in links
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_links(path: Path = DEFAULT_PATH) -> List[ReportLink]:
    """Load ReportLink list from JSON."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    return [
        ReportLink(
            title=r["title"],
            page_url=r["page_url"],
            pdf_url=r.get("pdf_url"),
            period_label=r.get("period_label"),
            period_number=r.get("period_number"),
        )
        for r in records
    ]
