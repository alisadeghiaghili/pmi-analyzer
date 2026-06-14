"""Unit tests for MonthlyUpdater."""

from pathlib import Path
from unittest.mock import patch


from pmi_analyzer.scraper.archive_scraper import ReportLink
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.updater.monthly_updater import MonthlyUpdater, UpdateResult


def make_link(period_label="\u062f\u06cc 1404", period_number=88, pdf_url="https://x.com/f.pdf"):
    return ReportLink(
        title="\u0634\u0627\u0645\u062e",
        page_url="https://x.com/page",
        pdf_url=pdf_url,
        period_label=period_label,
        period_number=period_number,
    )


def make_metrics(month="\u062f\u06cc 1404", pmi_total=46.6):
    return ShamkhMetrics(month=month, pmi_total=pmi_total)


class TestUpdateResult:
    def test_is_new_true(self):
        r = UpdateResult(status="new", month="\u062f\u06cc 1404")
        assert r.is_new is True

    def test_is_new_false(self):
        r = UpdateResult(status="already_up_to_date", month="\u062f\u06cc 1404")
        assert r.is_new is False


class TestMonthlyUpdater:
    def _make_updater(self, tmp_path: Path) -> MonthlyUpdater:
        updater = MonthlyUpdater(csv_path=tmp_path / "shamkh.csv", pdf_dir=tmp_path / "pdfs")
        return updater

    def test_returns_failed_when_no_links(self, tmp_path):
        updater = self._make_updater(tmp_path)
        updater._get_latest_link = lambda: None
        result = updater.run()
        assert result.status == "failed"

    def test_returns_already_up_to_date(self, tmp_path):
        updater = self._make_updater(tmp_path)
        link = make_link(period_label="\u062f\u06cc 1404")
        updater._get_latest_link = lambda: link
        updater._existing_months = lambda: {"\u062f\u06cc 1404"}
        result = updater.run()
        assert result.status == "already_up_to_date"

    def test_returns_failed_on_download_failure(self, tmp_path):
        updater = self._make_updater(tmp_path)
        link = make_link()
        updater._get_latest_link = lambda: link
        updater._existing_months = lambda: set()
        updater._downloader.download_all = lambda links, **kw: [(links[0], None)]
        result = updater.run()
        assert result.status == "failed"
        assert "Download failed" in result.error

    def test_returns_new_on_success(self, tmp_path):
        updater = self._make_updater(tmp_path)
        link = make_link()
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"%PDF")
        metrics = make_metrics()

        updater._get_latest_link = lambda: link
        updater._existing_months = lambda: set()
        updater._downloader.download_all = lambda links, **kw: [(links[0], fake_pdf)]
        updater._parser.parse_single = lambda path, month=None: metrics
        updater._csv_path = tmp_path / "shamkh.csv"

        # patch append_record to avoid file ops
        with patch("pmi_analyzer.updater.monthly_updater.append_record") as mock_append:
            result = updater.run()
            mock_append.assert_called_once()

        assert result.status == "new"
        assert result.metrics == metrics
