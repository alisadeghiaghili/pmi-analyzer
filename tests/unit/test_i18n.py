"""Tests for i18n module."""

import pytest
from pmi_analyzer.i18n import _, set_locale, get_locale


def test_default_locale_is_fa():
    assert get_locale() == "fa"


def test_set_locale_en():
    set_locale("en")
    assert get_locale() == "en"
    set_locale("fa")  # reset


def test_translate_fa():
    set_locale("fa")
    assert _("Production") == "تولید"
    assert _("Employment") == "اشتغال"
    assert _("Exports") == "صادرات"


def test_translate_en():
    set_locale("en")
    assert _("Production") == "Production"
    assert _("Employment") == "Employment"
    assert _("رکود") == "Recession"
    set_locale("fa")  # reset


def test_invalid_locale_raises():
    with pytest.raises(ValueError):
        set_locale("de")


def test_missing_key_returns_original():
    set_locale("fa")
    assert _("NonExistentKey_xyz") == "NonExistentKey_xyz"
