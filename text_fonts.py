"""Catalog of thumbnail text fonts (title + reciter) and download URLs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont

# ── Google Fonts raw URLs (github.com/google/fonts) ──────────────────────────
_GH = "https://raw.githubusercontent.com/google/fonts/main/ofl"

FONT_DOWNLOADS: dict[str, str] = {
    # Arabic + script coverage (required for non-Latin UI languages)
    "Amiri-Bold.ttf": f"{_GH}/amiri/Amiri-Bold.ttf",
    "NotoSans-Variable.ttf": f"{_GH}/notosans/NotoSans%5Bwdth,wght%5D.ttf",
    "NotoSansSC-Variable.ttf": f"{_GH}/notosanssc/NotoSansSC%5Bwght%5D.ttf",
    "NotoSansJP-Variable.ttf": f"{_GH}/notosansjp/NotoSansJP%5Bwght%5D.ttf",
    "NotoSansKR-Variable.ttf": f"{_GH}/notosanskr/NotoSansKR%5Bwght%5D.ttf",
    "NotoSansDevanagari-Variable.ttf": f"{_GH}/notosansdevanagari/NotoSansDevanagari%5Bwdth,wght%5D.ttf",
    "NotoSansBengali-Variable.ttf": f"{_GH}/notosansbengali/NotoSansBengali%5Bwdth,wght%5D.ttf",
    "NotoNaskhArabic-Variable.ttf": f"{_GH}/notonaskharabic/NotoNaskhArabic%5Bwght%5D.ttf",
    # Title — serif / display (cinematic surah names)
    "Cinzel-Variable.ttf": f"{_GH}/cinzel/Cinzel%5Bwght%5D.ttf",
    "PlayfairDisplay-Variable.ttf": f"{_GH}/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "CormorantGaramond-Variable.ttf": f"{_GH}/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
    "EBGaramond-Variable.ttf": f"{_GH}/ebgaramond/EBGaramond%5Bwght%5D.ttf",
    "LibreBaskerville-Variable.ttf": f"{_GH}/librebaskerville/LibreBaskerville%5Bwght%5D.ttf",
    "Spectral-Regular.ttf": f"{_GH}/spectral/Spectral-Regular.ttf",
    "Spectral-Bold.ttf": f"{_GH}/spectral/Spectral-Bold.ttf",
    "Lora-Variable.ttf": f"{_GH}/lora/Lora%5Bwght%5D.ttf",
    "Merriweather-Variable.ttf": f"{_GH}/merriweather/Merriweather%5Bopsz,wdth,wght%5D.ttf",
    "Fraunces-Variable.ttf": f"{_GH}/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf",
    "CrimsonPro-Variable.ttf": f"{_GH}/crimsonpro/CrimsonPro%5Bwght%5D.ttf",
    "Alegreya-Variable.ttf": f"{_GH}/alegreya/Alegreya%5Bwght%5D.ttf",
    "Italiana-Regular.ttf": f"{_GH}/italiana/Italiana-Regular.ttf",
    "Marcellus-Regular.ttf": f"{_GH}/marcellus/Marcellus-Regular.ttf",
    "BodoniModa-Variable.ttf": f"{_GH}/bodonimoda/BodoniModa%5Bopsz,wght%5D.ttf",
    "Vollkorn-Variable.ttf": f"{_GH}/vollkorn/Vollkorn%5Bwght%5D.ttf",
    "Cardo-Regular.ttf": f"{_GH}/cardo/Cardo-Regular.ttf",
    "CinzelDecorative-Regular.ttf": f"{_GH}/cinzeldecorative/CinzelDecorative-Regular.ttf",
    "Unna-Regular.ttf": f"{_GH}/unna/Unna-Regular.ttf",
    "Cormorant-Variable.ttf": f"{_GH}/cormorant/Cormorant%5Bwght%5D.ttf",
    "LibreCaslonText-Variable.ttf": f"{_GH}/librecaslontext/LibreCaslonText%5Bwght%5D.ttf",
    "GentiumPlus-Regular.ttf": f"{_GH}/gentiumplus/GentiumPlus-Regular.ttf",
    # Reciter — light sans / refined serif subtitles
    "JosefinSans-Variable.ttf": f"{_GH}/josefinsans/JosefinSans%5Bwght%5D.ttf",
    "Raleway-Variable.ttf": f"{_GH}/raleway/Raleway%5Bwght%5D.ttf",
    "Montserrat-Variable.ttf": f"{_GH}/montserrat/Montserrat%5Bwght%5D.ttf",
    "SourceSans3-Variable.ttf": f"{_GH}/sourcesans3/SourceSans3%5Bwght%5D.ttf",
    "Inter-Variable.ttf": f"{_GH}/inter/Inter%5Bopsz,wght%5D.ttf",
    "NunitoSans-Variable.ttf": f"{_GH}/nunitosans/NunitoSans%5BYTLC,opsz,wdth,wght%5D.ttf",
    "Quicksand-Variable.ttf": f"{_GH}/quicksand/Quicksand%5Bwght%5D.ttf",
    "LibreFranklin-Variable.ttf": f"{_GH}/librefranklin/LibreFranklin%5Bwght%5D.ttf",
    "WorkSans-Variable.ttf": f"{_GH}/worksans/WorkSans%5Bwght%5D.ttf",
    "Lato-Light.ttf": f"{_GH}/lato/Lato-Light.ttf",
    "Lato-Regular.ttf": f"{_GH}/lato/Lato-Regular.ttf",
    "Jost-Variable.ttf": f"{_GH}/jost/Jost%5Bwght%5D.ttf",
    "Outfit-Variable.ttf": f"{_GH}/outfit/Outfit%5Bwght%5D.ttf",
    "DMSans-Variable.ttf": f"{_GH}/dmsans/DMSans%5Bopsz,wght%5D.ttf",
    "Karla-Variable.ttf": f"{_GH}/karla/Karla%5Bwght%5D.ttf",
    "Manrope-Variable.ttf": f"{_GH}/manrope/Manrope%5Bwght%5D.ttf",
    "OpenSans-Variable.ttf": f"{_GH}/opensans/OpenSans%5Bwdth,wght%5D.ttf",
    "Poppins-Light.ttf": f"{_GH}/poppins/Poppins-Light.ttf",
    "Poppins-Regular.ttf": f"{_GH}/poppins/Poppins-Regular.ttf",
    "Mulish-Variable.ttf": f"{_GH}/mulish/Mulish%5Bwght%5D.ttf",
    "Figtree-Variable.ttf": f"{_GH}/figtree/Figtree%5Bwght%5D.ttf",
    "Lexend-Variable.ttf": f"{_GH}/lexend/Lexend%5Bwght%5D.ttf",
    "Cabin-Variable.ttf": f"{_GH}/cabin/Cabin%5Bwdth,wght%5D.ttf",
    "EBGaramond-Italic-Variable.ttf": f"{_GH}/ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf",
}

# Fonts bundled on first frozen launch (core + defaults)
ESSENTIAL_FONT_FILES: frozenset[str] = frozenset({
    "Amiri-Bold.ttf",
    "Cinzel-Variable.ttf",
    "CormorantGaramond-Variable.ttf",
    "PlayfairDisplay-Variable.ttf",
    "JosefinSans-Variable.ttf",
    "NotoSans-Variable.ttf",
    "NotoSansSC-Variable.ttf",
    "NotoSansJP-Variable.ttf",
    "NotoSansKR-Variable.ttf",
    "NotoSansDevanagari-Variable.ttf",
    "NotoSansBengali-Variable.ttf",
    "NotoNaskhArabic-Variable.ttf",
})


@dataclass(frozen=True)
class FontChoice:
    id: str
    label: str
    filename: str
    weight: int | None = None


TITLE_FONTS: tuple[FontChoice, ...] = (
    FontChoice("cinzel", "Cinzel — Roman inscription", "Cinzel-Variable.ttf", 400),
    FontChoice("playfair", "Playfair Display — editorial luxury", "PlayfairDisplay-Variable.ttf", 400),
    FontChoice("cormorant_garamond", "Cormorant Garamond — refined classic", "CormorantGaramond-Variable.ttf", 500),
    FontChoice("eb_garamond", "EB Garamond — bookish elegance", "EBGaramond-Variable.ttf", 500),
    FontChoice("libre_baskerville", "Libre Baskerville — timeless serif", "LibreBaskerville-Variable.ttf", 400),
    FontChoice("spectral", "Spectral — crisp literary", "Spectral-Bold.ttf"),
    FontChoice("lora", "Lora — warm contemporary serif", "Lora-Variable.ttf", 500),
    FontChoice("merriweather", "Merriweather — sturdy headline", "Merriweather-Variable.ttf", 700),
    FontChoice("fraunces", "Fraunces — soft display charm", "Fraunces-Variable.ttf", 500),
    FontChoice("crimson_pro", "Crimson Pro — heritage book", "CrimsonPro-Variable.ttf", 600),
    FontChoice("alegreya", "Alegreya — calligraphic rhythm", "Alegreya-Variable.ttf", 500),
    FontChoice("italiana", "Italiana — art-deco caps", "Italiana-Regular.ttf"),
    FontChoice("marcellus", "Marcellus — temple inscription", "Marcellus-Regular.ttf"),
    FontChoice("bodoni_moda", "Bodoni Moda — high fashion", "BodoniModa-Variable.ttf", 500),
    FontChoice("vollkorn", "Vollkorn — old-style gravitas", "Vollkorn-Variable.ttf", 600),
    FontChoice("cardo", "Cardo — scholarly classic", "Cardo-Regular.ttf"),
    FontChoice("cinzel_decorative", "Cinzel Decorative — ornate caps", "CinzelDecorative-Regular.ttf"),
    FontChoice("unna", "Unna — gentle editorial", "Unna-Regular.ttf"),
    FontChoice("cormorant", "Cormorant — airy display", "Cormorant-Variable.ttf", 500),
    FontChoice("libre_caslon", "Libre Caslon Text — traditional", "LibreCaslonText-Variable.ttf", 400),
    FontChoice("gentium_plus", "Gentium Plus — dignified Latin", "GentiumPlus-Regular.ttf"),
)

RECITER_FONTS: tuple[FontChoice, ...] = (
    FontChoice("cormorant_garamond", "Cormorant Garamond — light classic", "CormorantGaramond-Variable.ttf", 300),
    FontChoice("josefin_sans", "Josefin Sans — geometric light", "JosefinSans-Variable.ttf", 300),
    FontChoice("raleway", "Raleway — airy modern", "Raleway-Variable.ttf", 300),
    FontChoice("montserrat", "Montserrat — clean geometric", "Montserrat-Variable.ttf", 300),
    FontChoice("source_sans", "Source Sans 3 — neutral pro", "SourceSans3-Variable.ttf", 300),
    FontChoice("inter", "Inter — UI clarity", "Inter-Variable.ttf", 300),
    FontChoice("nunito_sans", "Nunito Sans — soft rounded", "NunitoSans-Variable.ttf", 300),
    FontChoice("quicksand", "Quicksand — friendly light", "Quicksand-Variable.ttf", 400),
    FontChoice("libre_franklin", "Libre Franklin — news sans", "LibreFranklin-Variable.ttf", 300),
    FontChoice("work_sans", "Work Sans — balanced grotesk", "WorkSans-Variable.ttf", 300),
    FontChoice("lato_light", "Lato Light — understated", "Lato-Light.ttf"),
    FontChoice("jost", "Jost — European grotesk", "Jost-Variable.ttf", 300),
    FontChoice("outfit", "Outfit — modern geometric", "Outfit-Variable.ttf", 300),
    FontChoice("dm_sans", "DM Sans — friendly pro", "DMSans-Variable.ttf", 400),
    FontChoice("karla", "Karla — warm grotesk", "Karla-Variable.ttf", 300),
    FontChoice("manrope", "Manrope — soft geometric", "Manrope-Variable.ttf", 400),
    FontChoice("open_sans", "Open Sans — universal readable", "OpenSans-Variable.ttf", 300),
    FontChoice("poppins_light", "Poppins Light — sleek modern", "Poppins-Light.ttf"),
    FontChoice("mulish", "Mulish — minimal grotesk", "Mulish-Variable.ttf", 300),
    FontChoice("figtree", "Figtree — contemporary UI", "Figtree-Variable.ttf", 400),
    FontChoice("lexend", "Lexend — readability tuned", "Lexend-Variable.ttf", 400),
    FontChoice("cabin", "Cabin — humanist sans", "Cabin-Variable.ttf", 400),
    FontChoice("lora", "Lora — serif subtitle", "Lora-Variable.ttf", 400),
    FontChoice("spectral", "Spectral — literary serif", "Spectral-Regular.ttf"),
    FontChoice("eb_garamond_italic", "EB Garamond Italic — elegant", "EBGaramond-Italic-Variable.ttf", 400),
)

_TITLE_BY_ID = {f.id: f for f in TITLE_FONTS}
_RECITER_BY_ID = {f.id: f for f in RECITER_FONTS}


def _fonts_dir() -> Path:
    from app_paths import base_dir
    return base_dir() / "assets" / "fonts"


def title_font_ids() -> list[str]:
    return [f.id for f in TITLE_FONTS]


def reciter_font_ids() -> list[str]:
    return [f.id for f in RECITER_FONTS]


def title_font_label(font_id: str) -> str:
    return _TITLE_BY_ID.get(font_id, TITLE_FONTS[0]).label


def reciter_font_label(font_id: str) -> str:
    return _RECITER_BY_ID.get(font_id, RECITER_FONTS[0]).label


def resolve_title_font(font_id: str) -> FontChoice:
    return _TITLE_BY_ID.get(font_id, TITLE_FONTS[0])


def resolve_reciter_font(font_id: str) -> FontChoice:
    return _RECITER_BY_ID.get(font_id, RECITER_FONTS[0])


def load_choice(choice: FontChoice, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = _fonts_dir() / choice.filename
    if not path.exists():
        return ImageFont.load_default()
    font = ImageFont.truetype(str(path), size=size)
    if choice.weight is not None:
        try:
            font.set_variation_by_axes([choice.weight])
        except (AttributeError, OSError, ValueError):
            pass
    return font


def load_title_font(font_id: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_choice(resolve_title_font(font_id), size)


def load_reciter_font(font_id: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return load_choice(resolve_reciter_font(font_id), size)
