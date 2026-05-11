from loctoolkit.locales import load_locales, LocaleCatalog


def test_load_locales_returns_catalog_with_expected_codes():
    catalog = load_locales()

    assert isinstance(catalog, LocaleCatalog)
    assert catalog.source_default == "en"
    assert catalog.codes[0] == "en"
    assert "zh-Hans" in catalog.codes
    assert "ru" in catalog.codes
    assert len(catalog.codes) == 13


def test_locale_catalog_membership_and_order():
    catalog = load_locales()

    assert catalog.contains("fr")
    assert not catalog.contains("xx")
    assert catalog.codes.index("en") < catalog.codes.index("fr")
    assert catalog.codes.index("fr") < catalog.codes.index("it")


def test_locale_catalog_name_lookup():
    catalog = load_locales()

    assert catalog.name_for("en") == "English"
    assert catalog.name_for("zh-Hans") == "Simplified Chinese"
