import json
import subprocess
import sys
from pathlib import Path

from loctoolkit.cli.locmerge import main


def _write(tmp_path: Path, data: dict, name: str) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _source():
    return {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "menu.start": {"description": "cta", "translations": {"en": "Start Game"}}
        },
    }


def _per_lang(locale: str, text: str):
    d = _source()
    d["strings"]["menu.start"]["translations"][locale] = text
    return d


def test_writes_combined_and_returns_zero(tmp_path):
    src = _write(tmp_path, _source(), "s.loc.json")
    zh = _write(tmp_path, _per_lang("zh-Hans", "开始游戏"), "s.zh-Hans.loc.json")
    out = tmp_path / "combined.loc.json"

    rc = main([str(src), "-t", str(zh), "-o", str(out)])

    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["strings"]["menu.start"]["translations"]["zh-Hans"] == "开始游戏"
    # CJK written literally, not escaped
    assert "开始游戏" in out.read_text(encoding="utf-8")


def test_returns_one_on_schema_invalid_source(tmp_path):
    bad = _write(tmp_path, {"formatVersion": "1.0"}, "bad.loc.json")
    out = tmp_path / "combined.loc.json"

    rc = main([str(bad), "-t", str(bad), "-o", str(out)])

    assert rc == 1
    assert not out.exists()


def test_console_script_help():
    result = subprocess.run(
        [sys.executable, "-m", "loctoolkit.cli.locmerge", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_requires_output_flag(tmp_path):
    src = _write(tmp_path, _source(), "s.loc.json")
    zh = _write(tmp_path, _per_lang("zh-Hans", "开始游戏"), "s.zh-Hans.loc.json")

    try:
        main([str(src), "-t", str(zh)])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("expected SystemExit when -o is omitted")


def test_warnings_go_to_stderr_but_rc_zero(tmp_path, capsys):
    src = _write(tmp_path, _source(), "s.loc.json")
    extra = _per_lang("zh-Hans", "开始游戏")
    extra["strings"]["bogus.key"] = {
        "description": "x",
        "translations": {"en": "x", "zh-Hans": "x"},
    }
    tgt = _write(tmp_path, extra, "s.zh-Hans.loc.json")
    out = tmp_path / "combined.loc.json"

    rc = main([str(src), "-t", str(tgt), "-o", str(out)])

    assert rc == 0
    captured = capsys.readouterr()
    assert "bogus.key" in captured.err
    assert out.exists()
