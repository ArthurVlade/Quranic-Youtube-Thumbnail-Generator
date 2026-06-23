"""Load and scale surah-name container frames around the Arabic SVG."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

_TEMPLATE_W = 1600
_TEMPLATE_H = 300
_INNER = (280 / _TEMPLATE_W, 72 / _TEMPLATE_H, 1320 / _TEMPLATE_W, 228 / _TEMPLATE_H)

_LABELS: dict[str, str] = {
    "lace_gold": "Lace Filigree — Gold",
    "lace_purple": "Lace Filigree — Royal Purple",
    "lace_rose": "Lace Filigree — Rose",
    "lace_white": "Lace Filigree — White",
    "lobed_emerald": "Lobed Medallion — Gold",
    "lobed_bronze": "Lobed Medallion — Bronze",
    "lobed_teal": "Lobed Medallion — Teal",
    "lobed_purple": "Lobed Medallion — Violet",
    "scallop_burgundy": "Scallop Bracket — Gold",
    "scallop_navy": "Scallop Bracket — Silver",
    "scallop_cream": "Scallop Bracket — White",
    "jewel_ruby": "Jewel Panel — Gold",
    "jewel_sapphire": "Jewel Panel — Silver",
    "jewel_emerald": "Jewel Panel — White",
    "jewel_gold": "Jewel Panel — Heavy Gold",
    "jewel_silver": "Jewel Panel — Fine Silver",
    "jewel_lavender": "Jewel Panel — Soft Violet",
    "jewel_sunset": "Jewel Panel — Warm Gold",
    "jewel_mint": "Jewel Panel — Pale Mint",
    "frame_minimal_gold": "Minimal — Double Gold",
    "frame_minimal_white": "Minimal — White Line",
    "frame_silver_thin": "Minimal — Silver Line",
    "frame_corner_brackets": "Corner Brackets — Gold",
    "frame_corner_silver": "Corner Brackets — Silver",
    "frame_diamond_ends": "Diamond Ends — Gold",
    "frame_art_deco": "Art Deco — Gold",
    "frame_triple_line": "Triple Line — Gold",
    "frame_crescent_ends": "Crescent Ends — Gold",
    "frame_geometric": "Geometric Band — Gold",
    "frame_wide_bracket": "Wide Bracket — Gold",
    "frame_royal_heavy": "Royal Frame — Heavy Gold",
    "frame_gold_underline": "Gold Underline Arc",
}


def _containers_dir() -> Path:
    from app_paths import base_dir
    d = base_dir() / "assets" / "name_containers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_name_containers() -> list[tuple[str, str, Path | None]]:
    items: list[tuple[str, str, Path | None]] = [("none", "None", None)]
    directory = _containers_dir()
    for path in sorted(directory.glob("*.png")):
        if path.stem.startswith("custom_"):
            label = f"Custom: {path.stem.replace('custom_', '').replace('_', ' ').title()}"
        else:
            label = _LABELS.get(path.stem, path.stem.replace("_", " ").title())
        items.append((path.stem, label, path))
    return items


def load_container(stem: str, custom: Path | None = None) -> Image.Image | None:
    if stem == "none" or not stem:
        return None
    if custom and custom.exists():
        return Image.open(custom).convert("RGBA")
    path = _containers_dir() / f"{stem}.png"
    if not path.exists():
        return None
    return Image.open(path).convert("RGBA")


def _apply_frame_opacity(frame: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 0.999:
        return frame
    opacity = max(0.05, min(1.0, opacity))
    out = frame.copy()
    alpha = out.getchannel("A").point(lambda a: int(a * opacity))
    out.putalpha(alpha)
    return out


def fit_container(
    template: Image.Image,
    inner_w: int,
    inner_h: int,
    *,
    width_scale: float = 1.0,
    height_scale: float = 1.0,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Fit frame around glyph; width/height scales add padding without shrinking the SVG."""
    il, it, ir, ib = _INNER
    tw, th = template.size
    base_inner_w = tw * (ir - il)
    base_inner_h = th * (ib - it)
    base_fit_w = inner_w / base_inner_w
    base_fit_h = inner_h / base_inner_h
    fit_w = base_fit_w * max(0.55, width_scale)
    fit_h = base_fit_h * max(0.55, height_scale)
    cw = max(1, int(tw * fit_w))
    ch = max(1, int(th * fit_h))
    scaled = template.resize((cw, ch), Image.Resampling.LANCZOS)
    inner = (int(cw * il), int(ch * it), int(cw * ir), int(ch * ib))
    return scaled, inner


def compose_name_block(
    container: Image.Image,
    inner_box: tuple[int, int, int, int],
    glyph: Image.Image,
    *,
    frame_opacity: float = 1.0,
) -> Image.Image:
    """Paste glyph centred inside container; frame opacity does not fade the glyph."""
    frame = _apply_frame_opacity(container, frame_opacity)
    block = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    block.alpha_composite(frame)

    ix1, iy1, ix2, iy2 = inner_box
    iw, ih = ix2 - ix1, iy2 - iy1
    gw, gh = glyph.size
    gx = ix1 + (iw - gw) // 2
    gy = iy1 + (ih - gh) // 2
    block.alpha_composite(glyph, (gx, gy))
    return block
