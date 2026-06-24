"""Pick fonts and display forms for localized thumbnail text."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from PIL import ImageFont

_PLACEHOLDER_RE = re.compile(r"\{[^}]+\}")

# Google Translate / deep-translator target codes
GOOGLE_LANG: dict[str, str] = {
    "en": "en",
    "de": "de",
    "fr": "fr",
    "es": "es",
    "pt": "pt",
    "it": "it",
    "nl": "nl",
    "pl": "pl",
    "ro": "ro",
    "cs": "cs",
    "sk": "sk",
    "hu": "hu",
    "bg": "bg",
    "hr": "hr",
    "sl": "sl",
    "et": "et",
    "lv": "lv",
    "lt": "lt",
    "fi": "fi",
    "sv": "sv",
    "da": "da",
    "el": "el",
    "ga": "ga",
    "mt": "mt",
    "uk": "uk",
    "ru": "ru",
    "tr": "tr",
    "no": "no",
    "is": "is",
    "ca": "ca",
    "sq": "sq",
    "sr": "sr",
    "bs": "bs",
    "mk": "mk",
    "be": "be",
    "lb": "lb",
    "cy": "cy",
    "ur": "ur",
    "bn": "bn",
    "hi": "hi",
    "zh": "zh-CN",
    "ja": "ja",
    "ko": "ko",
    "fa": "fa",
    "id": "id",
    "ms": "ms",
    "ar": "ar",
}


def google_target(code: str) -> str:
    return GOOGLE_LANG.get(code, code)


def _fonts_dir() -> Path:
    from app_paths import base_dir
    return base_dir() / "assets" / "fonts"


def _win_fonts() -> Path:
    return Path("C:/Windows/Fonts")


def _load_truetype(path: Path, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if not path.exists():
        return ImageFont.load_default()
    font = ImageFont.truetype(str(path), size=size)
    if weight is not None:
        from text_fonts import apply_font_weight
        apply_font_weight(font, weight)
    return font


def _first_existing(names: list[str], size: int, weight: int | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in names:
        for ext in (".ttf", ".otf", ".TTF", ".OTF", ".ttc"):
            bundled = _fonts_dir() / f"{name}{ext}"
            if bundled.exists():
                return _load_truetype(bundled, size, weight)
            system = _win_fonts() / f"{name}{ext}"
            if system.exists():
                return ImageFont.truetype(str(system), size=size)
    return ImageFont.load_default()


def _char_script(ch: str) -> str:
    if ch.isdigit() or ch in " .,:;!?·…—–-'\"()[]{}+/\\|&@#%":
        return "neutral"
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return "other"
    if "CJK UNIFIED" in name or "CJK COMPATIBILITY" in name:
        return "cjk"
    if "HIRAGANA" in name or "KATAKANA" in name:
        return "japanese"
    if "HANGUL" in name:
        return "korean"
    if "ARABIC" in name or "HEBREW" in name:
        return "arabic"
    if "DEVANAGARI" in name:
        return "devanagari"
    if "BENGALI" in name:
        return "bengali"
    if "CYRILLIC" in name:
        return "cyrillic"
    if "GREEK" in name:
        return "greek"
    if "LATIN" in name:
        return "latin"
    return "other"


def scripts_in_text(text: str) -> set[str]:
    return {_char_script(c) for c in text if _char_script(c) not in {"neutral", "other"}}


def primary_script(text: str) -> str:
    scripts = scripts_in_text(text)
    for preferred in ("cjk", "japanese", "korean", "arabic", "devanagari", "bengali", "cyrillic", "greek", "latin"):
        if preferred in scripts:
            return preferred
    counts: dict[str, int] = {}
    for ch in text:
        script = _char_script(ch)
        if script == "neutral":
            continue
        counts[script] = counts.get(script, 0) + 1
    if not counts:
        return "latin"
    return max(counts, key=counts.get)


def display_text(text: str) -> str:
    """Uppercase Latin titles; leave CJK/Arabic/etc. unchanged."""
    t = text.strip()
    if not t:
        return ""
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return t
    latin = sum(1 for c in letters if _char_script(c) == "latin")
    if latin >= len(letters) * 0.6:
        return t.upper()
    return t


def shape_text(text: str) -> str:
    """Prepare user-facing thumbnail line (RTL shaping or Latin uppercasing)."""
    t = text.strip()
    if not t:
        return ""
    if primary_script(t) == "arabic":
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            return get_display(arabic_reshaper.reshape(t))
        except Exception:
            return t
    return display_text(t)


def font_for_text(
    text: str,
    size: int,
    *,
    role: str = "title",
    font_id: str | None = None,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Return a font that can render the dominant script in *text*."""
    script = primary_script(text)
    weight = 400 if role == "title" else 300

    if script == "cjk":
        return _first_existing(
            ["NotoSansSC-Variable", "NotoSansSC[wght]", "NotoSansSC-Regular", "msyh", "msyhbd", "simhei"],
            size,
            weight,
        )
    if script == "japanese":
        return _first_existing(
            ["NotoSansJP-Variable", "NotoSansJP[wght]", "NotoSansJP-Regular", "YuGothM", "YuGothR", "meiryo"],
            size,
            weight,
        )
    if script == "korean":
        return _first_existing(
            ["NotoSansKR-Variable", "NotoSansKR[wght]", "NotoSansKR-Regular", "malgun", "malgunsl"],
            size,
            weight,
        )
    if script == "arabic":
        return _first_existing(
            ["NotoNaskhArabic-Variable", "NotoNaskhArabic[wght]", "NotoNaskhArabic-Regular",
             "NotoSansArabic-Variable", "NotoSansArabic[wght]", "arial", "tradbdo"],
            size,
            weight,
        )
    if script == "devanagari":
        return _first_existing(
            ["NotoSansDevanagari-Variable", "NotoSansDevanagari[wght]", "NotoSansDevanagari-Regular", "Nirmala", "mangal"],
            size,
            weight,
        )
    if script == "bengali":
        return _first_existing(
            ["NotoSansBengali-Variable", "NotoSansBengali[wght]", "NotoSansBengali-Regular", "Nirmala", "vrinda"],
            size,
            weight,
        )
    if script == "cyrillic":
        return _first_existing(
            ["NotoSans-Variable", "NotoSans[wght]", "NotoSans-Regular", "segoeui", "arial"],
            size,
            weight,
        )
    if script == "greek":
        return _first_existing(
            ["NotoSans-Variable", "NotoSans[wght]", "NotoSans-Regular", "segoeui", "arial"],
            size,
            weight,
        )

    # Latin / European — user-selected display font when available
    if script in {"latin", "other"} and font_id:
        from text_fonts import load_reciter_font, load_title_font

        if role == "title":
            return load_title_font(font_id, size)
        return load_reciter_font(font_id, size)

    fonts_dir = _fonts_dir()
    if role == "title":
        if (fonts_dir / "Cinzel-Variable.ttf").exists():
            return _load_truetype(fonts_dir / "Cinzel-Variable.ttf", size, 400)
        if (fonts_dir / "PlayfairDisplay-Variable.ttf").exists():
            return _load_truetype(fonts_dir / "PlayfairDisplay-Variable.ttf", size, 400)
    else:
        if (fonts_dir / "CormorantGaramond-Variable.ttf").exists():
            return _load_truetype(fonts_dir / "CormorantGaramond-Variable.ttf", size, 300)
        if (fonts_dir / "JosefinSans-Variable.ttf").exists():
            return _load_truetype(fonts_dir / "JosefinSans-Variable.ttf", size, 300)

    return _first_existing(["NotoSans-Variable", "NotoSans[wght]", "NotoSans-Regular", "Georgia", "segoeui"], size, weight)


def font_factory_for_text(text: str, *, role: str = "title", font_id: str | None = None):
    def factory(size: int):
        return font_for_text(text, size, role=role, font_id=font_id)
    return factory


def text_renders(text: str, size: int = 48) -> bool:
    """True when the chosen font draws visible glyphs (not tofu boxes)."""
    if not text.strip():
        return True
    from PIL import Image, ImageDraw

    shown = shape_text(text)
    font = font_for_text(text, size, role="title")
    img = Image.new("L", (800, 120), 0)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), shown, font=font, fill=255)
    return img.getbbox() is not None
