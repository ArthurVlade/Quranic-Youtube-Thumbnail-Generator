# Quran Thumbnail Generator

Generate cinematic, YouTube-style Quranic recitation thumbnails (1280×720, exportable up to 4K) with stylized Arabic surah names, English titles, reciter names, surah-number badges, nature backgrounds, and Islamic corner banners.

![icon](assets/icon.png)

## Install & run (Windows)

### Option 1 — One-click setup from source (recommended for tinkering)

1. Install [Python 3.10+](https://www.python.org/downloads/) (tick **Add Python to PATH**).
2. Double-click **`setup.bat`** — this creates an isolated virtual environment, installs all dependencies, and downloads fonts, backgrounds, banners and the app icon.
3. Launch any time with **`run.bat`**.

### Option 3 — Windows installer for end users (`Setup.exe`)

**For you (build once on a PC with Python + Inno Setup):**

1. Install [Python 3.10+](https://www.python.org/downloads/) and [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Double-click **`build_installer.bat`** — this installs build tools, prepares fonts/banners/scenery, bundles the app with PyInstaller, and compiles the installer.
3. Share **`Output\QuranThumbnailGenerator-Setup.exe`** with anyone.

**For your users (no Python needed):**

1. Run **`QuranThumbnailGenerator-Setup.exe`**.
2. Follow the wizard (installs to Program Files, optional desktop shortcut).
3. Launch from the Start Menu — on first run the app may download extra scenery over the internet if not bundled.

> All Python libraries (Pillow, PyMuPDF, etc.) are **inside the installer** — users never install pip packages. Settings and custom assets live in `%LOCALAPPDATA%\QuranThumbnailGenerator`.

### Option 2 — Standalone folder (no installer)

1. Run **`build.bat`** (or run Option 3 steps 1–2 and skip Inno Setup).
2. Copy the folder `dist\QuranThumbnailGenerator\` to any Windows PC and run `QuranThumbnailGenerator.exe`.

> When packaged, user data (settings, reciters, custom banners, cached SVGs) is stored in `%LOCALAPPDATA%\QuranThumbnailGenerator` so it persists across updates.

## Features

- **Stylized surah names** — high-resolution SVG (3× supersampled) auto-loaded for all 114 surahs; pick a surah and the Arabic name, English title and number fill in automatically.
- **HD / Full HD / 4K export** — render at 1280×720, 2560×1440, or 3840×2160 with crisp text and smooth badge/banner edges.
- **Independent text layers** — move the Arabic SVG, English title, reciter name, and number badge separately via colored drag-handles, or move the whole block together. Center-snap and alignment guides included.
- **Per-element sizing & colors** — sliders for each element's size; color pickers for every text item and the badge.
- **500+ categorised nature backgrounds** — Forests, Mountains, Lakes, Springs, and more, filterable in-app (run `setup_backgrounds.py` / `setup.bat` to populate the full library); or load your own image.
- **Fetch fresh scenery** — pull a brand-new random nature image on demand so your thumbnails stay unique.
- **Resizable Islamic corner banners** — classic + geometric styles (off by default), correctly mirrored into all four corners, with a size slider; upload your own PNG.
- **Reciter photo overlays** — manage reciter collections and drag a portrait onto the thumbnail.
- **Batch export** — generate a whole range of surahs at once with a progress bar.
- **Modern dark UI** — flat, gold-accented theme with a custom title bar (the app shows its own icon in the taskbar). Set `"native_titlebar": true` in `data/settings.json` to fall back to the native window frame.
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
| `first_run_assets.py` | First-launch font/scenery download (installed app) |
| `prepare_release_assets.py` | Prepares assets before building the installer |
| `image_quality.py` / `clean_backgrounds.py` | Scenery validation and cleanup |
| `setup.bat` / `run.bat` | Developer setup & launch (needs Python) |
| `build.bat` | Build standalone folder (`dist\…`) |
| `build_installer.bat` | **Build `Output\QuranThumbnailGenerator-Setup.exe`** |
| `quran_thumbnail.spec` / `installer.iss` | PyInstaller + Inno Setup configs |
