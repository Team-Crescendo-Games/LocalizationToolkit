"""Deterministic merge of per-language localization files onto a source.

The source file is the structural authority: keys, descriptions, placeholders,
maxLength, formatVersion, and sourceLocale all come from it. A per-language file
may only contribute non-source-locale translation values. No Claude involved —
this is the "done through a JSON parser" guarantee.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


def _load(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def merge_localizations(
    source_path: Path | str,
    target_paths: Sequence[Path | str],
) -> Tuple[dict, List[str]]:
    """Union per-language translations onto the source.

    Returns (merged_dict, warnings). The merged dict preserves source key order
    and all source metadata; only translation values are added.
    """
    merged = copy.deepcopy(_load(source_path))
    source_locale = merged.get("sourceLocale")
    # setdefault (not get) so src_strings aliases the dict stored in `merged`
    # even when the source omits "strings"; writes must reach the output.
    src_strings: Dict[str, dict] = merged.setdefault("strings", {})
    warnings: List[str] = []
    seen_locale_for: Dict[str, str] = {}  # locale -> file that set it

    for tp in target_paths:
        data = _load(tp)
        name = str(tp)
        for key, entry in data.get("strings", {}).items():
            if key not in src_strings:
                warnings.append(f"{name}: key '{key}' absent from source; skipped")
                continue
            translations = entry.get("translations", {}) or {}
            for locale, text in translations.items():
                if locale == source_locale:
                    continue
                prior = seen_locale_for.get(locale)
                if prior and prior != name:
                    warnings.append(
                        f"locale '{locale}' provided by both {prior} and {name}; "
                        f"using {name} (last-wins)"
                    )
                seen_locale_for[locale] = name
                src_strings[key].setdefault("translations", {})[locale] = text

    return merged, warnings
