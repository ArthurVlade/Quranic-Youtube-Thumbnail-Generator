"""Download a large, categorised library of calm nature backgrounds (500+).

Goal: enough unique scenery that two users rarely pick the same image.

Sources (no API key required):
  1. LoremFlickr  - keyword-accurate Flickr photos, deterministic via ?lock=
  2. Picsum.photos - always-on curated landscape fallback via /seed/

Files are named  <category>_<NNN>.jpg  so the app can group them into tabs:
  forest_*, mountain_*, lake_*, spring_*  (springs/waterfalls/rivers),
  sky_*, valley_*, meadow_*, desert_*, beach_*, autumn_*, winter_*  (Other).

Re-running resumes: existing, valid files are skipped. Failed downloads are
skipped silently so a flaky connection never blocks the whole run.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.request import Request, urlopen

from image_quality import is_good_bytes

# category prefix -> list of search keywords used to vary the imagery
CATEGORIES: dict[str, list[str]] = {
    "forest":   ["forest", "pine forest", "forest path", "misty forest", "woodland", "jungle"],
    "mountain": ["mountain", "mountain range", "snowy mountain", "alps", "mountain peak", "highlands"],
    "lake":     ["lake", "lake reflection", "alpine lake", "calm lake", "mountain lake", "still water"],
    "spring":   ["waterfall", "river", "stream", "creek", "spring nature", "rapids"],
    "sky":      ["sunset", "sunrise", "starry sky", "clouds", "aurora", "dramatic sky"],
    "valley":   ["valley", "green valley", "canyon", "gorge"],
    "meadow":   ["meadow", "wildflowers", "green field", "grassland"],
    "desert":   ["desert", "sand dunes", "desert landscape"],
    "beach":    ["beach", "coast", "ocean cliff", "seascape"],
    "autumn":   ["autumn forest", "autumn nature", "fall foliage"],
    "winter":   ["winter forest", "snow landscape", "frozen lake"],
}

PER_CATEGORY = 48          # 11 categories x 48 = 528 target images
TIMEOUT = 40

# 4K target — Picsum honours the requested size exactly; LoremFlickr does not,
# so Picsum is the primary (reliable, 4K, never a red placeholder) source.
RES = (3840, 2160)


def _loremflickr(keyword: str, seed: int) -> str:
    kw = keyword.replace(" ", ",")
    return f"https://loremflickr.com/{RES[0]}/{RES[1]}/{kw}?lock={seed}"


def _picsum(seed: int) -> str:
    return f"https://picsum.photos/seed/scenery{seed}/{RES[0]}/{RES[1]}"


def _download(urls: list[str], dest: Path) -> bool:
    """Try each URL; keep only the first that passes the quality check."""
    for url in urls:
        try:
            req = Request(url, headers={"User-Agent": "QuranThumbnailGenerator/3.0"})
            with urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if not is_good_bytes(data):
                continue
            dest.write_bytes(data)
            return True
        except Exception:
            continue
    return False


def _build_plan() -> list[tuple[str, list[str]]]:
    plan: list[tuple[str, list[str]]] = []
    for prefix, keywords in CATEGORIES.items():
        for i in range(PER_CATEGORY):
            seed = hash((prefix, i)) % 100_000
            keyword = keywords[i % len(keywords)]
            name = f"{prefix}_{i + 1:03d}.jpg"
            # Picsum first (guaranteed clean 4K), then a couple of validated
            # keyword attempts for nature flavour.
            urls = [
                _picsum(seed),
                _loremflickr(keyword, seed),
                _loremflickr(keyword, seed + 7777),
            ]
            plan.append((name, urls))
    return plan


def main(limit: int | None = None) -> None:
    backgrounds_dir = Path(__file__).resolve().parent / "assets" / "backgrounds"
    backgrounds_dir.mkdir(parents=True, exist_ok=True)

    plan = _build_plan()
    if limit:
        plan = plan[:limit]

    total = len(plan)
    ok = skip = fail = 0
    print(f"Target library: {total} nature backgrounds across {len(CATEGORIES)} categories.\n")

    for idx, (name, urls) in enumerate(plan, 1):
        dest = backgrounds_dir / name
        if dest.exists() and dest.stat().st_size > 15_000:
            skip += 1
            continue
        print(f"[{idx:>4}/{total}] {name} ...", end=" ", flush=True)
        if _download(urls, dest):
            print("OK")
            ok += 1
        else:
            print("skip")
            fail += 1

    present = len([p for p in backgrounds_dir.glob("*.jpg") if p.stat().st_size > 15_000])
    print(f"\nDone - {ok} new, {skip} already present, {fail} failed.")
    print(f"Total backgrounds available: {present}")


if __name__ == "__main__":
    # optional CLI limit: python setup_backgrounds.py 50
    arg = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    main(arg)
