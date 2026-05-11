import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_sample_csv_matches_golden(tmp_path):
    out = tmp_path / "sample.csv"
    rc = subprocess.run(
        [
            sys.executable,
            "-m",
            "loctoolkit.cli.loc2csv",
            str(REPO_ROOT / "examples" / "sample.loc.json"),
            "-o",
            str(out),
        ],
        check=False,
    ).returncode
    assert rc == 0

    expected = (REPO_ROOT / "examples" / "sample.csv").read_bytes()
    actual = out.read_bytes()
    assert actual == expected, "regenerated CSV diverges from golden"


def test_sample_validates_clean(tmp_path):
    rc = subprocess.run(
        [
            sys.executable,
            "-m",
            "loctoolkit.cli.locvalidate",
            str(REPO_ROOT / "examples" / "sample.loc.json"),
        ],
        check=False,
    ).returncode
    assert rc == 0
