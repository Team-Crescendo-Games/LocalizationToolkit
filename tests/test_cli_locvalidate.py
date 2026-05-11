import json
import subprocess
import sys
from pathlib import Path

from loctoolkit.cli.locvalidate import main


def _write(tmp_path: Path, data: dict, name: str = "f.loc.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _good():
    return {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "menu.start": {
                "description": "cta",
                "translations": {"en": "Start"},
            }
        },
    }


def test_returns_zero_when_valid(tmp_path):
    p = _write(tmp_path, _good())

    rc = main([str(p)])

    assert rc == 0


def test_returns_one_when_errors(tmp_path):
    bad = _good()
    bad["strings"]["menu.start"]["translations"] = {"fr": "Commencer"}
    p = _write(tmp_path, bad)

    rc = main([str(p)])

    assert rc == 1


def test_warnings_alone_return_zero(tmp_path):
    p = _write(tmp_path, _good())

    rc = main([str(p)])

    assert rc == 0


def test_strict_promotes_warnings_to_errors(tmp_path):
    p = _write(tmp_path, _good())

    rc = main([str(p), "--strict"])

    assert rc == 1


def test_source_locale_override(tmp_path):
    data = _good()
    data["strings"]["menu.start"]["translations"] = {"en": "Start", "fr": "Commencer"}
    p = _write(tmp_path, data)

    rc = main([str(p), "--source-locale", "fr"])

    assert rc == 0


def test_multiple_files_all_clean(tmp_path):
    p1 = _write(tmp_path, _good(), "a.loc.json")
    p2 = _write(tmp_path, _good(), "b.loc.json")

    rc = main([str(p1), str(p2)])

    assert rc == 0


def test_console_script_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "loctoolkit.cli.locvalidate", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
