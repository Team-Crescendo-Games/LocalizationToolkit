import json
from pathlib import Path

from loctoolkit.merge import merge_localizations


def _write(tmp_path: Path, data: dict, name: str) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _source():
    return {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "menu.start": {
                "description": "cta",
                "placeholders": [],
                "translations": {"en": "Start Game"},
            },
            "hud.score": {
                "description": "score readout",
                "placeholders": ["{score}"],
                "translations": {"en": "Score: {score}"},
            },
        },
    }


def _per_lang(locale: str, values: dict):
    src = _source()
    for key, text in values.items():
        src["strings"][key]["translations"][locale] = text
    return src


def test_unions_two_locales_onto_source(tmp_path):
    source = _write(tmp_path, _source(), "s.loc.json")
    zh = _write(
        tmp_path,
        _per_lang("zh-Hans", {"menu.start": "开始游戏", "hud.score": "得分：{score}"}),
        "s.zh-Hans.loc.json",
    )
    ja = _write(
        tmp_path,
        _per_lang("ja", {"menu.start": "スタート", "hud.score": "スコア：{score}"}),
        "s.ja.loc.json",
    )

    merged, warnings = merge_localizations(source, [zh, ja])

    t = merged["strings"]["menu.start"]["translations"]
    assert t == {"en": "Start Game", "zh-Hans": "开始游戏", "ja": "スタート"}
    assert merged["strings"]["hud.score"]["translations"]["ja"] == "スコア：{score}"
    # source metadata preserved
    assert merged["formatVersion"] == "1.0"
    assert merged["sourceLocale"] == "en"
    assert merged["strings"]["hud.score"]["placeholders"] == ["{score}"]


def test_does_not_clobber_existing_target_translation(tmp_path):
    # source already has a human zh-Hans for menu.start
    source_data = _source()
    source_data["strings"]["menu.start"]["translations"]["zh-Hans"] = "手动开始"
    source = _write(tmp_path, source_data, "s.loc.json")
    # per-language file only fills the *other* key
    zh = _write(
        tmp_path,
        _per_lang("zh-Hans", {"hud.score": "得分：{score}"}),
        "s.zh-Hans.loc.json",
    )

    merged, warnings = merge_localizations(source, [zh])

    # existing human translation preserved (per-lang file did not include it)
    assert merged["strings"]["menu.start"]["translations"]["zh-Hans"] == "手动开始"
    assert merged["strings"]["hud.score"]["translations"]["zh-Hans"] == "得分：{score}"


def test_unknown_key_in_target_is_warned_and_skipped(tmp_path):
    source = _write(tmp_path, _source(), "s.loc.json")
    extra = _per_lang("zh-Hans", {"menu.start": "开始游戏"})
    extra["strings"]["bogus.key"] = {
        "description": "x",
        "translations": {"en": "x", "zh-Hans": "x"},
    }
    zh = _write(tmp_path, extra, "s.zh-Hans.loc.json")

    merged, warnings = merge_localizations(source, [zh])

    assert "bogus.key" not in merged["strings"]
    assert any("bogus.key" in w for w in warnings)


def test_key_order_follows_source(tmp_path):
    source = _write(tmp_path, _source(), "s.loc.json")
    # target file lists keys in reverse order
    rev = {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "hud.score": {"description": "s", "translations": {"en": "Score: {score}", "ja": "スコア：{score}"}},
            "menu.start": {"description": "c", "translations": {"en": "Start Game", "ja": "スタート"}},
        },
    }
    ja = _write(tmp_path, rev, "s.ja.loc.json")

    merged, _ = merge_localizations(source, [ja])

    assert list(merged["strings"].keys()) == ["menu.start", "hud.score"]


def test_cjk_round_trips_with_ensure_ascii_false(tmp_path):
    source = _write(tmp_path, _source(), "s.loc.json")
    zh = _write(tmp_path, _per_lang("zh-Hans", {"menu.start": "开始游戏"}), "s.zh-Hans.loc.json")

    merged, _ = merge_localizations(source, [zh])
    out = tmp_path / "combined.loc.json"
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    text = out.read_text(encoding="utf-8")
    assert "开始游戏" in text  # literal CJK, not \uXXXX escapes
    assert json.loads(text)["strings"]["menu.start"]["translations"]["zh-Hans"] == "开始游戏"


def test_duplicate_locale_across_files_is_last_wins_with_warning(tmp_path):
    source = _write(tmp_path, _source(), "s.loc.json")
    first = _write(tmp_path, _per_lang("zh-Hans", {"menu.start": "甲"}), "a.zh-Hans.loc.json")
    second = _write(tmp_path, _per_lang("zh-Hans", {"menu.start": "乙"}), "b.zh-Hans.loc.json")

    merged, warnings = merge_localizations(source, [first, second])

    # later file wins
    assert merged["strings"]["menu.start"]["translations"]["zh-Hans"] == "乙"
    assert any("last-wins" in w and "zh-Hans" in w for w in warnings)


def test_source_locale_value_in_target_never_overwrites_source(tmp_path):
    source = _write(tmp_path, _source(), "s.loc.json")
    # a per-language file that (wrongly) carries a different `en` value
    tampered = _per_lang("zh-Hans", {"menu.start": "开始游戏"})
    tampered["strings"]["menu.start"]["translations"]["en"] = "TAMPERED"
    zh = _write(tmp_path, tampered, "s.zh-Hans.loc.json")

    merged, _ = merge_localizations(source, [zh])

    # source `en` is authoritative; the target's `en` is ignored
    assert merged["strings"]["menu.start"]["translations"]["en"] == "Start Game"
    assert merged["strings"]["menu.start"]["translations"]["zh-Hans"] == "开始游戏"
