"""`csv2loc` CLI — import a wide CSV (spreadsheet export) into localization JSON.

Usage:
    csv2loc <input.csv> -o <output.loc.json> [--source-locale CODE]

Exit codes:
    0 — wrote JSON
    1 — CSV could not be interpreted (header or key problem)
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from ..csvimport import CsvFormatError, import_from_csv


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="csv2loc",
        description="Import a wide CSV into a localization JSON file.",
    )
    p.add_argument("input", help="Input CSV file")
    p.add_argument("-o", "--output", required=True, help="Output .loc.json path")
    p.add_argument(
        "--source-locale",
        help="Locale code to treat as the source column (default: catalog sourceDefault)",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        warnings = import_from_csv(
            args.input, args.output, source_locale=args.source_locale
        )
    except CsvFormatError as e:
        print(f"csv2loc: {e}", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"csv2loc: warning: {w}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
