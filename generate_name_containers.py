"""Generate transparent outline-only surah-name container frames (PNG assets).

No inner fills — only borders and margin ornament so the scenery shows through.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

W, H = 1600, 300
INNER = (280, 72, 1320, 228)


def _accent(r: int, g: int, b: int, a: int = 255) -> tuple[int, int, int, int]:
    return (r, g, b, a)


GOLD = _accent(212, 175, 55)
GOLD_LIGHT = _accent(255, 235, 170, 200)
WHITE = _accent(255, 255, 255, 220)
SILVER = _accent(190, 195, 205, 230)


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _draw_margin_arches(draw: ImageDraw.ImageDraw, y: float, x1: float, x2: float,
                        color, amp: float = 16) -> None:
    n = 10
    for i in range(n):
        ax1 = x1 + (x2 - x1) * i / n
        ax2 = x1 + (x2 - x1) * (i + 1) / n
        cx = (ax1 + ax2) / 2
        w = (ax2 - ax1) * 0.9
        draw.arc((cx - w / 2, y - amp, cx + w / 2, y + amp), 200, 340, fill=color, width=2)


def _draw_side_vines(draw: ImageDraw.ImageDraw, side: str, color) -> None:
    ix1, iy1, ix2, iy2 = INNER
    x = ix1 - 55 if side == "left" else ix2 + 55
    for t in range(5):
        y = iy1 + 20 + t * (iy2 - iy1 - 40) / 4
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), outline=color, width=2)
        draw.line((x, y, x + (18 if side == "left" else -18), y + 8), fill=color, width=2)


def _draw_corner_flourish(draw: ImageDraw.ImageDraw, cx: float, cy: float, color, flip: int = 1) -> None:
    for i in range(3):
        ang = -0.4 + i * 0.35
        ex = cx + math.cos(ang) * 28 * flip
        ey = cy + math.sin(ang) * 18
        draw.line((cx, cy, ex, ey), fill=color, width=2)
        draw.ellipse((ex - 4, ey - 4, ex + 4, ey + 4), outline=color, width=1)


def _decorate_margins(draw: ImageDraw.ImageDraw, lace_color) -> None:
    ix1, iy1, ix2, iy2 = INNER
    _draw_margin_arches(draw, iy1 - 32, ix1 - 60, ix2 + 60, lace_color, 14)
    _draw_margin_arches(draw, iy2 + 32, ix1 - 60, ix2 + 60, lace_color, 14)
    _draw_side_vines(draw, "left", lace_color)
    _draw_side_vines(draw, "right", lace_color)
    _draw_corner_flourish(draw, ix1 - 45, iy1 - 20, lace_color, 1)
    _draw_corner_flourish(draw, ix2 + 45, iy1 - 20, lace_color, -1)
    _draw_corner_flourish(draw, ix1 - 45, iy2 + 20, lace_color, 1)
    _draw_corner_flourish(draw, ix2 + 45, iy2 + 20, lace_color, -1)


def _draw_lobed_outline(draw: ImageDraw.ImageDraw, y1: float, y2: float, color, width: int = 4) -> None:
    mid = (y1 + y2) / 2
    h = y2 - y1
    body_l, body_r = 220, W - 220
    draw.rounded_rectangle((body_l, y1, body_r, y2), radius=int(h * 0.22), outline=color, width=width)
    draw.pieslice((40, mid - h * 0.95, 260, mid + h * 0.95), 120, 240, outline=color, width=width)
    draw.pieslice((80, mid - h * 0.55, 200, mid + h * 0.55), 90, 270, outline=color, width=max(2, width - 1))
    draw.pieslice((W - 260, mid - h * 0.95, W - 40, mid + h * 0.95), -60, 60, outline=color, width=width)
    draw.pieslice((W - 200, mid - h * 0.55, W - 80, mid + h * 0.55), -90, 90, outline=color, width=max(2, width - 1))


def _draw_scallop_bracket(draw: ImageDraw.ImageDraw, y1: float, y2: float, color) -> None:
    mid = (y1 + y2) / 2
    h = y2 - y1
    pts_l = []
    for i in range(9):
        t = i / 8
        ang = math.pi * 0.5 + t * math.pi
        r = h * (0.55 + 0.15 * math.sin(t * math.pi * 2))
        pts_l.append((60 + math.cos(ang) * r * 0.9, mid + math.sin(ang) * r))
    pts_r = [(W - x, y) for x, y in reversed(pts_l)]
    top = [(220 + i * (W - 440) / 20, y1 + (1 - abs(i - 10) / 10) * 8) for i in range(21)]
    bot = [(x, y2 * 2 - y) for x, y in reversed(top)]
    outline = pts_l + top + pts_r + bot
    draw.line(outline, fill=color, width=5, joint="curve")
    draw.line(outline, fill=GOLD_LIGHT, width=2, joint="curve")


def _style_lace_capsule(accent) -> Image.Image:
    img, draw = _canvas()
    ix1, iy1, ix2, iy2 = INNER
    draw.rounded_rectangle((ix1 - 30, iy1 - 18, ix2 + 30, iy2 + 18), radius=90, outline=accent, width=4)
    draw.rounded_rectangle((ix1 - 22, iy1 - 10, ix2 + 22, iy2 + 10), radius=78, outline=GOLD_LIGHT, width=1)
    _decorate_margins(draw, accent)
    return img


def _style_lobed_medallion(accent) -> Image.Image:
    img, draw = _canvas()
    y1, y2 = 55, H - 55
    _draw_lobed_outline(draw, y1, y2, accent, 5)
    _draw_lobed_outline(draw, y1 + 8, y2 - 8, GOLD_LIGHT, 2)
    _decorate_margins(draw, accent)
    return img


def _style_scallop_bracket(accent) -> Image.Image:
    img, draw = _canvas()
    y1, y2 = 48, H - 48
    _draw_scallop_bracket(draw, y1, y2, accent)
    draw.rounded_rectangle((210, y1 + 14, W - 210, y2 - 14), radius=16, outline=GOLD_LIGHT, width=2)
    _decorate_margins(draw, accent)
    return img


def _style_notched_jewel(accent) -> Image.Image:
    img, draw = _canvas()
    y1, y2 = 58, H - 58
    band = [
        (180, y1), (240, y1 - 18), (280, y1), (W - 280, y1), (W - 240, y1 - 18), (W - 180, y1),
        (W - 180, y2), (W - 240, y2 + 18), (W - 280, y2), (280, y2), (240, y2 + 18), (180, y2),
    ]
    draw.line(band + [band[0]], fill=accent, width=4, joint="curve")
    draw.line(band + [band[0]], fill=GOLD_LIGHT, width=2, joint="curve")
    _decorate_margins(draw, accent)
    return img


def _style_minimal_double(accent) -> Image.Image:
    img, draw = _canvas()
    ix1, iy1, ix2, iy2 = INNER
    draw.rounded_rectangle((ix1 - 40, iy1 - 24, ix2 + 40, iy2 + 24), radius=12, outline=accent, width=3)
    draw.rounded_rectangle((ix1 - 32, iy1 - 16, ix2 + 32, iy2 + 16), radius=8, outline=GOLD_LIGHT, width=1)
    return img


def _style_corner_brackets(accent) -> Image.Image:
    img, draw = _canvas()
    ix1, iy1, ix2, iy2 = INNER
    pad_x, pad_y = 50, 28
    x1, y1, x2, y2 = ix1 - pad_x, iy1 - pad_y, ix2 + pad_x, iy2 + pad_y
    arm = 42
    for corners in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
        cx, cy, fx, fy = corners
        draw.line((cx, cy, cx + arm * fx, cy), fill=accent, width=4)
        draw.line((cx, cy, cx, cy + arm * fy), fill=accent, width=4)
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), outline=GOLD_LIGHT, width=1)
    return img


def _style_diamond_ends(accent) -> Image.Image:
    img, draw = _canvas()
    mid = H // 2
    y1, y2 = 70, H - 70
    draw.line([(260, y1), (W - 260, y1), (W - 260, y2), (260, y2), (260, y1)], fill=accent, width=3)
    for cx in (130, W - 130):
        draw.polygon([(cx, mid), (cx + 55, y1 + 8), (cx + 55, y2 - 8), (cx, mid)], outline=accent, width=2)
        draw.polygon([(cx, mid), (cx - 55, y1 + 8), (cx - 55, y2 - 8), (cx, mid)], outline=GOLD_LIGHT, width=1)
    return img


def _style_art_deco(accent) -> Image.Image:
    img, draw = _canvas()
    y1, y2 = 62, H - 62
    for i in range(13):
        x = 180 + i * (W - 360) / 12
        hump = 10 if i % 2 == 0 else 4
        draw.line((x, y1 - hump, x, y1), fill=accent, width=2)
        draw.line((x, y2, x, y2 + hump), fill=accent, width=2)
    draw.line((200, y1, W - 200, y1), fill=accent, width=3)
    draw.line((200, y2, W - 200, y2), fill=accent, width=3)
    draw.line((160, y1 - 20, 160, y2 + 20), fill=GOLD_LIGHT, width=2)
    draw.line((W - 160, y1 - 20, W - 160, y2 + 20), fill=GOLD_LIGHT, width=2)
    return img


def _style_triple_line(accent) -> Image.Image:
    img, draw = _canvas()
    ix1, iy1, ix2, iy2 = INNER
    for off in (-22, 0, 22):
        draw.rounded_rectangle(
            (ix1 - 36 + off // 3, iy1 - 20 + off, ix2 + 36 - off // 3, iy2 + 20 - off),
            radius=6, outline=accent if off == 0 else GOLD_LIGHT, width=2 if off == 0 else 1,
        )
    return img


def _style_crescent_ends(accent) -> Image.Image:
    img, draw = _canvas()
    y1, y2 = 58, H - 58
    mid = H // 2
    draw.line((240, y1, W - 240, y1), fill=accent, width=3)
    draw.line((240, y2, W - 240, y2), fill=accent, width=3)
    draw.arc((60, mid - 100, 220, mid + 100), 270, 90, fill=accent, width=4)
    draw.arc((W - 220, mid - 100, W - 60, mid + 100), 90, 270, fill=accent, width=4)
    return img


def _style_geometric(accent) -> Image.Image:
    img, draw = _canvas()
    ix1, iy1, ix2, iy2 = INNER
    step = 28
    for x in range(ix1 - 40, ix2 + 40, step):
        draw.line((x, iy1 - 26, x + step // 2, iy1 - 14), fill=accent, width=2)
        draw.line((x, iy2 + 26, x + step // 2, iy2 + 14), fill=accent, width=2)
    draw.line((ix1 - 44, iy1 - 18, ix2 + 44, iy1 - 18), fill=accent, width=3)
    draw.line((ix1 - 44, iy2 + 18, ix2 + 44, iy2 + 18), fill=accent, width=3)
    return img


def _style_wide_bracket(accent) -> Image.Image:
    img, draw = _canvas()
    y1, y2 = 50, H - 50
    draw.line([(100, y1 + 30), (100, y1), (W - 100, y1), (W - 100, y1 + 30)], fill=accent, width=4)
    draw.line([(100, y2 - 30), (100, y2), (W - 100, y2), (W - 100, y2 - 30)], fill=accent, width=4)
    draw.line([(100, y1), (60, H // 2), (100, y2)], fill=GOLD_LIGHT, width=2)
    draw.line([(W - 100, y1), (W - 60, H // 2), (W - 100, y2)], fill=GOLD_LIGHT, width=2)
    return img


def _style_royal_heavy(accent) -> Image.Image:
    img, draw = _canvas()
    ix1, iy1, ix2, iy2 = INNER
    draw.rounded_rectangle((ix1 - 48, iy1 - 28, ix2 + 48, iy2 + 28), radius=18, outline=accent, width=6)
    draw.rounded_rectangle((ix1 - 38, iy1 - 18, ix2 + 38, iy2 + 18), radius=12, outline=GOLD_LIGHT, width=2)
    for cx in (ix1 - 48, ix2 + 48):
        draw.ellipse((cx - 8, H // 2 - 8, cx + 8, H // 2 + 8), outline=accent, width=2)
    return img


def _style_silver_thin() -> Image.Image:
    return _style_minimal_double(SILVER)


def _style_cinematic_white() -> Image.Image:
    img, draw = _canvas()
    ix1, iy1, ix2, iy2 = INNER
    draw.rounded_rectangle((ix1 - 36, iy1 - 20, ix2 + 36, iy2 + 20), radius=4, outline=WHITE, width=2)
    return img


def _style_gold_underline() -> Image.Image:
    img, draw = _canvas()
    ix1, _, ix2, iy2 = INNER
    draw.line((ix1 - 20, iy2 + 28, ix2 + 20, iy2 + 28), fill=GOLD, width=4)
    draw.line((ix1 - 10, iy2 + 34, ix2 + 10, iy2 + 34), fill=GOLD_LIGHT, width=1)
    for x in (ix1 - 20, ix2 + 20):
        draw.ellipse((x - 6, iy2 + 22, x + 6, iy2 + 34), outline=GOLD, width=2)
    return img


STYLES: list[tuple[str, str, callable]] = [
    # Lace filigree (outline)
    ("lace_gold", "Lace Filigree — Gold", lambda: _style_lace_capsule(GOLD)),
    ("lace_purple", "Lace Filigree — Royal Purple", lambda: _style_lace_capsule(_accent(180, 120, 220))),
    ("lace_rose", "Lace Filigree — Rose", lambda: _style_lace_capsule(_accent(220, 160, 180))),
    ("lace_white", "Lace Filigree — White", lambda: _style_lace_capsule(WHITE)),
    # Lobed medallion (outline)
    ("lobed_emerald", "Lobed Medallion — Gold", lambda: _style_lobed_medallion(GOLD)),
    ("lobed_bronze", "Lobed Medallion — Bronze", lambda: _style_lobed_medallion(_accent(180, 130, 70))),
    ("lobed_teal", "Lobed Medallion — Teal", lambda: _style_lobed_medallion(_accent(120, 200, 190))),
    ("lobed_purple", "Lobed Medallion — Violet", lambda: _style_lobed_medallion(_accent(170, 130, 220))),
    # Scallop bracket (outline)
    ("scallop_burgundy", "Scallop Bracket — Gold", lambda: _style_scallop_bracket(GOLD)),
    ("scallop_navy", "Scallop Bracket — Silver", lambda: _style_scallop_bracket(SILVER)),
    ("scallop_cream", "Scallop Bracket — White", lambda: _style_scallop_bracket(WHITE)),
    # Jewel panel (outline)
    ("jewel_ruby", "Jewel Panel — Gold", lambda: _style_notched_jewel(GOLD)),
    ("jewel_sapphire", "Jewel Panel — Silver", lambda: _style_notched_jewel(SILVER)),
    ("jewel_emerald", "Jewel Panel — White", lambda: _style_notched_jewel(WHITE)),
    ("jewel_gold", "Jewel Panel — Heavy Gold", lambda: _style_notched_jewel(_accent(255, 210, 90))),
    ("jewel_silver", "Jewel Panel — Fine Silver", lambda: _style_notched_jewel(SILVER)),
    ("jewel_lavender", "Jewel Panel — Soft Violet", lambda: _style_notched_jewel(_accent(190, 170, 230))),
    ("jewel_sunset", "Jewel Panel — Warm Gold", lambda: _style_notched_jewel(_accent(240, 180, 100))),
    ("jewel_mint", "Jewel Panel — Pale Mint", lambda: _style_notched_jewel(_accent(170, 220, 200))),
    # Minimal / cinematic
    ("frame_minimal_gold", "Minimal — Double Gold", lambda: _style_minimal_double(GOLD)),
    ("frame_minimal_white", "Minimal — White Line", _style_cinematic_white),
    ("frame_silver_thin", "Minimal — Silver Line", _style_silver_thin),
    ("frame_corner_brackets", "Corner Brackets — Gold", lambda: _style_corner_brackets(GOLD)),
    ("frame_corner_silver", "Corner Brackets — Silver", lambda: _style_corner_brackets(SILVER)),
    ("frame_diamond_ends", "Diamond Ends — Gold", lambda: _style_diamond_ends(GOLD)),
    ("frame_art_deco", "Art Deco — Gold", lambda: _style_art_deco(GOLD)),
    ("frame_triple_line", "Triple Line — Gold", lambda: _style_triple_line(GOLD)),
    ("frame_crescent_ends", "Crescent Ends — Gold", lambda: _style_crescent_ends(GOLD)),
    ("frame_geometric", "Geometric Band — Gold", lambda: _style_geometric(GOLD)),
    ("frame_wide_bracket", "Wide Bracket — Gold", lambda: _style_wide_bracket(GOLD)),
    ("frame_royal_heavy", "Royal Frame — Heavy Gold", lambda: _style_royal_heavy(GOLD)),
    ("frame_gold_underline", "Gold Underline Arc", _style_gold_underline),
]


def main() -> None:
    out = Path(__file__).resolve().parent / "assets" / "name_containers"
    out.mkdir(parents=True, exist_ok=True)
    for stem, _label, fn in STYLES:
        fn().save(out / f"{stem}.png", "PNG")
        print(f"  {stem}.png")
    print(f"Generated {len(STYLES)} surah name containers in {out}")


if __name__ == "__main__":
    main()
