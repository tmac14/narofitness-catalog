"""Read-only listing of images available for cover assignment."""

from __future__ import annotations

from pathlib import Path

from app.services.media import ALLOWED_EXTENSIONS, data_root, media_url

MAX_LIBRARY_ITEMS = 200


def list_media_library_images(*, limit: int = MAX_LIBRARY_ITEMS) -> list[dict[str, str]]:
    root = data_root()
    images_dir = root / "images"
    if not images_dir.is_dir():
        return []

    items: list[dict[str, str]] = []
    for path in sorted(images_dir.rglob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        rel = path.relative_to(root).as_posix()
        items.append(
            {
                "relative_path": rel,
                "url": media_url(rel),
                "filename": path.name,
            }
        )
        if len(items) >= limit:
            break
    return items
