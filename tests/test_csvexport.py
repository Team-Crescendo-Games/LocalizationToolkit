import pytest

from loctoolkit.csvexport import SchemaInvalidError, export_to_csv


def _data():
    return {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "hud.score": {
                "description": "hud readout",
                "maxLength": 32,
                "placeholders": ["{score}"],
                "translations": {
                    "en": "Score: {score}",
                    "fr": "Score : {score}",
                },
            },
            "menu.start": {
                "description": "main menu CTA, with \"quotes\"",
                "translations": {
                    "en": "Start Game",
                    "ja": "スタート",
                },
            },
        },
    }


def test_csv_has_bom_and_crlf(tmp_path, write_loc):
    src = write_loc(_data())
    out = tmp_path / "out.csv"

    export_to_csv(src, out)

    raw = out.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "\r\n" in text


def test_csv_header_columns_are_in_locale_order(tmp_path, write_loc):
    src = write_loc(_data())
    out = tmp_path / "out.csv"

    export_to_csv(src, out)

    text = out.read_bytes().decode("utf-8-sig")
    header = text.splitlines()[0]
    assert header == (
        "key,description,max_length,placeholders,"
        "en,fr,it,de,es-ES,ja,ko,pl,zh-Hans,es-419,zh-Hant,pt-BR,ru"
    )


def test_csv_rows_sorted_by_key_and_blank_for_missing(tmp_path, write_loc):
    src = write_loc(_data())
    out = tmp_path / "out.csv"

    export_to_csv(src, out)

    text = out.read_bytes().decode("utf-8-sig")
    lines = text.splitlines()
    assert lines[1].startswith("hud.score,")
    assert lines[2].startswith("menu.start,")

    menu_row = lines[2]
    # Quoted "menu.start" description contains a comma; need to count cell count
    # via the parser, not naive split. Simpler check: confirm trailing locale cells
    # for missing target locales are empty by looking at the row's last segment.
    assert menu_row.endswith(",")  # last column (ru) is empty


def test_csv_quotes_embedded_quote_per_rfc4180(tmp_path, write_loc):
    src = write_loc(_data())
    out = tmp_path / "out.csv"

    export_to_csv(src, out)

    text = out.read_bytes().decode("utf-8-sig")
    assert "\"main menu CTA, with \"\"quotes\"\"\"" in text


def test_csv_placeholders_pipe_joined(tmp_path, write_loc):
    data = _data()
    data["strings"]["hud.score"]["placeholders"] = ["{score}", "{playerName}"]
    src = write_loc(data)
    out = tmp_path / "out.csv"

    export_to_csv(src, out)

    text = out.read_bytes().decode("utf-8-sig")
    assert "{score}|{playerName}" in text


def test_csv_raises_on_schema_invalid_input(tmp_path):
    p = tmp_path / "bad.loc.json"
    p.write_text('{"formatVersion": "1.0"}', encoding="utf-8")

    with pytest.raises(SchemaInvalidError):
        export_to_csv(p, tmp_path / "out.csv")
