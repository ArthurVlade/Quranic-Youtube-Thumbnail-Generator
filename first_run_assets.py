"""First-run asset provisioning for the frozen (installed) application.

End users do not need Python — this module runs inside the bundled .exe and
downloads any missing fonts or scenery over the network on first launch.
"""

from __future__ import annotations

import threading
from pathlib import Path
from urllib.request import Request, urlopen

from app_paths import base_dir, is_frozen
from image_quality import is_good_bytes

# Minimum scenery count before we offer a background download
MIN_BACKGROUNDS = 40

# Fonts required for thumbnail text (same URLs as setup_fonts.py)
FONTS: dict[str, str] = {
    "Amiri-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Bold.ttf",
    "Cinzel-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",
    "CormorantGaramond-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
}

# One clean 4K image per category for a fast starter library
STARTER_SCENERY: list[tuple[str, int]] = [
    ("mountain", 1001),
    ("forest", 2002),
    ("lake", 3003),
    ("spring", 4004),
    ("valley", 5005),
    ("sky", 6006),
    ("meadow", 7007),
    ("desert", 8008),
    ("beach", 9009),
    ("autumn", 1010),
    ("winter", 1111),
]


def _fonts_dir() -> Path:
    return base_dir() / "assets" / "fonts"


def _backgrounds_dir() -> Path:
    d = base_dir() / "assets" / "backgrounds"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _count_backgrounds() -> int:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return sum(
        1 for p in _backgrounds_dir().glob("*")
        if p.is_file() and p.suffix.lower() in exts and p.stat().st_size > 15_000
    )


def missing_fonts() -> list[str]:
    fonts_dir = _fonts_dir()
    fonts_dir.mkdir(parents=True, exist_ok=True)
    missing = []
    for name in FONTS:
        dest = fonts_dir / name
        if not dest.exists() or dest.stat().st_size < 1000:
            missing.append(name)
    return missing


def needs_scenery_download() -> bool:
    return _count_backgrounds() < MIN_BACKGROUNDS


def needs_any_download() -> bool:
    return bool(missing_fonts()) or needs_scenery_download()


def _download_url(url: str, dest: Path, timeout: int = 60) -> bool:
    try:
        req = Request(url, headers={"User-Agent": "QuranThumbnailGenerator/3.0"})
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if dest.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            if not is_good_bytes(data):
                return False
        elif len(data) < 1000:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def download_assets(progress=None) -> tuple[int, int]:
    """Download missing fonts and starter scenery. Returns (ok, failed)."""
    ok = fail = 0

    fonts_dir = _fonts_dir()
    missing = missing_fonts()
    for i, name in enumerate(missing):
        if progress:
            progress(f"Downloading font {name} ({i + 1}/{len(missing)})…")
        url = FONTS[name]
        if _download_url(url, fonts_dir / name):
            ok += 1
        else:
            fail += 1

    if needs_scenery_download():
        bg_dir = _backgrounds_dir()
        total = len(STARTER_SCENERY)
        for i, (prefix, seed) in enumerate(STARTER_SCENERY):
            name = f"{prefix}_starter_{seed}.jpg"
            dest = bg_dir / name
            if dest.exists() and dest.stat().st_size > 15_000:
                ok += 1
                continue
            if progress:
                progress(f"Downloading scenery {i + 1}/{total} ({prefix})…")
            url = f"https://picsum.photos/seed/qtg{seed}/3840/2160"
            if _download_url(url, dest):
                ok += 1
            else:
                fail += 1

    return ok, fail


def start_background_download(on_progress, on_done) -> threading.Thread:
    """Run download_assets in a daemon thread."""

    def worker():
        try:
            ok, fail = download_assets(on_progress)
            on_done(ok, fail, "")
        except Exception as exc:
            on_done(0, 1, str(exc))

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t


def ensure_frozen_assets(on_progress=None, on_done=None) -> None:
    """If frozen and assets are missing, download them (blocking or threaded)."""
    if not is_frozen() or not needs_any_download():
        if on_done:
            on_done(0, 0)
        return
    if on_progress and on_done:
        start_background_download(on_progress, on_done)
    else:
        download_assets(on_progress)
