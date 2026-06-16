"""`locmerge` CLI — deterministically union per-language files into one file.

Usage:
    locmerge <source.loc.json> -t f1.loc.json f2.loc.json -o <combined.loc.json>

Exit codes:
    0 — wrote combined file
    1 — schema-invalid source input (Pass 1 errors)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from ..merge import merge_localizations
from ..validate import Severity, has_errors, validate_file


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="locmerge",
        description="Merge per-language localization files into one combined file.",
    )
    p.add_argument("source", help="Source .loc.json file (structural authority)")
    p.add_argument(
        "-t",
        "--targets",
        nargs="+",
        required=True,
        help="One or more per-language .loc.json files to merge in",
    )
    p.add_argument("-o", "--output", required=True, help="Output combined .loc.json path")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    issues = validate_file(args.source, schema_only=True)
    if has_errors(issues):
        msg = "; ".join(i.format() for i in issues if i.severity is Severity.ERROR)
        print(f"locmerge: schema-invalid source: {msg}", file=sys.stderr)
        return 1

    merged, warnings = merge_localizations(args.source, args.targets)
    for w in warnings:
        print(f"locmerge: warning: {w}", file=sys.stderr)

    Path(args.output).write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
