"""Shared pytest fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _minimal_loc(**overrides) -> dict:
    base = {
        "formatVersion": "1.0",
        "sourceLocale": "en",
        "strings": {
            "menu.start": {
                "description": "main menu CTA",
                "translations": {"en": "Start Game"},
            }
        },
    }
    base.update(overrides)
    return base


@pytest.fixture
def write_loc(tmp_path):
    """Write a localization dict to a temp .loc.json file and return its path."""
    def _write(data: dict, name: str = "fixture.loc.json") -> Path:
        p = tmp_path / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p
    return _write


@pytest.fixture
def loc_factory():
    return _minimal_loc
