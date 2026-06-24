"""Download premium open fonts into assets/fonts."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

from text_fonts import FONT_DOWNLOADS


def main() -> None:
    fonts_dir = Path(__file__).resolve().parent / "assets" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    ok = fail = 0
    for name, url in FONT_DOWNLOADS.items():
        dest = fonts_dir / name
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"Already present: {name}")
            ok += 1
            continue
        print(f"Downloading {name}...")
        try:
            urlretrieve(url, dest)
            print(f"Saved {dest}")
            ok += 1
        except Exception as exc:
            print(f"Could not download {name}: {exc}")
            fail += 1

    print(f"\nDone — {ok} fonts ready, {fail} failed.")


if __name__ == "__main__":
    main()
