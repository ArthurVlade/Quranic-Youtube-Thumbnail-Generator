# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Quran Thumbnail Generator.

Build with:   pyinstaller quran_thumbnail.spec --noconfirm
Output:       dist/QuranThumbnailGenerator/QuranThumbnailGenerator.exe  (onedir)
"""

from pathlib import Path

block_cipher = None

PROJECT = Path(SPECPATH)

# Bundle the whole assets tree (fonts, banners, backgrounds, surah svg cache, icon)
datas = [
    (str(PROJECT / "assets"), "assets"),
]

a = Analysis(
    ["app.py"],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PIL._tkinter_finder",
        "arabic_reshaper",
        "bidi",
        "bidi.algorithm",
        "fitz",
        "first_run_assets",
        "image_quality",
        "app_paths",
        "settings_store",
        "reciter_store",
        "win_chrome",
        "preview_canvas",
        "ui_theme",
        "surahs",
        "surah_svg",
        "thumbnail_generator",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["numpy", "scipy", "pytest", "tkinter.test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="QuranThumbnailGenerator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                 # GUI app — no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT / "assets" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="QuranThumbnailGenerator",
)
