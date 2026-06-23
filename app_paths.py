"""Centralised path handling for both source runs and frozen (PyInstaller) builds.

- When running from source, everything lives in the project directory (unchanged
  behaviour).
- When running as a frozen .exe, read-only resources are unpacked by PyInstaller
  into a temp dir (``sys._MEIPASS``), while user-writable data (settings, reciter
  photos, custom banners, SVG cache, downloaded backgrounds) must live somewhere
  persistent — we use ``%LOCALAPPDATA%\\QuranThumbnailGenerator``.

On first frozen launch, bundled assets are copied into the writable base so the
rest of the code can treat a single base directory as both source and target.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "QuranThumbnailGenerator"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_dir() -> Path:
    """Directory containing bundled, read-only resources."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def base_dir() -> Path:
    """Writable base directory used for assets and data at runtime."""
    if is_frozen():
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP_NAME
        root.mkdir(parents=True, exist_ok=True)
        return root
    return Path(__file__).resolve().parent


def ensure_initialized() -> None:
    """On frozen first run, seed the writable base with bundled assets."""
    if not is_frozen():
        return
    src = bundle_dir() / "assets"
    dst = base_dir() / "assets"
    if src.exists():
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.rglob("*"):
            rel = item.relative_to(src)
            target = dst / rel
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(item, target)
                except OSError:
                    pass


def resource_path(*parts: str) -> Path:
    """Read-only bundled resource (falls back to writable base if present)."""
    candidate = bundle_dir().joinpath(*parts)
    if candidate.exists():
        return candidate
    return base_dir().joinpath(*parts)
