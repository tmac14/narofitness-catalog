"""Private artifact storage for source documents (outside public media mount)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from app.config import settings


def private_artifact_root() -> Path:
    root = Path(settings.private_artifact_dir)
    if not root.is_absolute():
        root = Path.cwd() / root
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def source_document_storage_key(sha256_hex: str) -> str:
    normalized = sha256_hex.lower()
    return f"source-documents/{normalized[:2]}/{normalized}.pdf"


def absolute_private_path(storage_key: str) -> Path:
    root = private_artifact_root()
    target = (root / storage_key).resolve()
    target.relative_to(root)
    return target


def write_private_bytes_atomic(storage_key: str, content: bytes) -> Path:
    dest = absolute_private_path(storage_key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=dest.parent, suffix=".part")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        tmp_path.write_bytes(content)
        tmp_path.replace(dest)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    return dest


def read_private_bytes(storage_key: str) -> bytes:
    return absolute_private_path(storage_key).read_bytes()


def private_path_not_under_public_media(storage_key: str) -> bool:
    """True when the private file is outside the mounted public data_dir tree."""
    private_file = absolute_private_path(storage_key)
    public_root = Path(settings.data_dir).resolve()
    if not public_root.is_absolute():
        public_root = (Path.cwd() / public_root).resolve()
    try:
        private_file.relative_to(public_root)
        return False
    except ValueError:
        return True
