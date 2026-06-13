"""Safe path resolution for job result files."""

from __future__ import annotations

from pathlib import Path

from app.config import settings


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


def relative_export_path(absolute_path: Path) -> str:
    data_dir = Path(settings.data_dir).resolve()
    resolved = absolute_path.resolve()
    try:
        return resolved.relative_to(data_dir).as_posix()
    except ValueError:
        return str(resolved)
