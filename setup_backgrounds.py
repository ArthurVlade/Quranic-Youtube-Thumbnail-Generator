"""Download categorised nature background images.

Sources used:
  - Pexels CDN (primary, very stable, no key needed for direct photo URLs)
  - Unsplash CDN (secondary, uses known-good photo IDs)

Files are stored as:
  forest_XX.jpg   mountain_XX.jpg   lake_XX.jpg
  spring_XX.jpg   sky_XX.jpg        nature_XX.jpg (existing)
"""

from pathlib import Path
from urllib.request import Request, urlopen
import sys

def _pex(photo_id: int) -> str:
    return (
        f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}"
        f".jpeg?auto=compress&cs=tinysrgb&w=1920&h=1080&dpr=1"
    )

def _uns(photo_id: str) -> str:
    return f"https://images.unsplash.com/photo-{photo_id}?w=1920&h=1080&fit=crop&q=85"

# Each value is a list of URLs tried in order; first successful download wins.
BACKGROUNDS: dict[str, list[str]] = {

    # ── Forests ───────────────────────────────────────────────────────────────
    "forest_01.jpg": [_pex(1179229),  _pex(15286)],
    "forest_02.jpg": [_uns("1441974231531-c6227db76b6e"), _pex(38537)],
    "forest_03.jpg": [_pex(1125850),  _pex(975771)],
    "forest_04.jpg": [_uns("1511497584788-876760111969"), _pex(1340502)],
    "forest_05.jpg": [_pex(1167034),  _uns("1476231682828-37e571bc172f")],
    "forest_06.jpg": [_pex(2097614),  _pex(1005417)],
    "forest_07.jpg": [_uns("1500534314209-a25ddb2bd429"), _pex(33109)],
    "forest_08.jpg": [_uns("1425913397330-cf8af2ff40a1"), _pex(373894)],
    "forest_09.jpg": [_pex(7294682),  _pex(302804)],
    "forest_10.jpg": [_pex(145683),   _pex(167698)],
    "forest_11.jpg": [_pex(3225517),  _pex(688660)],
    "forest_12.jpg": [_pex(1448375),  _pex(235615)],

    # ── Mountains ─────────────────────────────────────────────────────────────
    "mountain_01.jpg": [_uns("1506905925346-21bda4d32df4"), _pex(417173)],
    "mountain_02.jpg": [_uns("1454496522488-7a8e488e8606"), _pex(618833)],
    "mountain_03.jpg": [_uns("1501854140801-50d01698950b"), _pex(261621)],
    "mountain_04.jpg": [_pex(2325446), _pex(1462938)],
    "mountain_05.jpg": [_pex(733745),  _pex(1054218)],
    "mountain_06.jpg": [_uns("1452587925148-ce544e77e70d"), _pex(1366919)],
    "mountain_07.jpg": [_uns("1469474968028-56623f02e42e"), _pex(1025469)],
    "mountain_08.jpg": [_uns("1486870591958-9b9d0d1dda99"), _pex(1576302)],
    "mountain_09.jpg": [_pex(2743287), _pex(3408354)],
    "mountain_10.jpg": [_uns("1505765050516-f72dcac9c60e"), _pex(1586348)],
    "mountain_11.jpg": [_pex(1366919), _pex(1903702)],
    "mountain_12.jpg": [_pex(546593),  _pex(1598073)],

    # ── Lakes ─────────────────────────────────────────────────────────────────
    "lake_01.jpg": [_uns("1439066615861-d1af74d74000"), _pex(376464)],
    "lake_02.jpg": [_pex(417074),   _pex(462747)],
    "lake_03.jpg": [_uns("1504455583697-3a9b04be6397"), _pex(289225)],
    "lake_04.jpg": [_pex(1703314),  _pex(1705154)],
    "lake_05.jpg": [_pex(346885),   _pex(1704120)],
    "lake_06.jpg": [_pex(1535162),  _uns("1470071459604-3b5ec3a7fe05")],
    "lake_07.jpg": [_pex(3225528),  _pex(697186)],
    "lake_08.jpg": [_uns("1455218873509-8097305ee378"), _pex(1122411)],
    "lake_09.jpg": [_pex(1671325),  _pex(1761279)],
    "lake_10.jpg": [_pex(2724664),  _pex(1320684)],
    "lake_11.jpg": [_pex(1591056),  _pex(1535163)],
    "lake_12.jpg": [_pex(1486515),  _pex(1562546)],

    # ── Springs / Waterfalls ──────────────────────────────────────────────────
    "spring_01.jpg": [_pex(1621126), _pex(460621)],
    "spring_02.jpg": [_pex(47547),   _pex(1325753)],
    "spring_03.jpg": [_pex(814499),  _pex(355278)],
    "spring_04.jpg": [_pex(1144687), _pex(2662116)],
    "spring_05.jpg": [_uns("1476231682828-37e571bc172f"), _pex(1535161)],
    "spring_06.jpg": [_pex(3225517), _pex(1680172)],
    "spring_07.jpg": [_pex(908714),  _pex(1368382)],
    "spring_08.jpg": [_pex(1482685), _pex(2559941)],
    "spring_09.jpg": [_uns("1501854140801-50d01698950b"), _pex(1448383)],
    "spring_10.jpg": [_pex(3348532), _pex(1408221)],

    # ── Dramatic Skies / Sunsets ──────────────────────────────────────────────
    "sky_01.jpg": [_uns("1469474968028-56623f02e42e"), _pex(1447092)],
    "sky_02.jpg": [_pex(414110),    _pex(210186)],
    "sky_03.jpg": [_uns("1504455583697-3a9b04be6397"), _pex(1166209)],
    "sky_04.jpg": [_pex(1323550),   _pex(1003581)],
    "sky_05.jpg": [_uns("1505765050516-f72dcac9c60e"), _pex(1486516)],
    "sky_06.jpg": [_uns("1476231682828-37e571bc172f"), _pex(1561020)],
    "sky_07.jpg": [_pex(1287146),   _pex(1624496)],
    "sky_08.jpg": [_uns("1505765050516-f72dcac9c60e"), _pex(1553961)],
    "sky_09.jpg": [_uns("1486870591958-9b9d0d1dda99"), _pex(1809644)],
    "sky_10.jpg": [_uns("1455218873509-8097305ee378"), _pex(2387873)],

    # ── Existing / General (keep if not yet present) ──────────────────────────
    "nature_mountain_lake.jpg":    [_uns("1506905925346-21bda4d32df4")],
    "nature_forest_mist.jpg":      [_uns("1470071459604-3b5ec3a7fe05")],
    "nature_lake_reflection.jpg":  [_uns("1439066615861-d1af74d74000")],
    "nature_calm_forest.jpg":      [_uns("1441974231531-c6227db76b6e")],
    "nature_sunset_valley.jpg":    [_uns("1469474968028-56623f02e42e")],
    "nature_pine_forest.jpg":      [_uns("1511497584788-876760111969")],
    "nature_misty_peaks.jpg":      [_uns("1454496522488-7a8e488e8606")],
    "nature_river_forest.jpg":     [_pex(1179229),  _uns("1448375240886-882787673e5c")],
    "nature_alpine_meadow.jpg":    [_uns("1501854140801-50d01698950b")],
    "nature_waterfall_green.jpg":  [_pex(1621126),  _pex(460621)],
    "nature_lake_mountains.jpg":   [_uns("1505765050516-f72dcac9c60e"), _pex(376464)],
    "nature_serene_lake.jpg":      [_pex(417074),   _uns("1475483495702-6e08d7d12e6a")],
    "nature_cloudy_mountains.jpg": [_uns("1452587925148-ce544e77e70d")],
    "nature_green_hills.jpg":      [_pex(210186),   _pex(414110)],
}

_PORTRAIT_STEMS = {"nature_autumn_forest"}


def _try_download(urls: list[str], dest: Path) -> bool:
    for url in urls:
        try:
            req = Request(url, headers={"User-Agent": "QuranThumbnailGenerator/2.1"})
            with urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) < 30_000:
                continue
            dest.write_bytes(data)
            return True
        except Exception:
            continue
    return False


def main() -> None:
    backgrounds_dir = Path(__file__).resolve().parent / "assets" / "backgrounds"
    backgrounds_dir.mkdir(parents=True, exist_ok=True)

    for stem in _PORTRAIT_STEMS:
        for ext in (".jpg", ".jpeg", ".png"):
            bad = backgrounds_dir / f"{stem}{ext}"
            if bad.exists():
                bad.unlink()
                print(f"Removed portrait image: {bad.name}")

    ok = skip = fail = 0
    total = len(BACKGROUNDS)

    for idx, (name, urls) in enumerate(BACKGROUNDS.items(), 1):
        dest = backgrounds_dir / name
        if dest.exists() and dest.stat().st_size > 50_000:
            print(f"[{idx:>3}/{total}] already present: {name}")
            skip += 1
            continue
        print(f"[{idx:>3}/{total}] downloading {name}...", end=" ", flush=True)
        if _try_download(urls, dest):
            print("OK")
            ok += 1
        else:
            print("FAILED (all fallbacks exhausted)")
            fail += 1

    print(f"\nDone — {ok} downloaded, {skip} already present, {fail} failed.")
    total_present = len(list(backgrounds_dir.glob("*.jpg"))) + len(list(backgrounds_dir.glob("*.jpeg")))
    print(f"Total backgrounds in library: {total_present}")


if __name__ == "__main__":
    main()
