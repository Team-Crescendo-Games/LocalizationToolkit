from loctoolkit.model import LocalizationFile, StringEntry, parse_localization


def test_parse_minimal_file():
    raw = {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "menu.start": {
                "description": "main menu CTA",
                "translations": {"en": "Start Game"},
            }
        },
    }

    result = parse_localization(raw)

    assert isinstance(result, LocalizationFile)
    assert result.format_version == "1.0"
    assert result.source_locale == "en"
    entry = result.strings["menu.start"]
    assert isinstance(entry, StringEntry)
    assert entry.description == "main menu CTA"
    assert entry.placeholders == ()
    assert entry.max_length is None
    assert entry.translations["en"] == "Start Game"


def test_parse_full_entry():
    raw = {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "hud.score": {
                "description": "hud readout",
                "maxLength": 32,
                "placeholders": ["{score}"],
                "translations": {"en": "Score: {score}", "fr": "Score : {score}"},
            }
        },
    }

    result = parse_localization(raw)
    entry = result.strings["hud.score"]

    assert entry.max_length == 32
    assert entry.placeholders == ("{score}",)
    assert entry.translations == {"en": "Score: {score}", "fr": "Score : {score}"}
