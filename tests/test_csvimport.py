import json
from pathlib import Path

import pytest

from loctoolkit.csvimport import CsvFormatError, import_from_csv
from loctoolkit.validate import Severity, validate_file


def _write_csv(tmp_path: Path, text: str, name: str = "in.csv", bom: bool = False) -> Path:
    p = tmp_path / name
    data = text.encode("utf-8")
    p.write_bytes(b"\xef\xbb\xbf" + data if bom else data)
    return p


def _run(tmp_path: Path, text: str, **kwargs):
    src = _write_csv(tmp_path, text)
    out = tmp_path / "out.loc.json"
    warnings = import_from_csv(src, out, **kwargs)
    return json.loads(out.read_text(encoding="utf-8")), warnings


def test_parses_sheet_style_header_into_locale_codes(tmp_path):
    data, _ = _run(
        tmp_path,
        "Key,English(en),Chinese (Simplified)(zh-Hans)\r\n"
        "menu.start,Start Game,开始游戏\r\n",
    )

    assert data["formatVersion"] == "1.0"
    assert data["sourceLocale"] == "en"
    assert data["strings"]["menu.start"]["translations"] == {
        "en": "Start Game",
        "zh-Hans": "开始游戏",
    }


def test_parses_bare_locale_code_header(tmp_path):
    data, _ = _run(tmp_path, "key,en,fr\r\nmenu.start,Start,Commencer\r\n")

    assert data["strings"]["menu.start"]["translations"] == {
        "en": "Start",
        "fr": "Commencer",
    }


def test_empty_cell_omits_locale_rather_than_writing_empty_string(tmp_path):
    data, _ = _run(tmp_path, "Key,English(en),French(fr)\r\nmenu.start,Start,\r\n")

    assert data["strings"]["menu.start"]["translations"] == {"en": "Start"}


def test_infers_brace_and_angle_placeholders_from_source_cell(tmp_path):
    data, _ = _run(
        tmp_path,
        "Key,English(en)\r\n"
        'interact.pickup,"Press <action=UI_Exit, compositeId=0> for {prct}% <sprite name=""Sprt"">"\r\n',
    )

    assert data["strings"]["interact.pickup"]["placeholders"] == [
        "<action=UI_Exit, compositeId=0>",
        "{prct}",
        '<sprite name="Sprt">',
    ]


def test_explicit_placeholders_column_overrides_inference(tmp_path):
    data, _ = _run(
        tmp_path,
        "key,placeholders,en\r\nhud.score,{score},Score: {score} of {max}\r\n",
    )

    assert data["strings"]["hud.score"]["placeholders"] == ["{score}"]


def test_omits_placeholders_key_when_none_found(tmp_path):
    data, _ = _run(tmp_path, "Key,English(en)\r\nmenu.start,Start Game\r\n")

    assert "placeholders" not in data["strings"]["menu.start"]


def test_uses_description_column_when_present(tmp_path):
    data, _ = _run(
        tmp_path,
        "key,description,en\r\nmenu.start,Main menu CTA,Start\r\n",
    )

    assert data["strings"]["menu.start"]["description"] == "Main menu CTA"


def test_falls_back_to_key_as_description_and_warns(tmp_path):
    data, warnings = _run(tmp_path, "Key,English(en)\r\nmenu.start,Start\r\n")

    assert data["strings"]["menu.start"]["description"] == "menu.start"
    assert any("description" in w for w in warnings)


def test_parses_max_length_column_as_int_and_omits_when_blank(tmp_path):
    data, _ = _run(
        tmp_path,
        "key,max_length,en\r\nmenu.start,16,Start\r\nmenu.quit,,Quit\r\n",
    )

    assert data["strings"]["menu.start"]["maxLength"] == 16
    assert "maxLength" not in data["strings"]["menu.quit"]


def test_preserves_multiline_quoted_cell(tmp_path):
    data, _ = _run(
        tmp_path,
        'Key,English(en)\r\njournal.page,"line one\r\nline two"\r\n',
    )

    assert data["strings"]["journal.page"]["translations"]["en"] == "line one\nline two"


def test_reads_input_with_utf8_bom(tmp_path):
    src = _write_csv(tmp_path, "Key,English(en)\r\nmenu.start,Start\r\n", bom=True)
    out = tmp_path / "out.loc.json"

    import_from_csv(src, out)

    data = json.loads(out.read_text(encoding="utf-8"))
    assert "menu.start" in data["strings"]


def test_source_locale_override(tmp_path):
    data, _ = _run(
        tmp_path,
        "Key,English(en),French(fr)\r\nmenu.start,Start,Commencer\r\n",
        source_locale="fr",
    )

    assert data["sourceLocale"] == "fr"


def test_placeholders_inferred_from_overridden_source_locale_column(tmp_path):
    data, _ = _run(
        tmp_path,
        "Key,English(en),French(fr)\r\nhud.score,Score,Score : {score}\r\n",
        source_locale="fr",
    )

    assert data["strings"]["hud.score"]["placeholders"] == ["{score}"]


def test_skips_row_with_no_translations_at_all_and_warns(tmp_path):
    data, warnings = _run(tmp_path, "Key,English(en),French(fr)\r\nmenu.start,,\r\n")

    assert data["strings"] == {}
    assert any("menu.start" in w for w in warnings)


def test_warns_when_a_placeholder_repeats_in_source(tmp_path):
    data, warnings = _run(
        tmp_path,
        "Key,English(en)\r\nhud.ratio,{n} of {n}\r\n",
    )

    assert data["strings"]["hud.ratio"]["placeholders"] == ["{n}"]
    assert any("hud.ratio" in w and "repeat" in w.lower() for w in warnings)


def test_warns_and_skips_duplicate_key_row(tmp_path):
    data, warnings = _run(
        tmp_path,
        "Key,English(en)\r\nmenu.start,Start\r\nmenu.start,Begin\r\n",
    )

    assert data["strings"]["menu.start"]["translations"]["en"] == "Start"
    assert any("duplicate" in w.lower() for w in warnings)


def test_unknown_locale_code_in_header_is_fatal(tmp_path):
    with pytest.raises(CsvFormatError, match="klingon"):
        _run(tmp_path, "Key,Klingon(klingon)\r\nmenu.start,nuqneH\r\n")


def test_unrecognised_column_header_is_fatal(tmp_path):
    with pytest.raises(CsvFormatError, match="Reviewer notes"):
        _run(tmp_path, "Key,English(en),Reviewer notes\r\nmenu.start,Start,ok\r\n")


def test_missing_key_column_is_fatal(tmp_path):
    with pytest.raises(CsvFormatError, match="key"):
        _run(tmp_path, "English(en),French(fr)\r\nStart,Commencer\r\n")


def test_no_locale_columns_is_fatal(tmp_path):
    with pytest.raises(CsvFormatError, match="locale"):
        _run(tmp_path, "Key,description\r\nmenu.start,cta\r\n")


def test_invalid_key_pattern_is_fatal(tmp_path):
    with pytest.raises(CsvFormatError, match="menu start"):
        _run(tmp_path, "Key,English(en)\r\nmenu start,Start\r\n")


def test_source_locale_must_have_a_column(tmp_path):
    with pytest.raises(CsvFormatError, match="de"):
        _run(
            tmp_path,
            "Key,English(en)\r\nmenu.start,Start\r\n",
            source_locale="de",
        )


def test_empty_csv_is_fatal(tmp_path):
    with pytest.raises(CsvFormatError):
        _run(tmp_path, "")


def test_output_is_schema_valid(tmp_path):
    src = _write_csv(
        tmp_path,
        "Key,English(en),Japanese(ja)\r\n"
        "menu.start,Start Game,スタート\r\n"
        "hud.score,Score: {score},スコア: {score}\r\n",
    )
    out = tmp_path / "out.loc.json"

    import_from_csv(src, out)

    issues = validate_file(out, schema_only=True)
    assert [i.format() for i in issues if i.severity is Severity.ERROR] == []


def test_output_json_is_written_with_literal_cjk(tmp_path):
    src = _write_csv(tmp_path, "Key,English(en),Japanese(ja)\r\nmenu.start,Start,スタート\r\n")
    out = tmp_path / "out.loc.json"

    import_from_csv(src, out)

    assert "スタート" in out.read_text(encoding="utf-8")


def test_real_memoria_sheet_imports_schema_clean(tmp_path):
    sheet = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "Memoria Wake Localization - UI Text.csv"
    )
    out = tmp_path / "ui-text.loc.json"

    import_from_csv(sheet, out)

    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["strings"]) == 102
    # es-ES / id / pt-BR are fully untranslated in the sheet -> must be absent, not ""
    for entry in data["strings"].values():
        assert "" not in entry["translations"].values()
    assert "pl" not in data["strings"]["accessibilitySettings.colorblind"]["translations"]

    issues = validate_file(out, schema_only=True)
    assert [i.format() for i in issues if i.severity is Severity.ERROR] == []
