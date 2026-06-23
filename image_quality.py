"""Shared validation so only clean, high-resolution landscape scenery is kept.

Rejects the solid-red "no image" placeholders that some keyword image hosts
return, flat/near-solid images, portrait crops, and anything below HD.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageStat

MIN_WIDTH = 1280
MIN_HEIGHT = 720


def evaluate(image: Image.Image) -> tuple[bool, str]:
    """Return (is_good, reason). reason is '' when good."""
    try:
        rgb = image.convert("RGB")
    except Exception:
        return False, "undecodable"

    w, h = rgb.size
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return False, f"too small ({w}x{h})"
    if h > w:
        return False, "portrait"

    small = rgb.resize((48, 48))
    stat = ImageStat.Stat(small)
    r, g, b = stat.mean
    stddev = sum(stat.stddev) / 3

    # Solid-red (or near-solid red) placeholder
    if r > 160 and g < 75 and b < 75:
        return False, f"red placeholder (rgb {int(r)},{int(g)},{int(b)})"
    # Flat / near-solid colour (broken or boring)
    if stddev < 10:
        return False, f"flat (stddev {stddev:.1f})"

    return True, ""


def is_good(image: Image.Image) -> bool:
    return evaluate(image)[0]


def is_good_bytes(data: bytes) -> bool:
    if len(data) < 15_000:
        return False
    try:
        return is_good(Image.open(BytesIO(data)))
    except Exception:
        return False
