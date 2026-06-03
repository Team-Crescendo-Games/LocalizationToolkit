"""Validation for localization files: schema (Pass 1) and semantic (Pass 2)."""
from __future__ import annotations

import enum
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, List, Optional

from jsonschema import Draft202012Validator

from .locales import LocaleCatalog, load_locales

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _REPO_ROOT / "schema" / "localization.schema.json"


class Severity(enum.Enum):
    ERROR = "ERROR"
    WARN = "WARN"


@dataclass(frozen=True)
class Issue:
    file: str
    key: Optional[str]
    severity: Severity
    message: str

    def format(self) -> str:
        key_part = self.key if self.key else "-"
        return f"{self.file}:{key_part}: {self.severity.value}: {self.message}"


def _load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _schema_pass(data: dict, file: str, catalog: LocaleCatalog) -> List[Issue]:
    issues: List[Issue] = []

    validator = Draft202012Validator(_load_schema())
    for err in validator.iter_errors(data):
        key = None
        path = list(err.absolute_path)
        if len(path) >= 2 and path[0] == "strings":
            candidate = path[1]
            if isinstance(candidate, str):
                key = candidate
        issues.append(
            Issue(file=file, key=key, severity=Severity.ERROR, message=err.message)
        )

    source_locale = data.get("sourceLocale")
    if isinstance(source_locale, str) and not catalog.contains(source_locale):
        issues.append(
            Issue(
                file=file,
                key=None,
                severity=Severity.ERROR,
                message=f"sourceLocale '{source_locale}' is not in the canonical locale list",
            )
        )

    strings = data.get("strings")
    if isinstance(strings, dict):
        for key, entry in strings.items():
            if not isinstance(entry, dict):
                continue
            translations = entry.get("translations")
            if not isinstance(translations, dict):
                continue
            for code in translations.keys():
                if not catalog.contains(code):
                    issues.append(
                        Issue(
                            file=file,
                            key=key,
                            severity=Severity.ERROR,
                            message=f"unknown locale code '{code}' in translations",
                        )
                    )

    return issues


def _placeholders_match(text: str, expected: List[str]) -> bool:
    """Multiset equality: each declared placeholder must appear exactly the
    declared number of times, and no other placeholders may exist in the text.

    For now we only check the declared set is fully present; detection of
    extra placeholder-shaped tokens not in the declared set is out of scope
    (would require defining what "placeholder-shaped" means).
    """
    for token in expected:
        declared_count = expected.count(token)
        if text.count(token) != declared_count:
            return False
    return True


def _semantic_pass(
    data: dict,
    file: str,
    catalog: LocaleCatalog,
    source_locale: str,
) -> List[Issue]:
    issues: List[Issue] = []

    strings = data.get("strings", {})
    for key, entry in strings.items():
        translations: dict = entry.get("translations", {})
        placeholders = list(entry.get("placeholders", []) or [])
        max_length = entry.get("maxLength")

        if source_locale not in translations:
            issues.append(
                Issue(
                    file=file,
                    key=key,
                    severity=Severity.ERROR,
                    message=f"missing source-locale translation '{source_locale}'",
                )
            )

        for code in catalog.codes:
            if code == source_locale:
                continue
            if code not in translations:
                issues.append(
                    Issue(
                        file=file,
                        key=key,
                        severity=Severity.WARN,
                        message=f"missing translation for target locale '{code}'",
                    )
                )

        if isinstance(max_length, int):
            for code, text in translations.items():
                if not isinstance(text, str):
                    continue
                if len(text) > max_length:
                    severity = Severity.ERROR if code == source_locale else Severity.WARN
                    issues.append(
                        Issue(
                            file=file,
                            key=key,
                            severity=severity,
                            message=(
                                f"translation '{code}' length {len(text)} exceeds maxLength "
                                f"{max_length}"
                            ),
                        )
                    )

        for code, text in translations.items():
            if not isinstance(text, str):
                continue
            if text == "":
                issues.append(
                    Issue(
                        file=file,
                        key=key,
                        severity=Severity.WARN,
                        message=f"empty translation for locale '{code}'",
                    )
                )
                continue
            if not _placeholders_match(text, placeholders):
                issues.append(
                    Issue(
                        file=file,
                        key=key,
                        severity=Severity.ERROR,
                        message=(
                            f"placeholder mismatch in '{code}': expected {placeholders}"
                        ),
                    )
                )

    return issues


def validate_file(
    path: Path | str,
    *,
    strict: bool = False,
    source_locale_override: Optional[str] = None,
    schema_only: bool = False,
    catalog: Optional[LocaleCatalog] = None,
) -> List[Issue]:
    """Validate one localization file. Returns a list of issues (empty = clean).

    `schema_only=True` runs only Pass 1 (used by `loc2csv`, which treats
    semantic warnings as non-blocking).
    """
    p = Path(path)
    file_str = str(p)
    cat = catalog or load_locales()

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [Issue(file=file_str, key=None, severity=Severity.ERROR, message=f"invalid JSON: {e}")]
    except OSError as e:
        return [Issue(file=file_str, key=None, severity=Severity.ERROR, message=f"cannot read file: {e}")]

    if not isinstance(data, dict):
        return [Issue(file=file_str, key=None, severity=Severity.ERROR, message="top-level value must be a JSON object")]

    issues = _schema_pass(data, file=file_str, catalog=cat)

    if not schema_only and not has_errors(issues):
        source_locale = source_locale_override or data.get("sourceLocale", cat.source_default)
        issues.extend(_semantic_pass(data, file=file_str, catalog=cat, source_locale=source_locale))

    if strict:
        issues = [
            replace(i, severity=Severity.ERROR) if i.severity is Severity.WARN else i
            for i in issues
        ]

    return issues


def has_errors(issues: Iterable[Issue]) -> bool:
    return any(i.severity is Severity.ERROR for i in issues)
