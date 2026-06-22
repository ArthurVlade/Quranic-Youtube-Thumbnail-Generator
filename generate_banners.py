"""Generate decorative corner banner overlays."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


def _ornament_swirl(draw: ImageDraw.ImageDraw, cx: float, cy: float, scale: float, variant: int) -> None:
    points: list[tuple[float, float]] = []
    steps = 80
    for i in range(steps):
        t = i / steps * math.pi * 1.6
        radius = scale * (0.35 + 0.65 * (1 - i / steps))
        if variant == 1:
            radius *= 1 + 0.15 * math.sin(t * 3)
        elif variant == 2:
            radius *= 1 + 0.2 * math.cos(t * 2)
        elif variant == 3:
            t += math.sin(t * 2) * 0.25
        elif variant == 4:
            radius *= 0.8 + 0.35 * math.sin(t * 4)
        x = cx + math.cos(t) * radius
        y = cy + math.sin(t) * radius
        points.append((x, y))
    if len(points) > 2:
        draw.line(points, fill=(255, 255, 255, 230), width=max(2, int(scale * 0.025)))

    for loop in range(2 + variant % 2):
        angle = loop * 1.2 + variant * 0.3
        lx = cx + math.cos(angle) * scale * 0.55
        ly = cy + math.sin(angle) * scale * 0.55
        draw.ellipse(
            (lx - scale * 0.08, ly - scale * 0.08, lx + scale * 0.08, ly + scale * 0.08),
            outline=(255, 255, 255, 210),
            width=2,
        )


def _draw_leaf_cluster(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float, flip: int = 1) -> None:
    for i in range(4):
        angle = -0.8 + i * 0.45
        ex = x + math.cos(angle) * scale * 0.35 * flip
        ey = y + math.sin(angle) * scale * 0.35
        draw.line((x, y, ex, ey), fill=(255, 255, 255, 200), width=2)
        draw.ellipse((ex - 4, ey - 7, ex + 4, ey + 7), fill=(255, 255, 255, 180))


def create_banner(variant: int, size: int = 320) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = size * 0.06

    if variant == 0:
        _ornament_swirl(draw, margin + 20, margin + 20, size * 0.42, 0)
        _draw_leaf_cluster(draw, margin + 55, margin + 75, size * 0.35)
        draw.arc((margin, margin, margin + size * 0.55, size * 0.55), 180, 270, fill=(255, 255, 255, 220), width=3)
    elif variant == 1:
        _ornament_swirl(draw, margin + 15, margin + 15, size * 0.48, 1)
        draw.line((margin, margin + 40, margin + 120, margin + 10), fill=(255, 255, 255, 210), width=2)
        draw.polygon(
            [(margin + 90, margin + 8), (margin + 110, margin + 25), (margin + 95, margin + 35)],
            outline=(255, 255, 255, 200),
        )
    elif variant == 2:
        _ornament_swirl(draw, margin + 25, margin + 25, size * 0.4, 2)
        for i in range(5):
            px = margin + 20 + i * 18
            py = margin + 15 + i * 8
            draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=(255, 255, 255, 190))
    elif variant == 3:
        _ornament_swirl(draw, margin + 10, margin + 10, size * 0.5, 3)
        draw.rounded_rectangle(
            (margin, margin, margin + 95, margin + 28),
            radius=12,
            outline=(255, 255, 255, 210),
            width=2,
        )
        _draw_leaf_cluster(draw, margin + 70, margin + 60, size * 0.28, -1)
    else:
        _ornament_swirl(draw, margin + 18, margin + 18, size * 0.45, 4)
        draw.line((margin, margin + 8, margin + 140, margin + 8), fill=(255, 255, 255, 200), width=2)
        draw.line((margin + 8, margin, margin + 8, margin + 140), fill=(255, 255, 255, 200), width=2)
        for i in range(3):
            draw.ellipse(
                (margin + 35 + i * 22, margin + 45, margin + 45 + i * 22, margin + 55),
                outline=(255, 255, 255, 180),
                width=2,
            )

    return img


def create_islamic_banner(variant: int, size: int = 320) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = size * 0.05
    gold = (255, 255, 255, 220)

    if variant == 0:
        draw.arc((m, m, m + size * 0.7, size * 0.7), 180, 270, fill=gold, width=3)
        draw.line((m, m + 40, m + 130, m + 10), fill=gold, width=2)
        for i in range(6):
            ang = math.radians(200 + i * 12)
            x = m + 30 + math.cos(ang) * 55
            y = m + 30 + math.sin(ang) * 55
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=gold)
    elif variant == 1:
        cx, cy = m + 55, m + 55
        for i in range(8):
            ang = math.radians(i * 45)
            x = cx + math.cos(ang) * 45
            y = cy + math.sin(ang) * 45
            draw.line((cx, cy, x, y), fill=gold, width=2)
        draw.polygon([(cx, cy - 18), (cx + 16, cy + 10), (cx - 16, cy + 10)], outline=gold)
    elif variant == 2:
        for i in range(7):
            draw.arc((m + i * 8, m + i * 6, m + 120 - i * 5, m + 100 - i * 4), 200, 280, fill=gold, width=2)
        for i in range(4):
            draw.line((m + 20 + i * 18, m + 15, m + 35 + i * 18, m + 55), fill=gold, width=2)
    elif variant == 3:
        draw.polygon([(m, m + 90), (m + 40, m), (m + 110, m), (m + 130, m + 90)], outline=gold, width=2)
        draw.arc((m + 25, m + 15, m + 95, m + 75), 200, 340, fill=gold, width=2)
    elif variant == 4:
        cx, cy = m + 60, m + 60
        for ring in (18, 30, 42):
            draw.ellipse((cx - ring, cy - ring, cx + ring, cy + ring), outline=gold, width=2)
        for i in range(8):
            ang = math.radians(i * 45)
            draw.line((cx, cy, cx + math.cos(ang) * 50, cy + math.sin(ang) * 50), fill=gold, width=1)
    elif variant == 5:
        draw.line((m, m + 8, m + 140, m + 8), fill=gold, width=2)
        for i in range(5):
            draw.text((m + 10 + i * 22, m + 18), "۞", fill=gold)
        draw.arc((m, m, m + 100, m + 100), 180, 270, fill=gold, width=2)
    elif variant == 6:
        step = 16
        for row in range(5):
            for col in range(5 - row):
                x = m + col * step + row * step * 0.5
                y = m + row * step * 0.8
                draw.polygon([(x, y), (x + 8, y + 8), (x, y + 16), (x - 8, y + 8)], outline=gold)
    else:
        draw.line((m + 10, m + 80, m + 10, m + 20), fill=gold, width=3)
        draw.polygon([(m + 10, m + 15), (m + 25, m + 35), (m - 5, m + 35)], fill=gold)
        draw.arc((m + 30, m + 20, m + 110, m + 100), 200, 270, fill=gold, width=2)

    return img


def main() -> None:
    output_dir = Path(__file__).resolve().parent / "assets" / "banners"
    output_dir.mkdir(parents=True, exist_ok=True)
    classic = ["Classic Scroll", "Floral Arc", "Dot Trail", "Frame Curl", "Corner Lines"]
    for i in range(5):
        banner = create_banner(i)
        path = output_dir / f"banner_{i + 1}.png"
        banner.save(path)
        print(f"Saved {path} ({classic[i]})")

    islamic = [
        "Islamic Arch",
        "Geometric Star",
        "Arabesque Vine",
        "Mihrab Frame",
        "Eight-Point Rosette",
        "Calligraphic Corner",
        "Tile Pattern",
        "Minaret Silhouette",
    ]
    for i in range(8):
        banner = create_islamic_banner(i)
        path = output_dir / f"islamic_{i + 1}.png"
        banner.save(path)
        print(f"Saved {path} ({islamic[i]})")


if __name__ == "__main__":
    main()
