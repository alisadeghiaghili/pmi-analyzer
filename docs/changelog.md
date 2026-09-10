# Changelog

All notable changes to PMI Analyzer will be documented in this file.

## [1.1.0] - 2026-08-10

### Added
- Regression suite `tests/unit/test_pdf_extraction_accuracy.py` covering live ICCIMA PDF artefacts
- Golden table snapshots under `tests/fixtures/golden_tables.py` (summary + industry matrices)
- Arabic decimal separator (`U+066B`) support in numeric cell parsing
- Header-aware current-period column selection (`جاری` / `ماه جاری`)
- Detection of wide sector matrices so industry columns never overwrite national metrics

### Fixed
- Month detection no longer treats `دی`/`تیر`/`آذر` inside RTL gibberish (e.g. «می‌دهد») as Jalali months
- `_to_float` rejects double-drawn PDF tokens (`4511..42`, `951.49.2`) instead of returning garbage
- Multi-line cells prefer the first clean decimal (current period) over trailing artefacts
- Percent/delta columns (`12%`) no longer override the level value
- `ShamkhMetrics.validate()` includes `input_price`
- CSV loader tolerates `None` cells without raising `AttributeError`
- `MetricsCalculator` preserves official `pmi_total` in the output DataFrame
- `قیمت محصول` is no longer mapped to `sales`
- Expanded industry keyword list (petrochemical, aerospace, textiles, …)

### Changed
- Cross-tab extraction still prefers aggregate rows, but wide industry matrices are excluded from national `ShamkhMetrics`

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
