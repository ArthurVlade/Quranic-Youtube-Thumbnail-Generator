"""Download default reciter portrait photos into the collection."""

from __future__ import annotations

import shutil
from pathlib import Path
from urllib.request import Request, urlopen

import reciter_store

# Wikimedia Commons / open portrait sources (thumbnail use)
PORTRAITS: dict[str, str] = {
    "yasser-al-dosari": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Yasser_Al-Dosari.jpg/440px-Yasser_Al-Dosari.jpg",
    "mishary-rashid": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Mishary_Rashid_Alafasy.jpg/440px-Mishary_Rashid_Alafasy.jpg",
    "abdul-basit": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Abdul_Basit_Abdul_Samad_%28cropped%29.jpg/440px-Abdul_Basit_Abdul_Samad_%28cropped%29.jpg",
    "saad-al-ghamdi": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Saad_Al-Ghamdi.jpg/440px-Saad_Al-Ghamdi.jpg",
    "muhammad-al-luhaidan": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Muhammad_Ayyub_%28cropped%29.jpg/440px-Muhammad_Ayyub_%28cropped%29.jpg",
    "maher-al-mueaqly": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Maher_Al_Mueaqly.jpg/440px-Maher_Al_Mueaqly.jpg",
}


def _download(url: str, dest: Path) -> bool:
    try:
        request = Request(url, headers={"User-Agent": "QuranThumbnailGenerator/1.0"})
        with urlopen(request, timeout=30) as response:
            data = response.read()
        if len(data) < 5000:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception as exc:
        print(f"  Failed: {exc}")
        return False


def main() -> None:
    reciters = reciter_store.load_reciters()
    for reciter in reciters:
        if reciter.photos:
            print(f"Skip {reciter.name} (already has photos)")
            continue
        url = PORTRAITS.get(reciter.id)
        if not url:
            print(f"No default photo URL for {reciter.name}")
            continue
        temp = reciter_store.reciter_images_dir() / f"{reciter.id}_default.jpg"
        print(f"Downloading {reciter.name}...")
        if not _download(url, temp):
            continue
        reciter_store.add_reciter_photo(reciter.id, "Portrait", temp)
        print(f"  Added portrait for {reciter.name}")


if __name__ == "__main__":
    main()
