"""Wide-CSV importer: spreadsheet export -> localization JSON.

Accepts both header dialects:

- sheet style, name plus parenthesised code — ``Chinese (Simplified)(zh-Hans)``
- bare canonical codes, as emitted by ``loc2csv`` — ``zh-Hans``

Optional meta columns (``description``, ``max_length``, ``placeholders``) are
picked up when present, so a ``loc2csv`` export round-trips. Blank locale cells
are omitted from ``translations`` rather than written as ``""`` — an absent
locale is what marks a string as still needing translation.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .locales import LocaleCatalog, load_locales


class CsvFormatError(ValueError):
    """Raised when the CSV cannot be interpreted as a localization table."""


_KEY_HEADERS = {"key"}
_DESCRIPTION_HEADERS = {"description"}
_MAX_LENGTH_HEADERS = {"max_length", "maxlength", "max length"}
_PLACEHOLDER_HEADERS = {"placeholders"}

# Mirrors the propertyNames pattern in schema/localization.schema.json.
_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+$")

_SHEET_HEADER = re.compile(r"^(?P<name>.*)\((?P<code>[^()]+)\)$")
_PLACEHOLDER_TOKEN = re.compile(r"\{[^{}]*\}|<[^<>]+>")


def _normalize_cell(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def _extract_placeholders(text: str, key: str, warnings: List[str]) -> List[str]:
    ordered: List[str] = []
    for match in _PLACEHOLDER_TOKEN.finditer(text):
        token = match.group(0)
        if token in ordered:
            warnings.append(
                f"key '{key}': placeholder '{token}' repeats in the source text; "
                f"declared once (schema requires unique items)"
            )
            continue
        ordered.append(token)
    return ordered


class _Header:
    def __init__(self, raw: List[str], catalog: LocaleCatalog):
        self.key_index: Optional[int] = None
        self.description_index: Optional[int] = None
        self.max_length_index: Optional[int] = None
        self.placeholders_index: Optional[int] = None
        self.locale_indices: Dict[str, int] = {}

        for index, cell in enumerate(raw):
            label = cell.strip()
            folded = label.lower()

            if folded in _KEY_HEADERS and self.key_index is None:
                self.key_index = index
            elif folded in _DESCRIPTION_HEADERS:
                self.description_index = index
            elif folded in _MAX_LENGTH_HEADERS:
                self.max_length_index = index
            elif folded in _PLACEHOLDER_HEADERS:
                self.placeholders_index = index
            else:
                self.locale_indices[self._locale_code(label, catalog)] = index

        if self.key_index is None:
            raise CsvFormatError("no 'key' column found in the header row")
        if not self.locale_indices:
            raise CsvFormatError("no locale columns found in the header row")

    @staticmethod
    def _locale_code(label: str, catalog: LocaleCatalog) -> str:
        match = _SHEET_HEADER.match(label)
        if match:
            code = match.group("code").strip()
            if not catalog.contains(code):
                raise CsvFormatError(
                    f"column '{label}' names locale code '{code}', "
                    f"which is not in the canonical locale list"
                )
            return code
        if catalog.contains(label):
            return label
        raise CsvFormatError(f"unrecognised column header '{label}'")


def import_from_csv(
    input_path: Path | str,
    output_path: Path | str,
    *,
    source_locale: Optional[str] = None,
    catalog: LocaleCatalog | None = None,
) -> List[str]:
    """Convert a wide CSV into a localization JSON file.

    Returns a list of non-fatal warnings. Raises `CsvFormatError` on a header or
    key the importer cannot interpret; no output is written in that case.
    """
    cat = catalog or load_locales()
    src_locale = source_locale or cat.source_default
    if not cat.contains(src_locale):
        raise CsvFormatError(
            f"source locale '{src_locale}' is not in the canonical locale list"
        )

    with Path(input_path).open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        raise CsvFormatError("CSV is empty: no header row")

    header = _Header(rows[0], cat)
    if src_locale not in header.locale_indices:
        raise CsvFormatError(f"no column for source locale '{src_locale}'")

    warnings: List[str] = []
    strings: Dict[str, dict] = {}
    missing_descriptions = 0

    def cell(row: List[str], index: Optional[int]) -> str:
        if index is None or index >= len(row):
            return ""
        return _normalize_cell(row[index])

    for line_number, row in enumerate(rows[1:], start=2):
        key = cell(row, header.key_index)
        if not key and not any(c.strip() for c in row):
            continue
        if not _KEY_PATTERN.match(key):
            raise CsvFormatError(
                f"line {line_number}: key '{key}' does not match the schema key pattern"
            )
        if key in strings:
            warnings.append(f"line {line_number}: duplicate key '{key}'; kept the first row")
            continue

        translations = {
            code: text
            for code, index in header.locale_indices.items()
            if (text := cell(row, index))
        }
        if not translations:
            warnings.append(f"line {line_number}: key '{key}' has no translations; skipped")
            continue

        description = cell(row, header.description_index)
        if not description:
            description = key
            missing_descriptions += 1

        entry: dict = {"description": description}

        max_length = cell(row, header.max_length_index)
        if max_length:
            try:
                entry["maxLength"] = int(max_length)
            except ValueError:
                warnings.append(
                    f"line {line_number}: key '{key}' has non-integer max_length "
                    f"'{max_length}'; omitted"
                )

        declared = cell(row, header.placeholders_index)
        if declared:
            placeholders = [t for t in declared.split("|") if t]
        else:
            placeholders = _extract_placeholders(
                translations.get(src_locale, ""), key, warnings
            )
        if placeholders:
            entry["placeholders"] = placeholders

        entry["translations"] = translations
        strings[key] = entry

    if missing_descriptions:
        warnings.append(
            f"{missing_descriptions} row(s) had no description; used the key itself. "
            f"Add a 'description' column for better translation quality."
        )

    data = {
        "formatVersion": "1.0",
        "sourceLocale": src_locale,
        "strings": strings,
    }
    Path(output_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return warnings
