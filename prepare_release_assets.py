"""Prepare assets before building the Windows installer.

Ensures fonts, banners, icon, and a validated scenery library exist so the
installer ships a complete, offline-ready app.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run(script: str, *args: str) -> None:
    cmd = [sys.executable, str(ROOT / script), *args]
    print(f">>> {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=ROOT)


def main() -> None:
    print("=== Preparing release assets ===\n")

    _run("make_icon.py")

    fonts_dir = ROOT / "assets" / "fonts"
    if not any(fonts_dir.glob("*.ttf")):
        _run("setup_fonts.py")
    else:
        print("Fonts already present — skipping download.")

    banners_dir = ROOT / "assets" / "banners"
    if not any(banners_dir.glob("*.png")):
        _run("generate_banners.py")
    else:
        print("Banners already present — skipping generation.")

    bg_dir = ROOT / "assets" / "backgrounds"
    bg_count = len(list(bg_dir.glob("*.jpg"))) if bg_dir.exists() else 0
    if bg_count < 100:
        print(f"Only {bg_count} backgrounds — downloading starter library (120 images)…")
        _run("setup_backgrounds.py", "120")
    else:
        print(f"{bg_count} backgrounds present — skipping bulk download.")

    if (ROOT / "clean_backgrounds.py").exists():
        _run("clean_backgrounds.py")

    final = len(list(bg_dir.glob("*.jpg"))) if bg_dir.exists() else 0
    print(f"\n=== Ready to build — {final} backgrounds, fonts, banners, icon ===")


if __name__ == "__main__":
    main()
