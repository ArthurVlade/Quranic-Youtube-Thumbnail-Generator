"""UI and thumbnail text localization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from surahs import SURAHS, get_surah
from app_paths import resource_path

_current = "en"
_cache: dict[str, dict[str, Any]] = {}
_bindings: list[tuple[Any, str, str]] = []  # widget, key, attr


def locales_dir() -> Path:
    return resource_path("locales")


def language_codes() -> list[str]:
    codes: list[str] = []
    root = locales_dir()
    if root.exists():
        for path in sorted(root.glob("*.json")):
            codes.append(path.stem)
    return codes or ["en"]


def language_choices() -> list[tuple[str, str, str]]:
    """Return (code, english_name, native_name) sorted by native name."""
    items: list[tuple[str, str, str]] = []
    for code in language_codes():
        data = _load(code)
        meta = data.get("meta", {})
        items.append((
            code,
            meta.get("name_en", code),
            meta.get("name_native", code),
        ))
    return sorted(items, key=lambda x: x[2].lower())


def _load(code: str) -> dict[str, Any]:
    if code in _cache:
        return _cache[code]
    path = locales_dir() / f"{code}.json"
    if not path.exists():
        data = _load("en") if code != "en" else {"ui": {}, "surahs": {}, "reciters": {}, "categories": {}}
        _cache[code] = data
        return data
    data = json.loads(path.read_text(encoding="utf-8"))
    _cache[code] = data
    return data


def set_language(code: str) -> None:
    global _current
    if code not in language_codes():
        code = "en"
    _current = code
    _load(code)


def get_language() -> str:
    return _current


def t(key: str, **kwargs: Any) -> str:
    data = _load(_current)
    ui = data.get("ui", {})
    text = ui.get(key)
    if text is None and _current != "en":
        text = _load("en").get("ui", {}).get(key)
    if text is None:
        text = key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return str(text)


def category_name(key: str) -> str:
    data = _load(_current)
    name = data.get("categories", {}).get(key)
    if name is None and _current != "en":
        name = _load("en").get("categories", {}).get(key)
    return name or key


def surah_title(number: int) -> str:
    surah = get_surah(number)
    if not surah:
        return ""
    data = _load(_current)
    name = data.get("surahs", {}).get(str(number))
    if name is None and _current != "en":
        name = _load("en").get("surahs", {}).get(str(number))
    return name or surah.english


def surah_picker_label(number: int) -> str:
    surah = get_surah(number)
    if not surah:
        return ""
    title = surah_title(number)
    short = title
    if short.lower().startswith("surah "):
        short = short[6:]
    for prefix in (
        "Sure ", "Sourate ", "Sura ", "Surah ", "Сура ", "スーラ ", "수라 ",
        "سورة ", "سورۂ ", "سوره ", "सूरह ", "সূরা ",
    ):
        if short.startswith(prefix):
            short = short[len(prefix):]
            break
    if _current == "zh" and short.startswith("第") and "章 " in short:
        short = short.split("章 ", 1)[1]
    return f"{number}. {short}"


def reciter_name(reciter_id: str, fallback: str) -> str:
    data = _load(_current)
    name = data.get("reciters", {}).get(reciter_id)
    if name is None and _current != "en":
        name = _load("en").get("reciters", {}).get(reciter_id)
    return name or fallback


def bind_widget(widget: Any, key: str, attr: str = "text") -> None:
    _bindings.append((widget, key, attr))


def apply_bindings() -> None:
    for widget, key, attr in _bindings:
        try:
            if hasattr(widget, "configure"):
                widget.configure(**{attr: t(key)})
            elif hasattr(widget, "config"):
                widget.config(**{attr: t(key)})
        except Exception:
            pass


def clear_bindings() -> None:
    _bindings.clear()
