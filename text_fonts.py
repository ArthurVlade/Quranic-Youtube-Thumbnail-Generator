"""Thumbnail font loading — picker lists live in font_library.py."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

from font_library import (
    ESSENTIAL_FONT_FILES,
    FONT_DOWNLOADS,
    RECITER_FONTS,
    TITLE_FONTS,
    FontDef,
)

_TITLE_FALLBACK = "Cinzel-Variable.ttf"
_RECITER_FALLBACK = "CormorantGaramond-Variable.ttf"

# Re-export for existing imports
FontChoice = FontDef

_TITLE_BY_ID = {f.id: f for f in TITLE_FONTS}
_RECITER_BY_ID = {f.id: f for f in RECITER_FONTS}


def _fonts_dir() -> Path:
    from app_paths import base_dir
    return base_dir() / "assets" / "fonts"


def _resolve_font_path(filename: str, fallback: str) -> Path | None:
    fonts_dir = _fonts_dir()
    for name in (filename, fallback):
        path = fonts_dir / name
        if path.exists() and path.stat().st_size > 1000:
            return path
    return None


def _system_fallback(size: int, weight: int | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    win = Path("C:/Windows/Fonts")
    for name in ("Cinzel-Variable.ttf", "georgia.ttf", "Georgia.ttf", "segoeui.ttf"):
        bundled = _fonts_dir() / name
        if bundled.exists():
            font = ImageFont.truetype(str(bundled), size=size)
            if weight is not None:
                apply_font_weight(font, weight)
            return font
        system = win / name
        if system.exists():
            return ImageFont.truetype(str(system), size=size)
    arial = win / "arial.ttf"
    if arial.exists():
        return ImageFont.truetype(str(arial), size=size)
    return ImageFont.load_default()


def apply_font_weight(font: ImageFont.FreeTypeFont, weight: int) -> None:
    """Set the wght axis on variable fonts without disturbing opsz/wdth/etc."""
    try:
        axes = font.get_variation_axes()
    except (AttributeError, OSError):
        return
    if not axes:
        return

    tags = [axis.get("tag") or "" for axis in axes]
    if "wght" in tags:
        values: list[float] = []
        for axis in axes:
            tag = axis.get("tag") or ""
            if tag == "wght":
                values.append(float(weight))
            else:
                default = axis.get("default")
                if default is None:
                    lo = float(axis.get("min", weight))
                    hi = float(axis.get("max", weight))
                    default = (lo + hi) / 2
                values.append(float(default))
        font.set_variation_by_axes(values)
    elif len(axes) == 1:
        font.set_variation_by_axes([float(weight)])


def title_font_ids() -> list[str]:
    return [f.id for f in TITLE_FONTS]


def reciter_font_ids() -> list[str]:
    return [f.id for f in RECITER_FONTS]


def title_font_label(font_id: str) -> str:
    return _TITLE_BY_ID.get(font_id, TITLE_FONTS[0]).label


def reciter_font_label(font_id: str) -> str:
    return _RECITER_BY_ID.get(font_id, RECITER_FONTS[0]).label


def resolve_title_font(font_id: str) -> FontDef:
    return _TITLE_BY_ID.get(font_id, TITLE_FONTS[0])


def resolve_reciter_font(font_id: str) -> FontDef:
    return _RECITER_BY_ID.get(font_id, RECITER_FONTS[0])


def load_choice(choice: FontDef, size: int, *, fallback: str) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    px = max(12, int(size * choice.size_scale))
    path = _resolve_font_path(choice.filename, fallback)
    if path is None:
        return _system_fallback(px, choice.weight)
    font = ImageFont.truetype(str(path), size=px)
    if choice.weight is not None:
        apply_font_weight(font, choice.weight)
    return font


def load_title_font(font_id: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_choice(resolve_title_font(font_id), size, fallback=_TITLE_FALLBACK)


def load_reciter_font(font_id: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_choice(resolve_reciter_font(font_id), size, fallback=_RECITER_FALLBACK)
