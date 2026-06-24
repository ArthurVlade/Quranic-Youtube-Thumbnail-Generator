# Quranic YouTube Thumbnail Generator

I built this because I wanted a fast, repeatable way to make **cinematic YouTube thumbnails for Quranic recitation videos** — without opening Photoshop every time. You pick a surah, choose a reciter and background, drag the text until it looks right, and export a crisp PNG. That is the whole idea: **professional-looking thumbnails in minutes, not hours.**

The app runs at **1280×720** in the preview and exports **HD, Full HD, or true 4K** when you need it. Everything you customize — colors, layout, banners, reciter photos, language — is saved between sessions. To keep every thumbnail feeling fresh, **Fetch fresh (online)** pulls a new random 4K background from the internet — no API key required.

![App icon](assets/icon.png)

### Sample output — Surah Al-Ma'idah

<img width="3840" height="2160" alt="Sample 4K thumbnail export" src="https://github.com/user-attachments/assets/6e60c469-3041-4fc5-8bb2-5bcd225718f2" />

*Example 4K export. You can also export HD (1280×720) or Full HD (2560×1440) from the Export tab.*

In-app screenshots:

<img width="1325" height="819" alt="image" src="https://github.com/user-attachments/assets/75e3093b-161b-44ac-adf3-36ff19f079b9" />



<img width="1325" height="817" alt="image" src="https://github.com/user-attachments/assets/97e5da99-d555-4a1b-a939-c7a2bdb3ff47" />


---

## What this does for you

If you upload recitation videos to YouTube (or anywhere else), this tool helps you:

- **Stay consistent** — same layout, fonts, and style across every video in a series
- **Look polished** — stylized Arabic surah art, soft glow, nature backgrounds, optional Islamic corner banners
- **Work in your language** — the app UI and default thumbnail text support **47 languages**; switch anytime from the header
- **Batch a full series** — export thumbnails for surahs 1–114 (or any range) in one go
- **Move things visually** — drag each text layer in the live preview instead of guessing pixel values
- **Never repeat a background** — random scenery from 500+ local images, or fetch a brand-new 4K photo online

The **Arabic surah name art always comes from the same high-quality SVG source** (Amrayn). What changes with language is the **menu**, the **localized title under the Arabic**, **reciter names**, and **background category labels** — not the calligraphy itself.

---

## Install (Windows — easiest way)

You do **not** need Python for the installer build.

1. Download **`QuranThumbnailGenerator-Setup.exe`** from the [Releases](../../releases) page (or build it yourself — see below).
2. Run the installer and follow the wizard.
3. Open **Quran Thumbnail Generator** from the Start Menu.

Fonts, banners, and core assets are bundled. On first launch the app may download extra scenery (and any missing fonts) once — that needs internet a single time.

Your settings, custom banners, and reciter photos are stored here:

`%LOCALAPPDATA%\QuranThumbnailGenerator`

---

## Install from source (run or hack on the code)

You need **Python 3.10+** on Windows. When you install Python, tick **Add Python to PATH**.

1. Clone the repo:

   ```powershell
   git clone https://github.com/ArthurVlade/Quranic-Youtube-Thumbnail-Generator.git
   cd Quranic-Youtube-Thumbnail-Generator
   ```

2. Double-click **`setup.bat`**.  
   It creates a virtual environment, installs dependencies, downloads fonts (including CJK/script fonts), banners, scenery, and the app icon. The full scenery library takes a while — let it finish.

3. Launch anytime with **`run.bat`**.

Prefer the terminal? See [Manual setup](#manual-setup-any-os) below.

---

## Build the installer yourself

To ship **`QuranThumbnailGenerator-Setup.exe`** to others:

1. Install [Python 3.10+](https://www.python.org/downloads/) and [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Clone the repo and run **`build_installer.bat`** once.
3. Output: `Output\QuranThumbnailGenerator-Setup.exe`

That script installs build tools, prepares assets, bundles the app with PyInstaller, and compiles the Inno Setup installer.

### Portable folder (no installer wizard)

1. Run **`setup.bat`**, then **`build.bat`**.
2. Copy **`dist\QuranThumbnailGenerator\`** anywhere and run **`QuranThumbnailGenerator.exe`**.

---

## Quick start

Once the app is open:

1. **Language** (top of the settings panel) → click **Change language…** if you want the UI in another language. English is the default.
2. **Surah** tab → pick a surah; I fill the Arabic name, localized title, and number.
3. **Reciter** tab → choose a collection, set the name on the thumbnail, optionally add a photo overlay.
4. **Style** tab → colors, typography sizes, optional **surah name container** (frame around Arabic only).
5. **Background** tab → filter by Forests, Mountains, Lakes, etc., or use **Random scenery** / **Fetch fresh (online)**.
6. **Banners** tab → optional Islamic corner ornaments; upload your own PNG if you like.
7. Drag the **colored handles** on the preview to move each layer, or drag the canvas to move the whole block.
8. **Export** tab → HD / Full HD / 4K → **Export PNG** (`Ctrl+S`) or **Batch export** (`Ctrl+E`).

Corner banners are off by default — turn them on under **Banners** when you want them.

---

## Features

### Thumbnail design

- **Stylized surah names** — high-resolution SVG (3× supersampled) for all 114 surahs from [Amrayn](https://www.amrayn.com/)
- **Surah name containers** — transparent ornate frames around the Arabic only; English/localized title, reciter, and badge stay below
- **Independent text layers** — move Arabic, title, reciter name, and surah badge separately
- **Soft glow, colors, and typography** — per-layer colors and size sliders
- **HD / Full HD / 4K export** — 1280×720, 2560×1440, or 3840×2160
- **Resizable corner banners** — classic and geometric styles; upload custom PNG corners
- **Reciter photo overlays** — save photo groups per reciter; drag portraits on the thumbnail
- **Batch export** — export a surah range with a progress bar and consistent naming

### Backgrounds

- **500+ categorised nature backgrounds** — Forests, Mountains, Lakes, Springs, and more
- **Random scenery** and **Fetch fresh (online)** for new 4K images on demand
- **Custom image** or **reciter photo** as the full background
- **Overlay opacity** slider for readability over busy photos

### Languages (47 supported)

I added full internationalization so more people can use the tool comfortably:

| Region | Languages |
|--------|-----------|
| **Europe** | English, German, French, Spanish, Portuguese, Italian, Dutch, Polish, Romanian, Czech, Slovak, Hungarian, Bulgarian, Croatian, Slovenian, Estonian, Latvian, Lithuanian, Finnish, Swedish, Danish, Greek, Irish, Maltese, Ukrainian, Russian, Turkish, Norwegian, Icelandic, Catalan, Albanian, Serbian, Bosnian, Macedonian, Belarusian, Luxembourgish, Welsh |
| **Asia & Middle East** | Arabic, Urdu, Bengali, Hindi, Chinese, Japanese, Korean, Persian, Indonesian, Malay |

What localizes:

- **App menus and settings** (tabs, buttons, hints, dialogs)
- **Default surah title** on the thumbnail when you pick a surah
- **Reciter names** (built-in reciters)
- **Background category buttons**

What stays the same across languages:

- **Arabic surah SVG art** (the calligraphy at the top)

Change language anytime: **Language: … · Change language…** in the header. Your choice is remembered.

### Script support on thumbnails

Titles and reciter names render in the correct script in **preview and export** — not empty boxes:

- **Chinese, Japanese, Korean** (Noto Sans SC / JP / KR)
- **Arabic, Urdu, Persian** (Noto Naskh Arabic + shaping)
- **Hindi** (Devanagari), **Bengali**, **Cyrillic**, **Greek**, and Latin European text

If you run from source and see boxes for CJK text, run **`python setup_fonts.py`** once to download the script fonts.

### App experience

- **Modern dark UI** with a custom Windows title bar and proper taskbar icon (installed build)
- **Live draggable preview** with layer handles and keyboard nudging
- **Settings persist** — layout, colors, language, last surah, backgrounds
- **Single-instance guard** — launching again focuses the existing window
- **First-run asset download** (installed build) — missing fonts/scenery fetched automatically in the background

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Export PNG |
| `Ctrl+E` | Batch export |
| `Ctrl+R` / `F5` | Refresh preview |
| Arrow keys | Nudge the text block |
| Double-click a handle | Reset that element |

## Preview handles

| Handle (left edge) | Moves |
|--------------------|--------|
| Blue **SVG** | Arabic surah name |
| Yellow **Title** | Localized / English title |
| Green **Reciter** | Reciter name |
| Gold **Badge** | Surah number badge |
| Drag elsewhere on preview | Whole text block |
| Gold dashed box | Reciter photo overlay |

Hover a name container in the preview for **↔ width**, **↕ height**, and **⧉ uniform padding** handles.

---

## Manual setup (any OS)

If you skip `setup.bat`:

```bash
python -m pip install -r requirements.txt
python setup_fonts.py
python setup_backgrounds.py
python generate_banners.py
python generate_name_containers.py
python setup_reciter_photos.py
python make_icon.py
python app.py
```

To refresh or expand the scenery library later:

```bash
python setup_backgrounds.py
python clean_backgrounds.py
```

To regenerate locale files after editing translations:

```bash
python generate_locales.py
```

---

## What I used to build it

| Library | Role |
|---------|------|
| **Pillow** | Image composition and PNG export |
| **PyMuPDF** | Renders Amrayn SVG surah names (no Cairo on Windows) |
| **arabic-reshaper** + **python-bidi** | Arabic / RTL shaping |
| **tkinter** | GUI (included with Python) |
| **PyInstaller** | Standalone `.exe` (build only) |
| **Inno Setup** | Windows installer (build only) |

---

## Project layout

| File | What it does |
|------|----------------|
| `app.py` | Main GUI |
| `thumbnail_generator.py` | Renders thumbnails (scale-aware for HD/4K) |
| `preview_canvas.py` | Draggable live preview |
| `surah_svg.py` | Fetches and rasterizes surah SVGs |
| `name_containers.py` | Ornate frames around the Arabic name |
| `i18n.py` | Localization API |
| `language_picker.py` | Searchable language chooser |
| `script_fonts.py` | Script-aware fonts for thumbnail text |
| `generate_locales.py` | Builds `locales/*.json` |
| `locales/` | UI + surah + reciter translations (47 languages) |
| `win_chrome.py` | Custom title bar + taskbar on Windows |
| `app_paths.py` | Paths for source vs installed `.exe` |
| `settings_store.py` / `reciter_store.py` | Saved settings and reciter data |
| `first_run_assets.py` | Background download for installed builds |
| `setup.bat` / `run.bat` | One-time setup and launch |
| `build.bat` / `build_installer.bat` | Build portable app or Setup.exe |
| `assets/samples/` | Example exports (including the README preview) |

---

## Troubleshooting

**Preview is blank or options do nothing**  
Run `setup.bat` again so fonts and banners exist. Check that `assets/fonts` and `assets/banners` are populated.

**Chinese / Japanese / Korean text shows boxes in preview or export**  
Run `python setup_fonts.py` to download Noto CJK fonts. Restart the app.

**Background list is empty or small**  
Run `python setup_backgrounds.py` (or full `setup.bat`). The full background library is not in git — you generate it locally after clone.

**Some menu items still appear in English**  
Not every string is fully translated in every language yet; core tabs and settings are covered for major languages, and more are added over time. The app always falls back to English for missing keys.

**Taskbar shows the Python icon when running from source**  
Normal for `run.bat`. The installed `.exe` uses the app icon and shows as **Quran Thumbnail Generator** in Task Manager.

**Want the normal Windows title bar**  
Add `"native_titlebar": true` to `data/settings.json`.

---

## License & feedback

Use it, fork it, improve it. If something breaks or you want a feature, [open an issue](https://github.com/ArthurVlade/Quranic-Youtube-Thumbnail-Generator/issues) — I am happy to keep making this better for everyone who uploads recitation content.
