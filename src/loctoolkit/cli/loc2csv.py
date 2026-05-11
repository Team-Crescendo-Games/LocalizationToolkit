"""`loc2csv` CLI.

Usage:
    loc2csv <input.loc.json> -o <output.csv>

Exit codes:
    0 — wrote CSV
    1 — schema-invalid input (Pass 1 errors)
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from ..csvexport import SchemaInvalidError, export_to_csv


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="loc2csv",
        description="Export a localization JSON file to wide CSV.",
    )
    p.add_argument("input", help="Input .loc.json file")
    p.add_argument("-o", "--output", required=True, help="Output CSV path")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        export_to_csv(args.input, args.output)
    except SchemaInvalidError as e:
        print(f"loc2csv: schema-invalid input: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
