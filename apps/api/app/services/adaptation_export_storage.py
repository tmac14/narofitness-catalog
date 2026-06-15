"""Persist adaptation export artifacts under private_artifact_dir."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from app.config import settings


def private_adaptation_exports_root() -> Path:
    root = Path(settings.private_artifact_dir) / "adaptation_exports"
    root.mkdir(parents=True, exist_ok=True)
    return root


def ephemeral_adaptation_exports_root() -> Path:
    root = Path(settings.private_artifact_dir) / "adaptation_exports_ephemeral"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _persist_project_dir(project_id: UUID) -> Path:
    project_dir = private_adaptation_exports_root() / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def _ephemeral_job_dir(job_id: UUID) -> Path:
    job_dir = ephemeral_adaptation_exports_root() / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def _relative_private(path: Path) -> str:
    base = Path(settings.private_artifact_dir).resolve()
    return path.resolve().relative_to(base).as_posix()


def write_manifest_atomic(
    *,
    project_id: UUID,
    export_id: UUID,
    manifest: dict,
    delivery_mode: str = "persist",
    job_id: UUID | None = None,
) -> str:
    if delivery_mode == "ephemeral":
        if job_id is None:
            raise ValueError("ephemeral manifest write requires job_id")
        target_dir = _ephemeral_job_dir(job_id)
    else:
        target_dir = _persist_project_dir(project_id)
    filename = f"{export_id}.manifest.json"
    target = target_dir / filename
    tmp = target_dir / f".{export_id}.manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(target)
    return _relative_private(target)


def write_pdf_atomic(
    *,
    project_id: UUID,
    export_id: UUID,
    pdf_bytes: bytes,
    delivery_mode: str = "persist",
    job_id: UUID | None = None,
    export_kind: str = "preview",
) -> str:
    if delivery_mode == "ephemeral":
        if job_id is None:
            raise ValueError("ephemeral pdf write requires job_id")
        target_dir = _ephemeral_job_dir(job_id)
    else:
        target_dir = _persist_project_dir(project_id)
    suffix = "final" if export_kind == "final" else "preview"
    filename = f"{export_id}.{suffix}.pdf"
    target = target_dir / filename
    tmp = target_dir / f".{export_id}.{suffix}.pdf.tmp"
    tmp.write_bytes(pdf_bytes)
    tmp.replace(target)
    return _relative_private(target)


def resolve_private_artifact_path(relative_path: str) -> Path | None:
    base = Path(settings.private_artifact_dir).resolve()
    raw = Path(relative_path)
    resolved = raw.resolve() if raw.is_absolute() else (base / raw).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        return None
    return resolved


def compute_expires_at(*, ttl_seconds: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)


def delete_artifact_files(*, artifact_path: str | None, pdf_artifact_path: str | None) -> None:
    for rel in (artifact_path, pdf_artifact_path):
        if not rel:
            continue
        path = resolve_private_artifact_path(rel)
        if path is not None and path.is_file():
            path.unlink(missing_ok=True)
