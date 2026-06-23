"""Fetch and rasterize stylized surah name SVGs from Amrayn CDN."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import fitz
from PIL import Image

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


def _recolor_rgba(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if a < 8:
                continue
            luminance = (r + g + b) / 3
            if luminance > 245:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            strength = min(255, int((255 - luminance) * 1.35))
            pixels[x, y] = (color[0], color[1], color[2], strength)
    return rgba


_OVERSAMPLE = 3  # render at 3× then downsample → crisp, anti-aliased result


def render_surah_svg(
    surah_number: int,
    max_width: int,
    color: tuple[int, int, int] = (255, 255, 255),
    max_height: int = 280,
) -> Image.Image | None:
    if surah_number < 1 or surah_number > 114:
        return None
    try:
        svg_bytes = _load_svg_bytes(surah_number)
        document = fitz.open(stream=svg_bytes, filetype="svg")
        page = document[0]
        scale_w = max_width / page.rect.width
        scale_h = max_height / page.rect.height
        scale = min(scale_w, scale_h) * _OVERSAMPLE
        matrix = fitz.Matrix(scale, scale)
        pixmap = page.get_pixmap(alpha=True, matrix=matrix)
        image = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples)
        document.close()
        # Downsample to target dimensions for crisp anti-aliasing
        target_w = pixmap.width // _OVERSAMPLE
        target_h = pixmap.height // _OVERSAMPLE
        image = image.resize((max(1, target_w), max(1, target_h)), Image.Resampling.LANCZOS)
        return _recolor_rgba(image, color)
    except Exception:
        return None


def prefetch_all() -> None:
    for number in range(1, 115):
        try:
            _load_svg_bytes(number)
            print(f"Cached surah SVG {number}/114")
        except Exception as exc:
            print(f"Surah {number}: {exc}")
