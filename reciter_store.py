"""Persist and manage reciter background image collections."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4


@dataclass
class ReciterPhoto:
    id: str
    label: str
    image_path: str


@dataclass
class Reciter:
    id: str
    name: str
    photos: list[ReciterPhoto] = field(default_factory=list)


def _app_root() -> Path:
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    path = _app_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reciters_file() -> Path:
    return data_dir() / "reciters.json"


def reciter_images_dir() -> Path:
    path = data_dir() / "reciter_images"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _default_reciters() -> list[Reciter]:
    return [
        Reciter("yasser-al-dosari", "Yasser Al Dosari"),
        Reciter("mishary-rashid", "Mishary Rashid Alafasy"),
        Reciter("abdul-basit", "Abdul Basit Abdul Samad"),
        Reciter("saad-al-ghamdi", "Saad Al Ghamdi"),
        Reciter("muhammad-al-luhaidan", "Muhammad Al Luhaidan"),
        Reciter("maher-al-mueaqly", "Maher Al Mueaqly"),
    ]


def _parse_reciter(raw: dict) -> Reciter:
    if "photos" in raw:
        photos = [ReciterPhoto(**photo) for photo in raw["photos"]]
        return Reciter(id=raw["id"], name=raw["name"], photos=photos)

    photos: list[ReciterPhoto] = []
    legacy_path = raw.get("image_path", "")
    if legacy_path:
        photos.append(
            ReciterPhoto(
                id=uuid4().hex[:10],
                label="Default",
                image_path=legacy_path,
            )
        )
    return Reciter(id=raw["id"], name=raw["name"], photos=photos)


def load_reciters() -> list[Reciter]:
    path = reciters_file()
    if not path.exists():
        reciters = _default_reciters()
        save_reciters(reciters)
        return reciters

    raw = json.loads(path.read_text(encoding="utf-8"))
    reciters = [_parse_reciter(item) for item in raw]
    save_reciters(reciters)
    return reciters


def save_reciters(reciters: list[Reciter]) -> None:
    payload = []
    for reciter in reciters:
        item = {
            "id": reciter.id,
            "name": reciter.name,
            "photos": [asdict(photo) for photo in reciter.photos],
        }
        payload.append(item)
    reciters_file().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def add_reciter(name: str) -> Reciter:
    reciter = Reciter(id=uuid4().hex[:12], name=name.strip())
    reciters = load_reciters()
    reciters.append(reciter)
    save_reciters(reciters)
    return reciter


def update_reciter_name(reciter_id: str, name: str) -> None:
    reciters = load_reciters()
    for reciter in reciters:
        if reciter.id == reciter_id:
            reciter.name = name.strip()
            save_reciters(reciters)
            return
    raise KeyError(f"Reciter not found: {reciter_id}")


def add_reciter_photo(reciter_id: str, label: str, source_image: Path) -> ReciterPhoto:
    ext = source_image.suffix.lower() or ".jpg"
    photo_id = uuid4().hex[:10]
    dest = reciter_images_dir() / f"{reciter_id}_{photo_id}{ext}"
    shutil.copy2(source_image, dest)
    photo = ReciterPhoto(id=photo_id, label=label.strip() or "Photo", image_path=str(dest))

    reciters = load_reciters()
    for reciter in reciters:
        if reciter.id == reciter_id:
            reciter.photos.append(photo)
            save_reciters(reciters)
            return photo
    raise KeyError(f"Reciter not found: {reciter_id}")


def delete_reciter_photo(reciter_id: str, photo_id: str) -> None:
    reciters = load_reciters()
    for reciter in reciters:
        if reciter.id != reciter_id:
            continue
        kept: list[ReciterPhoto] = []
        for photo in reciter.photos:
            if photo.id == photo_id:
                image_path = Path(photo.image_path)
                if image_path.exists():
                    image_path.unlink()
                continue
            kept.append(photo)
        reciter.photos = kept
        save_reciters(reciters)
        return
    raise KeyError(f"Reciter not found: {reciter_id}")


def delete_reciter(reciter_id: str) -> None:
    reciters = load_reciters()
    kept: list[Reciter] = []
    for reciter in reciters:
        if reciter.id == reciter_id:
            for photo in reciter.photos:
                image_path = Path(photo.image_path)
                if image_path.exists():
                    image_path.unlink()
            continue
        kept.append(reciter)
    save_reciters(kept)


def get_reciter(reciter_id: str) -> Reciter | None:
    for reciter in load_reciters():
        if reciter.id == reciter_id:
            return reciter
    return None
