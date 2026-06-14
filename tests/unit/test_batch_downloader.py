"""Unit tests for BatchDownloader."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from pmi_analyzer.scraper.archive_scraper import ReportLink
from pmi_analyzer.scraper.batch_downloader import BatchDownloader


def make_link(pdf_url: str, period_number: int = None, period_label: str = None) -> ReportLink:
    return ReportLink(
        title="test",
        page_url="https://example.com/page",
        pdf_url=pdf_url,
        period_label=period_label,
        period_number=period_number,
    )


class TestLocalPath:
    def test_uses_period_number(self, tmp_path):
        d = BatchDownloader(pdf_dir=tmp_path)
        lnk = make_link("https://x.com/file.pdf", period_number=88)
        assert d._local_path(lnk).name == "shamkh_period_088.pdf"

    def test_uses_period_label_when_no_number(self, tmp_path):
        d = BatchDownloader(pdf_dir=tmp_path)
        lnk = make_link("https://x.com/file.pdf", period_label="\u062f\u06cc 1404")
        name = d._local_path(lnk).name
        assert name.startswith("shamkh_")
        assert ".pdf" in name

    def test_fallback_to_url_filename(self, tmp_path):
        d = BatchDownloader(pdf_dir=tmp_path)
        lnk = make_link("https://x.com/reports/shamkh88.pdf")
        assert d._local_path(lnk).name == "shamkh88.pdf"


class TestDownloadAll:
    def test_skips_existing_files(self, tmp_path):
        d = BatchDownloader(pdf_dir=tmp_path, delay=0)
        lnk = make_link("https://x.com/file.pdf", period_number=1)
        dest = d._local_path(lnk)
        dest.write_bytes(b"%PDF fake")

        results = d.download_all([lnk], skip_existing=True)
        assert results[0][1] == dest

    def test_skips_links_without_pdf_url(self, tmp_path):
        d = BatchDownloader(pdf_dir=tmp_path, delay=0)
        lnk = ReportLink(title="t", page_url="https://x.com", pdf_url=None,
                         period_label=None, period_number=None)
        results = d.download_all([lnk])
        assert results == []

    def test_handles_download_failure_gracefully(self, tmp_path):
        d = BatchDownloader(pdf_dir=tmp_path, delay=0)
        lnk = make_link("https://x.com/bad.pdf", period_number=99)
        d._download = lambda url, dest: None  # simulate failure
        results = d.download_all([lnk], skip_existing=False)
        assert results[0][1] is None
