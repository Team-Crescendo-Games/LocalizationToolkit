import json
import subprocess
import sys
from pathlib import Path

import pytest

from loctoolkit.cli.loc2csv import main


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
                "translations": {"en": "Start", "fr": "Commencer"},
            }
        },
    }


def test_writes_csv_and_returns_zero(tmp_path):
    src = _write(tmp_path, _good())
    out = tmp_path / "out.csv"

    rc = main([str(src), "-o", str(out)])

    assert rc == 0
    assert out.exists()
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")


def test_returns_one_on_schema_invalid_input(tmp_path):
    bad = {"formatVersion": "1.0"}
    src = _write(tmp_path, bad)
    out = tmp_path / "out.csv"

    rc = main([str(src), "-o", str(out)])

    assert rc == 1
    assert not out.exists()


def test_requires_output_flag(tmp_path):
    src = _write(tmp_path, _good())

    with pytest.raises(SystemExit) as exc:
        main([str(src)])
    assert exc.value.code != 0


def test_console_script_help():
    result = subprocess.run(
        [sys.executable, "-m", "loctoolkit.cli.loc2csv", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
