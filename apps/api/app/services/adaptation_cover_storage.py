"""Store user-assigned adaptation cover images under data_dir."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.services.media import ALLOWED_EXTENSIONS, data_root, media_url

MAX_COVER_IMAGE_BYTES = 15 * 1024 * 1024


class AdaptationCoverStorageError(ValueError):
    pass


def adaptation_covers_dir(project_id: uuid.UUID) -> Path:
    directory = data_root() / "images" / "adaptations" / str(project_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def relative_adaptation_cover_path(project_id: uuid.UUID, filename: str) -> str:
    return f"images/adaptations/{project_id}/{filename}"


def save_adaptation_cover_bytes(
    project_id: uuid.UUID,
    *,
    slot_id: str,
    content: bytes,
    suffix: str,
) -> tuple[str, str, str]:
    if suffix.lower() not in ALLOWED_EXTENSIONS:
        raise AdaptationCoverStorageError(
            f"Unsupported image type {suffix or '(none)'}; allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if len(content) > MAX_COVER_IMAGE_BYTES:
        raise AdaptationCoverStorageError("Cover image exceeds 15 MB limit")
    if not content:
        raise AdaptationCoverStorageError("Empty upload")

    safe_slot = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in slot_id)[:48]
    filename = f"{safe_slot}{suffix.lower()}"
    target = adaptation_covers_dir(project_id) / filename
    target.write_bytes(content)
    rel = relative_adaptation_cover_path(project_id, filename)
    digest = hashlib.sha256(content).hexdigest()
    return rel, digest, media_url(rel)


def save_adaptation_cover_upload(
    project_id: uuid.UUID,
    *,
    slot_id: str,
    upload: UploadFile,
) -> tuple[str, str, str]:
    suffix = Path(upload.filename or "").suffix.lower()
    content = upload.file.read()
    return save_adaptation_cover_bytes(project_id, slot_id=slot_id, content=content, suffix=suffix)


def copy_library_image_to_adaptation_cover(
    project_id: uuid.UUID,
    *,
    slot_id: str,
    library_relative_path: str,
) -> tuple[str, str, str]:
    rel = library_relative_path.replace("\\", "/").lstrip("/")
    if rel.startswith("api/v1/media/"):
        rel = rel.removeprefix("api/v1/media/")
    source = data_root() / rel
    if not source.is_file():
        raise AdaptationCoverStorageError("Media library file not found")
    suffix = source.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise AdaptationCoverStorageError("Media library file is not a supported image")

    safe_slot = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in slot_id)[:48]
    filename = f"{safe_slot}{suffix}"
    target = adaptation_covers_dir(project_id) / filename
    shutil.copy2(source, target)
    content = target.read_bytes()
    rel_out = relative_adaptation_cover_path(project_id, filename)
    return rel_out, hashlib.sha256(content).hexdigest(), media_url(rel_out)
