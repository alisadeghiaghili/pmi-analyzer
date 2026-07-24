# CLI Usage

## Commands

### `analyse`

Analyze Shamkh (PMI) data from a PDF file.

```bash
pmi-analyzer analyse [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--download` | Download latest report from iccima.ir |
| `--pdf PATH` | Path to local PDF file |
| `--output PATH` | Output directory (default: output) |
| `--historical-csv PATH` | Path to historical CSV |
| `--plot` | Generate full sub-indicators chart |
| `--composite` | Generate composite indicators chart |
| `--inventory` | Generate inventory comparison chart |
| `--expectations` | Generate production expectations chart |
| `--labor` | Generate employment & exports chart |

**Examples:**

```bash
# Analyze a local PDF
pmi-analyzer analyse --pdf data/pdfs/report.pdf

# Download and analyze latest
pmi-analyzer analyse --download

# Generate all charts
pmi-analyzer analyse --pdf report.pdf --plot --composite --inventory

# Export with historical data
pmi-analyzer analyse --pdf report.pdf --historical-csv data/shamkh_historical.csv
```

### `build-historical`

Build historical Shamkh database from scratch.

```bash
pmi-analyzer build-historical [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--csv PATH` | Output CSV path |
| `--pdf-dir PATH` | Directory for downloaded PDFs |
| `--delay FLOAT` | Delay between requests (seconds) |
| `--verbose` | Show debug logs |

**Example:**

```bash
# Build full historical database
pmi-analyzer build-historical --csv data/shamkh_historical.csv --verbose
```
