"""Remove broken/low-quality scenery: red placeholders, flat images, portrait
crops, sub-HD images, and exact duplicates."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

import thumbnail_generator as tg
from image_quality import evaluate

EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def main(dry_run: bool = False) -> None:
    d = tg._backgrounds_dir()
    imgs = sorted(p for p in d.glob("*") if p.suffix.lower() in EXTS)

    removed: list[tuple[str, str]] = []
    seen_hashes: dict[str, str] = {}

    for p in imgs:
        try:
            data = p.read_bytes()
            digest = hashlib.md5(data).hexdigest()
            if digest in seen_hashes:
                removed.append((p.name, f"duplicate of {seen_hashes[digest]}"))
                if not dry_run:
                    p.unlink()
                continue
            ok, reason = evaluate(Image.open(p))
            if not ok:
                removed.append((p.name, reason))
                if not dry_run:
                    p.unlink()
                continue
            seen_hashes[digest] = p.name
        except Exception as e:
            removed.append((p.name, f"error: {e}"))
            if not dry_run:
                try:
                    p.unlink()
                except OSError:
                    pass

    print(f"Scanned {len(imgs)} files. Removed {len(removed)}:")
    for name, reason in removed:
        print(f"  - {name}: {reason}")
    remaining = len([p for p in d.glob('*') if p.suffix.lower() in EXTS])
    print(f"Remaining: {remaining}")


if __name__ == "__main__":
    import sys
    main(dry_run="--dry" in sys.argv)
