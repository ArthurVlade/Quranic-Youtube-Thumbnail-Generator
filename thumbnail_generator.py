"""Generate Quranic recitation thumbnails in a consistent cinematic style."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from surah_svg import render_surah_svg


THUMB_WIDTH = 1280
THUMB_HEIGHT = 720

GOLD = (212, 175, 55)
WHITE = (255, 255, 255)

TOP_MARGIN_RATIO = 0.12
GAP_ARABIC_TO_ENGLISH = 36
GAP_ENGLISH_TO_RECITER = 28
GAP_RECITER_TO_BADGE = 40


@dataclass
class ThumbnailConfig:
    arabic_surah: str
    english_surah: str
    reciter_name: str
    surah_number: int
    background_path: Path | None = None
    overlay_opacity: float = 0.50
    arabic_color: tuple[int, int, int] = field(default_factory=lambda: WHITE)
    english_color: tuple[int, int, int] = field(default_factory=lambda: WHITE)
    reciter_color: tuple[int, int, int] = field(default_factory=lambda: WHITE)
    badge_text_color: tuple[int, int, int] = field(default_factory=lambda: WHITE)
    badge_accent_color: tuple[int, int, int] = field(default_factory=lambda: GOLD)
    banner_id: str = "none"
    banner_custom_path: Path | None = None
    text_glow: bool = True
    text_offset_x: int = 0
    text_offset_y: int = 0
    show_reciter_overlay: bool = False
    reciter_overlay_path: Path | None = None
    reciter_overlay_x: int = 900
    reciter_overlay_y: int = 420
    reciter_overlay_width: int = 220
    # Typography sizes
    svg_max_height: int = 280
    title_size: int = 52
    reciter_size: int = 44
    badge_size: int = 28
    # Per-element independent offsets (relative to their natural stack position)
    svg_offset_x: int = 0
    svg_offset_y: int = 0
    title_offset_x: int = 0
    title_offset_y: int = 0
    reciter_offset_x: int = 0
    reciter_offset_y: int = 0
    badge_offset_x: int = 0
    badge_offset_y: int = 0
    # Banner corner size (fraction of min(W, H))
    banner_corner_size: float = 0.40


def _app_root() -> Path:
    return Path(__file__).resolve().parent


def _fonts_dir() -> Path:
    return _app_root() / "assets" / "fonts"


def _backgrounds_dir() -> Path:
    return _app_root() / "assets" / "backgrounds"


def _banners_dir() -> Path:
    path = _app_root() / "assets" / "banners"
    path.mkdir(parents=True, exist_ok=True)
    return path


_VALID_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
_PORTRAIT_STEMS = {"nature_autumn_forest"}  # known-bad portrait images


def list_nature_backgrounds() -> list[Path]:
    directory = _backgrounds_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file()
        and p.suffix.lower() in _VALID_SUFFIXES
        and p.stem not in _PORTRAIT_STEMS
        and p.stat().st_size > 10_000
    )


def list_banners() -> list[tuple[str, str, Path | None]]:
    directory = _banners_dir()
    labels = {
        "corner_gold_geometric": "Gold Geometric Lattice",
        "corner_arabesque_teal": "Teal Arabesque & Gold",
        "banner_1": "Simple - Classic Scroll",
        "banner_2": "Simple - Floral Arc",
        "banner_3": "Simple - Dot Trail",
        "banner_4": "Simple - Frame Curl",
        "banner_5": "Simple - Corner Lines",
    }
    items: list[tuple[str, str, Path | None]] = [("none", "None", None)]
    paths = sorted(directory.glob("*.png"), key=lambda p: (0 if p.stem.startswith("corner_") else 1 if p.stem.startswith("custom_") else 2, p.stem))
    for path in paths:
        if path.stem.startswith("custom_"):
            label = f"Custom: {path.stem.replace('custom_', '').replace('_', ' ').title()}"
        else:
            label = labels.get(path.stem, path.stem.replace("_", " ").title())
        items.append((path.stem, label, path))
    return items


def _is_premium_banner(stem: str) -> bool:
    return stem.startswith("corner_") or stem.startswith("custom_")


def default_nature_background() -> Path:
    images = list_nature_backgrounds()
    if images:
        return images[0]
    raise FileNotFoundError("No nature backgrounds found. Run: python setup_backgrounds.py")


def _load_font(filename: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = _fonts_dir() / filename
    if not path.exists():
        return ImageFont.load_default()
    font = ImageFont.truetype(str(path), size=size)
    if weight is not None:
        try:
            font.set_variation_by_axes([weight])
        except (AttributeError, OSError, ValueError):
            pass
    return font


def _find_font(candidates: list[str], size: int, weight: int | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in candidates:
        for ext in (".ttf", ".otf", ".TTF", ".OTF"):
            path = _fonts_dir() / f"{name}{ext}"
            if path.exists():
                font = ImageFont.truetype(str(path), size=size)
                if weight is not None:
                    try:
                        font.set_variation_by_axes([weight])
                    except (AttributeError, OSError, ValueError):
                        pass
                return font
    for name in candidates:
        for ext in (".ttf", ".otf", ".TTF", ".OTF"):
            path = Path("C:/Windows/Fonts") / f"{name}{ext}"
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _arabic_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _find_font(["Amiri-Bold", "Amiri-Regular", "Traditional Arabic", "trado"], size)


def _title_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Weight 400 = Cinzel Regular — elegant classical caps without heaviness
    if (_fonts_dir() / "Cinzel-Variable.ttf").exists():
        return _load_font("Cinzel-Variable.ttf", size, 400)
    if (_fonts_dir() / "PlayfairDisplay-Variable.ttf").exists():
        return _load_font("PlayfairDisplay-Variable.ttf", size, 400)
    return _find_font(["Georgia", "times"], size)


def _subtitle_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Cormorant Garamond Light for the reciter name — refined, not heavy
    if (_fonts_dir() / "CormorantGaramond-Variable.ttf").exists():
        return _load_font("CormorantGaramond-Variable.ttf", size, 300)
    if (_fonts_dir() / "JosefinSans-Variable.ttf").exists():
        return _load_font("JosefinSans-Variable.ttf", size, 300)
    return _find_font(["Georgia", "times"], size)


def _badge_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if (_fonts_dir() / "Cinzel-Variable.ttf").exists():
        return _load_font("Cinzel-Variable.ttf", size, 400)
    return _find_font(["Georgia", "times"], size)


def _reshape_arabic(text: str) -> str:
    if not text.strip():
        return ""
    return get_display(arabic_reshaper.reshape(text.strip()))


def _fit_text(draw, text, font_factory, max_width, start_size, min_size=24):
    size = start_size
    while size >= min_size:
        font = font_factory(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font, bbox
        size -= 2
    font = font_factory(min_size)
    return font, draw.textbbox((0, 0), text, font=font)


def _tint_rgba(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    img = image.convert("RGBA")
    pixels = img.load()
    for y in range(img.height):
        for x in range(img.width):
            _r, _g, _b, alpha = pixels[x, y]
            if alpha > 0:
                pixels[x, y] = (color[0], color[1], color[2], alpha)
    return img


def _draw_cinematic_text(draw, xy, text, font, fill, glow, s: int = 1):
    """Crisp shadow + optional soft bloom. Shadow offset scales with render scale."""
    x, y = xy
    draw.text((x + 2 * s, y + 3 * s), text, font=font, fill=(0, 0, 0, 140))
    if glow:
        bloom = (fill[0], fill[1], fill[2], 48)
        draw.text((x, y - s), text, font=font, fill=bloom)
        draw.text((x, y + s), text, font=font, fill=bloom)
    draw.text((x, y), text, font=font, fill=fill)


def _draw_centered_line(draw, center_x, y, text, font, fill, glow=True, s: int = 1):
    line = text.strip()
    if not line:
        return y, 0
    bbox = draw.textbbox((0, 0), line, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = center_x - width // 2
    _draw_cinematic_text(draw, (x, y - bbox[1]), line, font, fill, glow, s)
    return y + height, height



def _draw_surah_badge(draw, center_x, y, number, text_color, accent_color, glow, size=28, s: int = 1):
    text = str(number)
    font = _badge_font(size)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 24 * s, 14 * s
    badge_w, badge_h = text_w + pad_x * 2, text_h + pad_y * 2
    left = center_x - badge_w // 2
    top = y
    right, bottom = left + badge_w, top + badge_h
    radius = badge_h // 2
    outline_w = max(1, 2 * s)
    draw.rounded_rectangle((left, top, right, bottom), radius=radius, fill=(8, 8, 8, 230),
                           outline=accent_color, width=outline_w)
    # Side ornaments — gold dash + three dots
    ornament_y = top + badge_h // 2
    arm = 32 * s
    dash = 20 * s
    dot_r = 2 * s
    dot_gap = 8 * s
    for side in (-1, 1):
        ox = (left - arm) if side < 0 else (right + arm)
        draw.line((ox - dash * side, ornament_y, ox, ornament_y), fill=accent_color, width=outline_w)
        for dot in range(3):
            dy = ornament_y + (dot - 1) * dot_gap
            draw.ellipse((ox - dot_r, dy - dot_r, ox + dot_r, dy + dot_r), fill=accent_color)
    text_x = center_x - text_w // 2
    text_y = top + (badge_h - text_h) // 2 - bbox[1]
    _draw_cinematic_text(draw, (text_x, text_y), text, font, text_color, glow, s)




def _paste_reciter_overlay(canvas, config, s: int = 1):
    path = config.reciter_overlay_path
    if not config.show_reciter_overlay or not path or not path.exists():
        return
    photo = Image.open(path).convert("RGBA")
    width  = config.reciter_overlay_width * s
    height = int(width * photo.height / max(photo.width, 1))
    photo = ImageOps.fit(photo, (width, height), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width, height), radius=18 * s, fill=255)
    photo.putalpha(mask)
    x = config.reciter_overlay_x * s - width // 2
    y = config.reciter_overlay_y * s - height // 2
    canvas.alpha_composite(photo, (x, y))


def _apply_banners(canvas, config, s: int = 1):
    path = None
    if config.banner_custom_path and config.banner_custom_path.exists():
        path = config.banner_custom_path
    elif config.banner_id not in {"", "none"}:
        path = _banners_dir() / f"{config.banner_id}.png"
    if not path or not path.exists():
        return

    W, H = canvas.width, canvas.height
    corner = Image.open(path).convert("RGBA")
    premium = _is_premium_banner(path.stem)
    if not premium:
        corner = _tint_rgba(corner, config.arabic_color)

    # User-adjustable corner size (fraction of min dimension), non-premium slightly smaller
    frac = config.banner_corner_size if premium else config.banner_corner_size * 0.72
    size = max(40, int(min(W, H) * frac))
    corner = corner.resize((size, size), Image.Resampling.LANCZOS)

    # Premium banners touch the edge (margin=0); simple banners have a small inset
    margin = 0 if premium else max(8, int(14 * s))

    # Source images are designed as top-right corner pieces:
    #   top-right → use as-is
    #   top-left  → mirror horizontally
    #   bot-right → flip vertically
    #   bot-left  → mirror + flip (= rotate 180°)
    tr = corner
    tl = ImageOps.mirror(corner)
    br = ImageOps.flip(corner)
    bl = corner.rotate(180)

    placements = [
        (margin,          margin,          tl),   # top-left
        (W - size - margin, margin,        tr),   # top-right
        (margin,          H - size - margin, bl),   # bottom-left
        (W - size - margin, H - size - margin, br),  # bottom-right
    ]
    for x, y, piece in placements:
        canvas.alpha_composite(piece, (x, y))


def _load_background(path: Path, out_w: int = THUMB_WIDTH, out_h: int = THUMB_HEIGHT) -> Image.Image:
    image = Image.open(path).convert("RGB")
    src_w, src_h = image.size
    target_ratio = out_w / out_h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        image = image.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        image = image.crop((0, top, src_w, top + new_h))
    return image.resize((out_w, out_h), Image.Resampling.LANCZOS)


def compute_element_ys(config: ThumbnailConfig, s: int = 1) -> dict[str, int]:
    """Natural (un-offset) stack Y positions for each element in scaled coordinates."""
    H = THUMB_HEIGHT * s
    stack_y = int(H * TOP_MARGIN_RATIO) + config.text_offset_y * s
    svg_y   = stack_y
    title_y = svg_y   + config.svg_max_height * s  + GAP_ARABIC_TO_ENGLISH * s
    recit_y = title_y + config.title_size * s       + GAP_ENGLISH_TO_RECITER * s
    badge_y = recit_y + config.reciter_size * s     + GAP_RECITER_TO_BADGE * s
    return {"svg": svg_y, "title": title_y, "reciter": recit_y, "badge": badge_y}


def generate_thumbnail(config: ThumbnailConfig, *, _scale: int = 1) -> Image.Image:
    """Render thumbnail.  _scale=1 → 1280×720 (preview), 2 → 2560×1440 (HD), 3 → 4K."""
    s = _scale
    W, H = THUMB_WIDTH * s, THUMB_HEIGHT * s

    background_path = config.background_path or default_nature_background()
    base = _load_background(background_path, W, H)
    base = ImageEnhance.Brightness(base).enhance(0.68)
    base = ImageEnhance.Contrast(base).enhance(1.10)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * config.overlay_opacity)))
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(vignette).ellipse(
        (-W * 0.15, -H * 0.2, W * 1.15, H * 1.25),
        fill=(0, 0, 0, 55),
    )

    canvas = Image.alpha_composite(base.convert("RGBA"), overlay)
    canvas = Image.alpha_composite(canvas, vignette)
    draw   = ImageDraw.Draw(canvas)

    base_cx        = W // 2 + config.text_offset_x * s
    max_text_width = int(W * 0.86)
    ys = compute_element_ys(config, s)

    # ── Arabic SVG ────────────────────────────────────────────────────────────
    svg_cx = base_cx + config.svg_offset_x * s
    svg_y  = ys["svg"] + config.svg_offset_y * s
    art = render_surah_svg(config.surah_number, max_text_width, config.arabic_color,
                           max_height=config.svg_max_height * s)
    if art:
        canvas.alpha_composite(art, (svg_cx - art.width // 2, svg_y))
    elif config.arabic_surah.strip():
        arabic_text = _reshape_arabic(config.arabic_surah)
        if arabic_text:
            font, bbox = _fit_text(draw, arabic_text, _arabic_font, max_text_width,
                                   118 * s, 56 * s)
            arabic_w = bbox[2] - bbox[0]
            _draw_cinematic_text(draw, (svg_cx - arabic_w // 2, svg_y - bbox[1]),
                                 arabic_text, font, config.arabic_color, config.text_glow, s)

    # ── English title ─────────────────────────────────────────────────────────
    english = config.english_surah.strip().upper()
    if english:
        title_cx = base_cx + config.title_offset_x * s
        title_y  = ys["title"] + config.title_offset_y * s
        title_font, _ = _fit_text(draw, english, _title_font,
                                   max_text_width, config.title_size * s, 20 * s)
        _draw_centered_line(draw, title_cx, title_y, english,
                            title_font, config.english_color, config.text_glow, s)

    # ── Reciter name ──────────────────────────────────────────────────────────
    reciter = config.reciter_name.strip()
    if reciter:
        rec_cx  = base_cx + config.reciter_offset_x * s
        rec_y   = ys["reciter"] + config.reciter_offset_y * s
        rec_font, _ = _fit_text(draw, reciter.upper(), _subtitle_font,
                                 max_text_width, config.reciter_size * s, 18 * s)
        _draw_centered_line(draw, rec_cx, rec_y, reciter.upper(),
                            rec_font, config.reciter_color, config.text_glow, s)

    # ── Surah badge ───────────────────────────────────────────────────────────
    if config.surah_number > 0:
        badge_cx = base_cx + config.badge_offset_x * s
        badge_y  = ys["badge"] + config.badge_offset_y * s
        _draw_surah_badge(draw, badge_cx, badge_y, config.surah_number,
                          config.badge_text_color, config.badge_accent_color,
                          config.text_glow, config.badge_size * s, s)

    _paste_reciter_overlay(canvas, config, s)
    _apply_banners(canvas, config, s)
    return canvas.convert("RGB")


def save_thumbnail(config: ThumbnailConfig, output_path: Path, export_scale: int = 2) -> Path:
    image = generate_thumbnail(config, _scale=export_scale)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", compress_level=6)
    return output_path
