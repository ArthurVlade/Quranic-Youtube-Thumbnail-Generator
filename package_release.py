"""Build release artifacts for GitHub (portable zip + optional installer)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = "1.3.1"
APP_DIR = ROOT / "dist" / "QuranThumbnailGenerator"
EXE = APP_DIR / "QuranThumbnailGenerator.exe"
OUTPUT = ROOT / "Output"
PORTABLE_ZIP = OUTPUT / f"QuranThumbnailGenerator-{VERSION}-windows-x64.zip"
SETUP_EXE = OUTPUT / "QuranThumbnailGenerator-Setup.exe"


def _run(cmd: list[str]) -> None:
    print(">>>", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def build_app() -> None:
    vpy = ROOT / ".venv" / "Scripts" / "python.exe"
    if not vpy.exists():
        vpy = Path(sys.executable)
    _run([str(vpy), str(ROOT / "prepare_release_assets.py")])
    _run([str(vpy), "-m", "PyInstaller", "quran_thumbnail.spec", "--noconfirm", "--clean"])
    if not EXE.exists():
        raise SystemExit(
            f"Expected executable missing: {EXE}\n"
            "PyInstaller finished but the output path does not match quran_thumbnail.spec."
        )


def zip_portable() -> Path:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if PORTABLE_ZIP.exists():
        PORTABLE_ZIP.unlink()
    with zipfile.ZipFile(PORTABLE_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(APP_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, Path(APP_DIR.name) / path.relative_to(APP_DIR))
    size_mb = PORTABLE_ZIP.stat().st_size / (1024 * 1024)
    print(f"Portable zip: {PORTABLE_ZIP} ({size_mb:.1f} MB)")
    return PORTABLE_ZIP


def try_installer() -> Path | None:
    iscc = shutil.which("iscc")
    for candidate in (
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ):
        if candidate.exists():
            iscc = str(candidate)
            break
    if not iscc:
        print("Inno Setup not found — skipping Setup.exe (portable zip still ready).")
        return None
    _run([iscc, str(ROOT / "installer.iss")])
    if not SETUP_EXE.exists():
        raise SystemExit(f"Inno Setup finished but installer missing: {SETUP_EXE}")
    size_mb = SETUP_EXE.stat().st_size / (1024 * 1024)
    print(f"Installer: {SETUP_EXE} ({size_mb:.1f} MB)")
    return SETUP_EXE


def main() -> None:
    print(f"=== Packaging Quran Thumbnail Generator v{VERSION} ===\n")
    build_app()
    zip_portable()
    try_installer()
    print("\n=== Release artifacts in Output\\ ===")
    for path in sorted(OUTPUT.glob("*")):
        if path.is_file():
            print(f"  {path.name}")


if __name__ == "__main__":
    main()
