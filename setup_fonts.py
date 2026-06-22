"""Download premium open fonts into assets/fonts."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

# Variable-font builds from Google Fonts (static/ paths were removed upstream).
FONTS = {
    "Amiri-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Bold.ttf",
    "Cinzel-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",
    "CormorantGaramond-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
    "PlayfairDisplay-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "JosefinSans-Variable.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/josefinsans/JosefinSans%5Bwght%5D.ttf",
}


def main() -> None:
    fonts_dir = Path(__file__).resolve().parent / "assets" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    for name, url in FONTS.items():
        dest = fonts_dir / name
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"Already present: {name}")
            continue
        print(f"Downloading {name}...")
        try:
            urlretrieve(url, dest)
            print(f"Saved {dest}")
        except Exception as exc:
            print(f"Could not download {name}: {exc}")


if __name__ == "__main__":
    main()
