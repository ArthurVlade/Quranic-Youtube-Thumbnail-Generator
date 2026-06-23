# Quranic YouTube Thumbnail Generator

I built this tool to create cinematic, YouTube-style Quranic recitation thumbnails — 1280×720 by default, exportable up to 4K. Pick a surah and it fills in the Arabic name, English title, and number automatically. You can style the text, choose nature backgrounds, add optional corner banners, overlay a reciter photo, drag everything into place, and batch-export a whole series.

![icon](assets/icon.png)

### Sample output (Surah Al-Ma'idah)

![Sample thumbnail — 005 Surah Al-Ma'idah](docs/samples/005_surah_al-maidah.png)

*Export filename example: `005_Surah_Al-Ma'idah.png` at Full HD (2560×1440).*

---

## Install (Windows — easiest way)

**You do not need Python installed for this.**

1. Download **`QuranThumbnailGenerator-Setup.exe`** from the [Releases](../../releases) page (or build it yourself — see below).
2. Run the installer and follow the wizard.
3. Open **Quran Thumbnail Generator** from the Start Menu (I added an optional desktop shortcut in the installer).

Everything is bundled — Pillow, PyMuPDF, fonts, banners, and scenery. On first launch the app may download extra background images if they were not included in your build; that only needs an internet connection once.

Your settings, custom banners, and reciter photos are saved in:

`%LOCALAPPDATA%\QuranThumbnailGenerator`

---

## Install from source (if you want to run or modify the code)

You need **Python 3.10+** on Windows. During install, tick **Add Python to PATH**.

1. Clone this repo:

   ```powershell
   git clone https://github.com/ArthurVlade/Quranic-Youtube-Thumbnail-Generator.git
   cd Quranic-Youtube-Thumbnail-Generator
   ```

2. Double-click **`setup.bat`**.  
   This creates a virtual environment, installs dependencies from `requirements.txt`, and downloads fonts, banners, scenery, and the app icon. The full scenery library takes a while — let it finish.

3. Launch the app anytime with **`run.bat`**.

That is all you need to use it locally. No manual `pip` steps unless you prefer the terminal (see [Manual setup](#manual-setup-any-os) below).

---

## Build the installer yourself

If you want to produce **`QuranThumbnailGenerator-Setup.exe`** to share with others:

1. Install [Python 3.10+](https://www.python.org/downloads/) and [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Clone the repo and run **`build_installer.bat`** once.
3. Grab the output from:

   `Output\QuranThumbnailGenerator-Setup.exe`

That script installs build tools, prepares assets, bundles the app with PyInstaller, and compiles the Inno Setup installer. Share that single file — recipients do not need Python.

### Standalone folder (no installer wizard)

If you only want a portable folder instead of a Setup.exe:

1. Run **`setup.bat`**, then **`build.bat`**.
2. Copy **`dist\QuranThumbnailGenerator\`** to any PC and run **`QuranThumbnailGenerator.exe`**.

---

## Quick start after install

1. Open the **Surah** tab → pick a surah (names and number auto-fill).
2. Set your **reciter name** and tweak **Style** (sizes, colors, glow).
3. Pick a **Background** (filter by Forests, Mountains, Lakes, etc.) or use **Random scenery** / **Fetch fresh (online)**.
4. On the **Style** tab, optionally pick a **Surah name container** — the ornate frame wraps the Arabic name only.
5. Drag the colored tabs on the preview to position each text layer, or drag the canvas to move the whole block.
6. **Export** tab → choose HD / Full HD / 4K → **Export PNG** (`Ctrl+S`) or **Batch export** (`Ctrl+E`).

Corner banners are off by default. Enable them on the **Banners** tab if you want the Islamic corner ornaments.

---

## Features

- **Stylized surah names** — high-resolution SVG (3× supersampled) for all 114 surahs from Amrayn
- **Surah name containers** — 32 transparent outline frames; Arabic sits inside, everything else below
- **HD / Full HD / 4K export** — crisp text and badges at 1280×720, 2560×1440, or 3840×2160
- **Independent text layers** — move Arabic SVG, English title, reciter name, and badge separately
- **500+ categorised nature backgrounds** — Forests, Mountains, Lakes, Springs, and more
- **Fetch fresh scenery** — download a unique random image on demand
- **Resizable corner banners** — classic and geometric styles; upload your own PNG
- **Reciter photo overlays** — save collections and drag portraits onto the thumbnail
- **Batch export** — export a range of surahs with a progress bar
- **Modern dark UI** — custom title bar and taskbar icon; settings persist between sessions

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
| Yellow **Title** | English title |
| Green **Reciter** | Reciter name |
| Gold **Badge** | Surah number badge |
| Drag elsewhere on preview | Whole text block |
| Gold dashed box | Reciter photo overlay |

---

## Manual setup (any OS)

If you prefer the terminal over `setup.bat`:

```bash
python -m pip install -r requirements.txt
python setup_fonts.py
python setup_backgrounds.py
python generate_banners.py
python setup_reciter_photos.py
python make_icon.py
python app.py
```

To refresh or expand the scenery library later:

```bash
python setup_backgrounds.py
python clean_backgrounds.py
```

---

## What this is built with

| Library | Role |
|---------|------|
| **Pillow** | Image composition and PNG export |
| **PyMuPDF** | Renders Amrayn SVG surah names (no Cairo on Windows) |
| **arabic-reshaper** + **python-bidi** | Arabic shaping and direction |
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
| `app_paths.py` | Paths for source vs installed `.exe` |
| `settings_store.py` / `reciter_store.py` | Saved settings and reciter data |
| `setup.bat` / `run.bat` | One-time setup and launch |
| `build.bat` / `build_installer.bat` | Build portable app or Setup.exe |
| `setup_*.py`, `generate_banners.py`, `make_icon.py` | Asset download and generation |

---

## Troubleshooting

**Preview is blank or options do nothing**  
Run `setup.bat` again so fonts and banners exist. Check that `assets/fonts` and `assets/banners` are populated.

**Background list is empty or small**  
Run `python setup_backgrounds.py` (or full `setup.bat`). Backgrounds are not stored in git — you generate them locally after clone.

**Taskbar shows the Python icon when running from source**  
That is normal for `run.bat`. The installed `.exe` uses the app icon.

**Want the normal Windows title bar**  
Add `"native_titlebar": true` to `data/settings.json`.

---

## Pushing changes to GitHub

After you edit the project locally, commit and push from the repo folder in PowerShell:

```powershell
cd "C:\Users\Avalon Absolute\Projects\quran-thumbnail-generator"

git status
git add app.py win_chrome.py README.md docs/samples/
git add -u
git status

git commit -m "Fix maximized title bar controls and update README sample output"

git push origin main
```

Replace `main` with your branch name if different (`git branch` shows the current branch).

If `git push` says *Everything up-to-date* but you expected new commits, run `git status` — you may still need `git add` and `git commit` first.

Large generated folders such as `assets/backgrounds/` are gitignored. Sample thumbnails in `docs/samples/` are meant to be committed for the README.

---

If something breaks or you have a feature idea, open an issue on GitHub. I am happy to improve this further.
