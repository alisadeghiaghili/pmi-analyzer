"""i18n module for pmi_analyzer."""

from pathlib import Path
from typing import Dict, Optional

LOCALES_DIR = Path(__file__).parent / "locales"
SUPPORTED_LOCALES = ["fa", "en"]
_current_locale = "fa"

_translations: Dict[str, Dict[str, str]] = {}


def _load_po_file(locale: str) -> Dict[str, str]:
    """Parse a .po file and return msgid -> msgstr mapping."""
    po_file = LOCALES_DIR / locale / "locales.po"
    if not po_file.exists():
        return {}
    translations = {}
    current_id = None
    with open(po_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith('msgid "') and line.endswith('"'):
                current_id = line[7:-1]
            elif line.startswith('msgstr "') and line.endswith('"') and current_id:
                msgstr = line[8:-1]
                if current_id and msgstr:
                    translations[current_id] = msgstr
                current_id = None
    return translations


def set_locale(locale: str) -> None:
    """Set global locale."""
    global _current_locale
    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"Invalid locale: {locale}. Supported: {SUPPORTED_LOCALES}")
    _current_locale = locale
    if locale not in _translations:
        _translations[locale] = _load_po_file(locale)


def get_locale() -> str:
    """Get current locale."""
    return _current_locale


def _(message: str, default: Optional[str] = None) -> str:
    """Translate a message using the current locale."""
    if _current_locale not in _translations:
        _translations[_current_locale] = _load_po_file(_current_locale)
    return _translations[_current_locale].get(message, default or message)
