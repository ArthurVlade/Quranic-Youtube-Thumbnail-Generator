"""Generate the application icon (assets/icon.ico) — an elegant gold motif on dark.

Run once: python make_icon.py
The icon is a rounded dark tile with a gold crescent + book/open-pages motif,
evoking Quranic recitation. Multiple sizes are embedded for crisp display.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

GOLD = (212, 175, 55)
GOLD_LIGHT = (240, 214, 120)
DARK = (13, 17, 23)
PANEL = (26, 29, 35)


def _draw_icon(size: int) -> Image.Image:
    # Supersample for smooth edges
    ss = 4
    s = size * ss
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded background tile with subtle border
    margin = int(s * 0.06)
    radius = int(s * 0.22)
    d.rounded_rectangle(
        (margin, margin, s - margin, s - margin),
        radius=radius,
        fill=PANEL,
        outline=GOLD,
        width=max(2, int(s * 0.018)),
    )

    cx = s // 2
    cy = int(s * 0.56)

    # Open book / pages base
    book_w = int(s * 0.50)
    book_h = int(s * 0.20)
    top = cy
    left = cx - book_w // 2
    right = cx + book_w // 2
    bottom = top + book_h
    # Two page triangles meeting at the spine
    spine_lift = int(book_h * 0.35)
    d.polygon(
        [(cx, top - spine_lift), (left, top), (left, bottom), (cx, bottom - spine_lift // 2)],
        fill=GOLD,
    )
    d.polygon(
        [(cx, top - spine_lift), (right, top), (right, bottom), (cx, bottom - spine_lift // 2)],
        fill=GOLD_LIGHT,
    )
    # Spine line
    d.line([(cx, top - spine_lift), (cx, bottom - spine_lift // 2)], fill=DARK, width=max(2, int(s * 0.01)))

    # Crescent moon above the book
    moon_r = int(s * 0.16)
    moon_cx = cx
    moon_cy = int(s * 0.34)
    d.ellipse(
        (moon_cx - moon_r, moon_cy - moon_r, moon_cx + moon_r, moon_cy + moon_r),
        fill=GOLD_LIGHT,
    )
    # Carve crescent by overlaying a panel-colored circle offset to the right
    offset = int(moon_r * 0.55)
    d.ellipse(
        (moon_cx - moon_r + offset, moon_cy - moon_r, moon_cx + moon_r + offset, moon_cy + moon_r),
        fill=PANEL,
    )

    # Small star next to crescent
    star_cx = moon_cx + int(moon_r * 0.9)
    star_cy = moon_cy - int(moon_r * 0.2)
    star_r = int(s * 0.035)
    d.ellipse((star_cx - star_r, star_cy - star_r, star_cx + star_r, star_cy + star_r), fill=GOLD_LIGHT)

    return img.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    assets = Path(__file__).resolve().parent / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [_draw_icon(sz) for sz in sizes]

    ico_path = assets / "icon.ico"
    images[-1].save(ico_path, format="ICO", sizes=[(sz, sz) for sz in sizes])
    print(f"Wrote {ico_path}")

    # Also save a PNG preview
    png_path = assets / "icon.png"
    images[-1].save(png_path, format="PNG")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
