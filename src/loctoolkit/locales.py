"""Loader for the canonical locale catalog (schema/locales.json)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LOCALES_PATH = _REPO_ROOT / "schema" / "locales.json"


@dataclass(frozen=True)
class LocaleCatalog:
    source_default: str
    codes: Tuple[str, ...]
    names: Tuple[str, ...]

    def contains(self, code: str) -> bool:
        return code in self.codes

    def name_for(self, code: str) -> str:
        return self.names[self.codes.index(code)]


def load_locales(path: Path | None = None) -> LocaleCatalog:
    p = path or _LOCALES_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    locales = data["locales"]
    codes = tuple(item["code"] for item in locales)
    names = tuple(item["name"] for item in locales)
    return LocaleCatalog(
        source_default=data["sourceDefault"],
        codes=codes,
        names=names,
    )
