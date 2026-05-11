"""`locvalidate` CLI.

Usage:
    locvalidate <file.loc.json>... [--strict] [--source-locale CODE]

Exit codes:
    0 — no errors (warnings allowed unless --strict)
    1 — at least one error
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from ..validate import Severity, has_errors, validate_file


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="locvalidate",
        description="Validate localization JSON files (schema + semantic).",
    )
    p.add_argument("files", nargs="+", help="One or more .loc.json files to validate")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Promote warnings to errors (non-zero exit on any warning).",
    )
    p.add_argument(
        "--source-locale",
        dest="source_locale",
        default=None,
        help="Override the file's sourceLocale for this run.",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    any_errors = False
    for path in args.files:
        issues = validate_file(
            path,
            strict=args.strict,
            source_locale_override=args.source_locale,
        )
        for issue in issues:
            stream = sys.stderr if issue.severity is Severity.ERROR else sys.stdout
            print(issue.format(), file=stream)
        if has_errors(issues):
            any_errors = True

    return 1 if any_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
