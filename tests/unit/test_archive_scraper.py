"""Unit tests for ArchiveScraper (no network calls)."""

from bs4 import BeautifulSoup
from pmi_analyzer.scraper.archive_scraper import ArchiveScraper


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestExtractPeriod:
    scraper = ArchiveScraper()

    def test_month_and_year(self):
        label, num = self.scraper._extract_period("شامخ دی 1404 دوره 88")
        assert "دی" in label
        assert "1404" in label
        assert num == 88

    def test_month_without_year(self):
        label, num = self.scraper._extract_period("شامخ آبانماه")
        assert "آبان" in label
        assert num is None

    def test_no_match(self):
        label, num = self.scraper._extract_period("اخبار اقتصاد")
        assert label is None
        assert num is None


class TestIsShamkhRelated:
    scraper = ArchiveScraper()

    def test_shamkh_in_title(self):
        assert self.scraper._is_shamkh_related("شامخ آبان", "/report") is True

    def test_pmi_in_href(self):
        assert self.scraper._is_shamkh_related("گزارش", "/pmi-report") is True

    def test_unrelated(self):
        assert self.scraper._is_shamkh_related("اخبار بورس", "/stock") is False


class TestFindPdfInElement:
    scraper = ArchiveScraper()

    def test_direct_pdf_anchor(self):
        soup = make_soup('<a href="/files/shamkh.pdf">دانلود</a>')
        result = self.scraper._find_pdf_in_element(soup.find("a"), "https://iccima.ir")
        assert result == "https://iccima.ir/files/shamkh.pdf"

    def test_pdf_nested_in_div(self):
        soup = make_soup(
            "<div><p>توضیح</p>"
            '<a href="https://iccima.ir/wp-content/shamkh1404.pdf">دانلود</a></div>'
        )
        result = self.scraper._find_pdf_in_element(soup.find("div"), "https://iccima.ir")
        assert result == "https://iccima.ir/wp-content/shamkh1404.pdf"

    def test_no_pdf_returns_none(self):
        soup = make_soup('<div><a href="/page">متن</a></div>')
        result = self.scraper._find_pdf_in_element(soup.find("div"), "https://iccima.ir")
        assert result is None


class TestDiscoverAll:
    def _mock_scraper(self, html_otagh: str) -> ArchiveScraper:
        scraper = ArchiveScraper(delay=0)
        calls = {"n": 0}

        def fake_get_soup(url):
            calls["n"] += 1
            if "otaghiran" in url:
                return make_soup(html_otagh) if calls["n"] == 1 else None
            return None

        scraper._get_soup = fake_get_soup
        return scraper

    def test_discovers_shamkh_links(self):
        html = (
            "<article>"
            '<a href="/news/123/%D8%B4%D8%A7%D9%85%D8%AE-%D8%AF%DB%8C-1404">شامخ دی 1404 دوره 88</a>'
            '<a href="/files/shamkh-di1404.pdf">دانلود</a>'
            "</article>"
        )
        links = self._mock_scraper(html).discover_all()
        assert len(links) >= 1
        assert any("دی" in (lnk.period_label or "") for lnk in links)

    def test_deduplicates_same_pdf(self):
        html = (
            '<article><a href="/news/1/%D8%B4%D8%A7%D9%85%D8%AE">شامخ دی 1404</a>'
            '<a href="/files/shamkh.pdf">دانلود</a></article>'
            '<article><a href="/news/2/%D8%B4%D8%A7%D9%85%D8%AE">شامخ دی 1404</a>'
            '<a href="/files/shamkh.pdf">دانلود</a></article>'
        )
        links = self._mock_scraper(html).discover_all()
        pdf_urls = [lnk.pdf_url for lnk in links if lnk.pdf_url]
        assert len(pdf_urls) == len(set(pdf_urls))
