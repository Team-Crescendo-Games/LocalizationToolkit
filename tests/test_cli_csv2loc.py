import json
import subprocess
import sys
from pathlib import Path

import pytest

from loctoolkit.cli.csv2loc import main


def _write(tmp_path: Path, text: str, name: str = "in.csv") -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_writes_json_and_returns_zero(tmp_path):
    src = _write(tmp_path, "Key,English(en)\r\nmenu.start,Start\r\n")
    out = tmp_path / "out.loc.json"

    rc = main([str(src), "-o", str(out)])

    assert rc == 0
    assert json.loads(out.read_text(encoding="utf-8"))["strings"]["menu.start"]


def test_returns_one_on_malformed_header(tmp_path):
    src = _write(tmp_path, "English(en),French(fr)\r\nStart,Commencer\r\n")
    out = tmp_path / "out.loc.json"

    rc = main([str(src), "-o", str(out)])

    assert rc == 1
    assert not out.exists()


def test_warnings_go_to_stderr(tmp_path, capsys):
    src = _write(tmp_path, "Key,English(en)\r\nmenu.start,Start\r\n")
    out = tmp_path / "out.loc.json"

    main([str(src), "-o", str(out)])

    assert "csv2loc: warning:" in capsys.readouterr().err


def test_source_locale_flag(tmp_path):
    src = _write(tmp_path, "Key,English(en),French(fr)\r\nmenu.start,Start,Commencer\r\n")
    out = tmp_path / "out.loc.json"

    main([str(src), "-o", str(out), "--source-locale", "fr"])

    assert json.loads(out.read_text(encoding="utf-8"))["sourceLocale"] == "fr"


def test_requires_output_flag(tmp_path):
    src = _write(tmp_path, "Key,English(en)\r\nmenu.start,Start\r\n")

    with pytest.raises(SystemExit) as exc:
        main([str(src)])
    assert exc.value.code != 0


def test_console_script_help():
    result = subprocess.run(
        [sys.executable, "-m", "loctoolkit.cli.csv2loc", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
