from loctoolkit.validate import Severity, validate_file


def _build(strings: dict, source_locale: str = "en") -> dict:
    return {
        "formatVersion": "1.0",
        "sourceLocale": source_locale,
        "strings": strings,
    }


def test_missing_source_translation_is_error(write_loc):
    data = _build({
        "menu.start": {
            "description": "cta",
            "translations": {"fr": "Commencer"},
        }
    })
    path = write_loc(data)

    issues = validate_file(path)

    assert any(
        i.severity is Severity.ERROR and "source" in i.message.lower()
        for i in issues
    )


def test_missing_target_translation_is_warning(write_loc):
    data = _build({
        "menu.start": {
            "description": "cta",
            "translations": {"en": "Start"},
        }
    })
    path = write_loc(data)

    issues = validate_file(path)

    assert any(
        i.severity is Severity.WARN and "fr" in i.message
        for i in issues
    )


def test_source_translation_exceeds_max_length_is_error(write_loc):
    data = _build({
        "menu.start": {
            "description": "cta",
            "maxLength": 5,
            "translations": {"en": "Start Game"},
        }
    })
    path = write_loc(data)

    issues = validate_file(path)

    assert any(
        i.severity is Severity.ERROR and "maxLength" in i.message and "en" in i.message
        for i in issues
    )


def test_target_translation_exceeds_max_length_is_warning(write_loc):
    data = _build({
        "menu.start": {
            "description": "cta",
            "maxLength": 6,
            "translations": {"en": "Start", "fr": "Commencer"},
        }
    })
    path = write_loc(data)

    issues = validate_file(path)

    assert any(
        i.severity is Severity.WARN and "maxLength" in i.message and "fr" in i.message
        for i in issues
    )


def test_placeholder_mismatch_is_error(write_loc):
    data = _build({
        "hud.score": {
            "description": "score readout",
            "placeholders": ["{score}"],
            "translations": {
                "en": "Score: {score}",
                "fr": "Score",
            },
        }
    })
    path = write_loc(data)

    issues = validate_file(path)

    assert any(
        i.severity is Severity.ERROR and "placeholder" in i.message.lower() and "fr" in i.message
        for i in issues
    )


def test_strict_promotes_warnings_to_errors(write_loc):
    data = _build({
        "menu.start": {
            "description": "cta",
            "translations": {"en": "Start"},
        }
    })
    path = write_loc(data)

    issues = validate_file(path, strict=True)

    assert issues
    assert all(i.severity is Severity.ERROR for i in issues)


def test_source_locale_override(write_loc):
    data = _build({
        "menu.start": {
            "description": "cta",
            "translations": {"en": "Start", "fr": "Commencer"},
        }
    })
    path = write_loc(data)

    issues = validate_file(path, source_locale_override="fr")

    assert not any(
        i.severity is Severity.ERROR and "source" in i.message.lower()
        for i in issues
    )
