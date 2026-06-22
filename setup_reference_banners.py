"""Copy reference Islamic corner banner PNGs into assets/banners."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "assets" / "banners"
DEST.mkdir(parents=True, exist_ok=True)

SOURCES = [
    (
        Path(
            r"C:\Users\Avalon Absolute\.cursor\projects\c-Users-Avalon-Absolute-Projects-quran-thumbnail-generator"
            r"\assets\c__Users_Avalon_Absolute_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_"
            r"image-9c640903-d922-41af-b6cf-ba608e40d36c.png"
        ),
        "corner_gold_geometric.png",
    ),
    (
        Path(
            r"C:\Users\Avalon Absolute\.cursor\projects\c-Users-Avalon-Absolute-Projects-quran-thumbnail-generator"
            r"\assets\c__Users_Avalon_Absolute_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_"
            r"image-22575362-2bc3-4b23-a2cd-f1008bc9db8a.png"
        ),
        "corner_arabesque_teal.png",
    ),
]


def main() -> None:
    for source, name in SOURCES:
        dest = DEST / name
        if source.exists():
            shutil.copy2(source, dest)
            print(f"Copied {name}")
        elif dest.exists():
            print(f"Already present: {name}")
        else:
            print(f"Missing source for {name}: {source}")


if __name__ == "__main__":
    main()
