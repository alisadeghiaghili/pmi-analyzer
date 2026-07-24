"""Custom exceptions for pmi_analyzer."""


class PMIAnalyzerError(Exception):
    """Base exception for PMI Analyzer."""


class DownloadError(PMIAnalyzerError):
    """Raised when download fails."""


class ParseError(PMIAnalyzerError):
    """Raised when PDF parsing fails."""


# Alias for backwards-compatibility and test clarity
PDFParseError = ParseError


class ValidationError(PMIAnalyzerError):
    """Raised when data validation fails."""


class PlottingError(PMIAnalyzerError):
    """Raised when plotting fails."""


class ConfigError(PMIAnalyzerError):
    """Raised when configuration is invalid."""


class LocaleError(PMIAnalyzerError):
    """Raised when locale is invalid or not found."""
