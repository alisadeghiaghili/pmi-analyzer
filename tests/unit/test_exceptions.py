"""TDD tests for pmi_analyzer/exceptions.py."""

from pmi_analyzer.exceptions import (
    PMIAnalyzerError,
    PDFParseError,
    DownloadError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_pdf_parse_error_is_pmi_error(self):
        assert issubclass(PDFParseError, PMIAnalyzerError)

    def test_download_error_is_pmi_error(self):
        assert issubclass(DownloadError, PMIAnalyzerError)

    def test_validation_error_is_pmi_error(self):
        assert issubclass(ValidationError, PMIAnalyzerError)

    def test_all_are_base_exceptions(self):
        for exc in [PMIAnalyzerError, PDFParseError, DownloadError, ValidationError]:
            assert issubclass(exc, Exception)


class TestExceptionMessages:
    def test_pdf_parse_error_message(self):
        assert "bad pdf" in str(PDFParseError("bad pdf"))

    def test_download_error_message(self):
        assert "timeout" in str(DownloadError("timeout"))

    def test_validation_error_message(self):
        assert "out of range" in str(ValidationError("out of range"))
