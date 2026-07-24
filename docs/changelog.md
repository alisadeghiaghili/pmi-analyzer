# Changelog

All notable changes to PMI Analyzer will be documented in this file.

## [1.0.0] - 2024-01-01

### Added
- PDF parser with multi-strategy extraction (table, spatial, chart, text fallback)
- RTL Persian text support
- Cross-tab table detection and aggregate row preference
- Export to CSV, SQL, JSON, Excel formats
- Metrics calculator with trends and composite indicators
- CLI interface with `analyse` and `build-historical` commands
- Historical data management with deduplication
- 235 unit and integration tests
- Comprehensive documentation with MkDocs
- Multilingual support (English, Farsi, German)
- GitHub Pages deployment
- Pre-commit hooks for code quality

### Fixed
- Cross-tab row selection (extracts aggregate values instead of industry breakdown)
- Month detection preferring latest year over base year references
- Multi-line cell parsing in summary tables

### Changed
- Updated `_to_float()` to prefer decimal numbers over year-like integers
- Improved label matching with Arabic/Persian normalization
