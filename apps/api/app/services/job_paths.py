"""Safe path resolution for job and adaptation artifact files."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.services.adaptation_export_storage import resolve_private_artifact_path


def resolve_result_path_under_data_dir(result_path: str) -> Path | None:
    """Resolve result_path relative to data_dir; return None if outside data_dir."""
    data_dir = Path(settings.data_dir).resolve()
    raw = Path(result_path)
    resolved = raw.resolve() if raw.is_absolute() else (data_dir / raw).resolve()
    try:
        resolved.relative_to(data_dir)
    except ValueError:
        return None
    return resolved


def resolve_job_result_path(result_path: str) -> Path | None:
    private = resolve_private_artifact_path(result_path)
    if private is not None and private.is_file():
        return private
    return resolve_result_path_under_data_dir(result_path)


def relative_export_path(absolute_path: Path) -> str:
    data_dir = Path(settings.data_dir).resolve()
    resolved = absolute_path.resolve()
    try:
        return resolved.relative_to(data_dir).as_posix()
    except ValueError:
        private = Path(settings.private_artifact_dir).resolve()
        try:
            return resolved.relative_to(private).as_posix()
        except ValueError:
            return str(resolved)


def media_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".json":
        return "application/json"
    return "application/octet-stream"
