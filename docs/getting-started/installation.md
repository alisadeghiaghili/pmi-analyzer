# Installation

## Requirements

- Python 3.9 or higher
- pip or uv package manager

## Install from PyPI

```bash
pip install pmi-analyzer
```

### Optional Dependencies

For Excel export support:

```bash
pip install pmi-analyzer[excel]
```

For documentation development:

```bash
pip install pmi-analyzer[docs]
```

For development:

```bash
pip install pmi-analyzer[dev]
```

## Install from Source

```bash
git clone https://github.com/alisadeghiaghili/pmi-analyzer.git
cd pmi-analyzer
pip install -e .
```

## Verify Installation

```bash
python -c "from pmi_analyzer.parser.pdf_parser import PDFParser; print('OK')"
```

## System Dependencies

No system dependencies required. All dependencies are pure Python.
