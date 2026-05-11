"""Dataclasses representing a parsed localization file."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple


@dataclass(frozen=True)
class StringEntry:
    description: str
    translations: Mapping[str, str]
    placeholders: Tuple[str, ...] = ()
    max_length: int | None = None


@dataclass(frozen=True)
class LocalizationFile:
    format_version: str
    source_locale: str
    strings: Mapping[str, StringEntry]


def parse_localization(raw: Dict[str, Any]) -> LocalizationFile:
    strings: Dict[str, StringEntry] = {}
    for key, entry_raw in raw.get("strings", {}).items():
        strings[key] = StringEntry(
            description=entry_raw["description"],
            translations=dict(entry_raw["translations"]),
            placeholders=tuple(entry_raw.get("placeholders", []) or ()),
            max_length=entry_raw.get("maxLength"),
        )
    return LocalizationFile(
        format_version=raw["formatVersion"],
        source_locale=raw["sourceLocale"],
        strings=strings,
    )
