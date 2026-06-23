# Quran Thumbnail Generator

Generate cinematic, YouTube-style Quranic recitation thumbnails (1280×720, exportable up to 4K) with stylized Arabic surah names, English titles, reciter names, surah-number badges, nature backgrounds, and Islamic corner banners.

![icon](assets/icon.png)

## Install & run (Windows)

### Option 1 — One-click setup from source (recommended for tinkering)

1. Install [Python 3.10+](https://www.python.org/downloads/) (tick **Add Python to PATH**).
2. Double-click **`setup.bat`** — this creates an isolated virtual environment, installs all dependencies, and downloads fonts, backgrounds, banners and the app icon.
3. Launch any time with **`run.bat`**.

### Option 2 — Build a standalone app (no Python needed by end users)

1. Run **`setup.bat`** once (to get dependencies and assets).
2. Run **`build.bat`** — produces a self-contained app in `dist\QuranThumbnailGenerator\`. Double-click `QuranThumbnailGenerator.exe` to run; copy the folder to any Windows PC.

### Option 3 — Build a Windows installer (.exe)

1. Do Option 2 first (so `dist\QuranThumbnailGenerator\` exists).
2. Install [Inno Setup](https://jrsoftware.org/isdl.php).
3. Open **`installer.iss`** in Inno Setup and click **Compile** (or run `iscc installer.iss`).
4. The installer appears at `Output\QuranThumbnailGenerator-Setup.exe` — it installs to Program Files, adds Start-Menu/desktop shortcuts, and cleanly uninstalls.

> When packaged, user data (settings, reciters, custom banners, cached SVGs) is stored in `%LOCALAPPDATA%\QuranThumbnailGenerator` so it persists across updates.

## Features

- **Stylized surah names** — high-resolution SVG (3× supersampled) auto-loaded for all 114 surahs; pick a surah and the Arabic name, English title and number fill in automatically.
- **HD / Full HD / 4K export** — render at 1280×720, 2560×1440, or 3840×2160 with crisp text and smooth badge/banner edges.
- **Independent text layers** — move the Arabic SVG, English title, reciter name, and number badge separately via colored drag-handles, or move the whole block together. Center-snap and alignment guides included.
- **Per-element sizing & colors** — sliders for each element's size; color pickers for every text item and the badge.
- **70+ categorised nature backgrounds** — Forests, Mountains, Lakes, Springs, Skies, filterable in-app; or load your own image.
- **Resizable Islamic corner banners** — classic + geometric styles, correctly mirrored into all four corners, with a size slider; upload your own PNG.
- **Reciter photo overlays** — manage reciter collections and drag a portrait onto the thumbnail.
- **Batch export** — generate a whole range of surahs at once with a progress bar.
- **Remembers your setup** — colors, sizes, banner, background and quality are restored on next launch.

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Export PNG |
| `Ctrl+E` | Batch export |
| `Ctrl+R` / `F5` | Refresh preview |
| Arrow keys | Nudge text block in preview |
| Double-click handle | Reset that element |

## Preview controls

| Handle (left edge of preview) | Moves |
|--------|--------|
| Blue **SVG** tab | Arabic surah name |
| Yellow **Title** tab | English title |
| Green **Reciter** tab | Reciter name |
| Gold **Badge** tab | Surah number badge |
| Drag anywhere else | The whole text block |
| Gold dashed box | Reciter photo overlay |

## Manual setup (any OS)

```bash
python -m pip install -r requirements.txt
python setup_fonts.py
python setup_backgrounds.py
python generate_banners.py
python setup_reciter_photos.py
python make_icon.py
python app.py
```

## Dependencies

- **Pillow** — image composition and export
- **PyMuPDF** — renders Amrayn SVG surah names on Windows (no Cairo required)
- **arabic-reshaper** + **python-bidi** — correct Arabic shaping/direction
- **PyInstaller** (build only), **Inno Setup** (installer only)

## Project layout

| File | Purpose |
|------|---------|
| `app.py` | Tkinter GUI |
| `thumbnail_generator.py` | Scale-aware rendering engine |
| `preview_canvas.py` | Interactive draggable preview |
| `surah_svg.py` | Surah-name SVG fetch + high-res rasterize |
| `app_paths.py` | Source/frozen path handling |
| `settings_store.py` / `reciter_store.py` | Persisted user data |
| `setup_*.py`, `generate_banners.py`, `make_icon.py` | Asset setup scripts |
| `setup.bat` / `run.bat` / `build.bat` | Windows setup, launch, build |
| `quran_thumbnail.spec` / `installer.iss` | PyInstaller + Inno Setup configs |
