"""Custom exceptions for pmi_analyzer."""


class PMIAnalyzerError(Exception):
    """Base exception for PMI Analyzer."""

    pass


class DownloadError(PMIAnalyzerError):
    """Raised when download fails."""

    pass


class ParseError(PMIAnalyzerError):
    """Raised when PDF parsing fails."""

    pass


# Alias for backwards-compatibility and test clarity
PDFParseError = ParseError


class ValidationError(PMIAnalyzerError):
    """Raised when data validation fails."""

    pass


class PlottingError(PMIAnalyzerError):
    """Raised when plotting fails."""

    pass


class ConfigError(PMIAnalyzerError):
    """Raised when configuration is invalid."""

    pass


class LocaleError(PMIAnalyzerError):
    """Raised when locale is invalid or not found."""

    pass
