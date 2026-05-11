"""Wide-CSV exporter for localization files.

UTF-8 with BOM, CRLF line endings, RFC 4180 quoting via the stdlib `csv`
module. One row per string key, one column per canonical locale.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import List

from .locales import LocaleCatalog, load_locales
from .validate import has_errors, validate_file


class SchemaInvalidError(ValueError):
    """Raised when the input file fails Pass 1 (schema) validation."""


_META_COLUMNS = ["key", "description", "max_length", "placeholders"]


def export_to_csv(
    input_path: Path | str,
    output_path: Path | str,
    *,
    catalog: LocaleCatalog | None = None,
) -> None:
    cat = catalog or load_locales()

    issues = validate_file(input_path, schema_only=True, catalog=cat)
    if has_errors(issues):
        raise SchemaInvalidError(
            "; ".join(i.format() for i in issues if i.severity.name == "ERROR")
        )

    data = json.loads(Path(input_path).read_text(encoding="utf-8"))

    rows: List[List[str]] = []
    locale_codes = list(cat.codes)
    header = _META_COLUMNS + locale_codes

    for key in sorted(data["strings"].keys()):
        entry = data["strings"][key]
        translations = entry.get("translations", {}) or {}
        placeholders = entry.get("placeholders", []) or []
        max_length = entry.get("maxLength")

        row = [
            key,
            entry.get("description", ""),
            "" if max_length is None else str(max_length),
            "|".join(placeholders),
        ]
        for code in locale_codes:
            row.append(translations.get(code, ""))
        rows.append(row)

    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        dialect="excel",
        lineterminator="\r\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writerow(header)
    writer.writerows(rows)

    out = Path(output_path)
    out.write_bytes(b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8"))
