"""Fetch and rasterize stylized surah name SVGs from Amrayn CDN."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import fitz
from PIL import Image, ImageChops

CDN_URL = "https://cdn.amrayn.com/qimages-c/{number}.svg"


def _cache_dir() -> Path:
    from app_paths import base_dir
    path = base_dir() / "assets" / "surah_svgs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _fetch_svg(surah_number: int) -> bytes:
    url = CDN_URL.format(number=surah_number)
    request = Request(url, headers={"User-Agent": "QuranThumbnailGenerator/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def _load_svg_bytes(surah_number: int) -> bytes:
    cache_path = _cache_dir() / f"{surah_number}.svg"
    if cache_path.exists() and cache_path.stat().st_size > 100:
        return cache_path.read_bytes()
    data = _fetch_svg(surah_number)
    cache_path.write_bytes(data)
    return data


_ALPHA_LUT = [0 if l > 245 else min(255, int((255 - l) * 1.35)) for l in range(256)]


def _recolor_rgba(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    """Tint the glyph to `color`, deriving alpha from luminance.

    Fully vectorised via PIL point/channel ops (was a per-pixel Python loop).
    """
    rgba = image.convert("RGBA")
    # Alpha from luminance, with near-white knocked out
    lum_alpha = rgba.convert("L").point(_ALPHA_LUT)
    # Respect the original coverage so transparent padding stays transparent
    orig_mask = rgba.getchannel("A").point(lambda a: 255 if a >= 8 else 0)
    final_alpha = ImageChops.multiply(lum_alpha, orig_mask)
    out = Image.new("RGBA", rgba.size, (color[0], color[1], color[2], 0))
    out.putalpha(final_alpha)
    return out


_OVERSAMPLE = 3  # render at 3× then downsample → crisp, anti-aliased result

# Cache rendered glyphs so repeated previews (e.g. dragging text) are instant.
_RENDER_CACHE: dict[tuple, Image.Image] = {}
_RENDER_CACHE_MAX = 32


def render_surah_svg(
    surah_number: int,
    max_width: int,
    color: tuple[int, int, int] = (255, 255, 255),
    max_height: int = 280,
) -> Image.Image | None:
    if surah_number < 1 or surah_number > 114:
        return None

    cache_key = (surah_number, int(max_width), tuple(color), int(max_height))
    cached = _RENDER_CACHE.get(cache_key)
    if cached is not None:
        return cached

    try:
        svg_bytes = _load_svg_bytes(surah_number)
        document = fitz.open(stream=svg_bytes, filetype="svg")
        page = document[0]
        # Render generously, then trim the (large) transparent margins so the
        # returned image is the *tight* glyph — this keeps the layout honest.
        scale_w = max_width / page.rect.width
        scale_h = max_height / page.rect.height
        scale = min(scale_w, scale_h) * _OVERSAMPLE
        matrix = fitz.Matrix(scale, scale)
        pixmap = page.get_pixmap(alpha=True, matrix=matrix)
        image = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples)
        document.close()

        # Trim transparent padding to the actual calligraphy bounds
        bbox = image.getbbox()
        if bbox:
            image = image.crop(bbox)

        # Fit the tight glyph within the requested box, preserving aspect
        gw, gh = image.size
        fit = min((max_width * _OVERSAMPLE) / gw, (max_height * _OVERSAMPLE) / gh, 1.0)
        target_w = max(1, int(gw * fit / _OVERSAMPLE))
        target_h = max(1, int(gh * fit / _OVERSAMPLE))
        image = image.resize((target_w, target_h), Image.Resampling.LANCZOS)
        result = _recolor_rgba(image, color)

        if len(_RENDER_CACHE) >= _RENDER_CACHE_MAX:
            _RENDER_CACHE.pop(next(iter(_RENDER_CACHE)))
        _RENDER_CACHE[cache_key] = result
        return result
    except Exception:
        return None


def prefetch_all() -> None:
    for number in range(1, 115):
        try:
            _load_svg_bytes(number)
            print(f"Cached surah SVG {number}/114")
        except Exception as exc:
            print(f"Surah {number}: {exc}")
