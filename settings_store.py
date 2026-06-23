"""Persist and restore the user's last-used UI settings between sessions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app_paths import base_dir

_SETTINGS_PATH = base_dir() / "data" / "settings.json"


def load_settings() -> dict[str, Any]:
    try:
        if _SETTINGS_PATH.exists():
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_settings(data: dict[str, Any]) -> None:
    try:
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass
