# Quran Thumbnail Generator

Generate YouTube-style Quranic recitation thumbnails.

## Quick start

```powershell
python -m pip install -r requirements.txt
python setup_fonts.py
python setup_backgrounds.py
python generate_banners.py
python setup_reciter_photos.py
python app.py
```

Or double-click **`run.bat`**.

## Features

- **Stylized surah names** — auto-loaded SVG from `https://cdn.amrayn.com/qimages-c/{number}.svg` for all 114 surahs
- **Original fonts restored** — Amiri (Arabic fallback), Montserrat (English/reciter)
- **Draggable preview** — drag blue handle (text block) and gold handle (reciter photo); export matches layout
- **Reciter photos** — add via **Add reciter photo...** or Manage dialog; toggle overlay on thumbnail
- **13 corner banners** — 5 classic + 8 Islamic geometric styles + custom PNG upload
- **Per-text colors**, batch export, nature backgrounds, dark UI theme

## Preview controls

| Handle | Action |
|--------|--------|
| Blue circle | Move entire text stack (Arabic SVG, English, reciter name, badge) |
| Gold rectangle | Move reciter portrait overlay |
| Reset layout positions | Restore default placement |

## Custom corner banner

Click **Upload custom banner...** and select a PNG with transparent corners. It is saved to `assets/banners/` and appears in the banner dropdown.

## Dependencies

- **PyMuPDF** — renders Amrayn SVG surah names on Windows (no Cairo required)
