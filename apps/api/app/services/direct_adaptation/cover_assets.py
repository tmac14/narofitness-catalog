"""Resolve cover asset paths for direct adaptation rendering."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.services.media import data_root

def _monorepo_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        marker = parent / "wireframes" / "portadas-fdl" / "main" / "5.png"
        if marker.is_file():
            return parent
    return None


def cover_asset_search_roots() -> list[Path]:
    roots: list[Path] = []
    if settings.adaptation_assets_root:
        roots.append(Path(settings.adaptation_assets_root))
    roots.append(Path(settings.data_dir) / "adaptation_assets")
    roots.append(data_root())
    monorepo = _monorepo_root()
    if monorepo is not None:
        roots.append(monorepo)
    return roots


def bundled_cover_assets_available() -> bool:
    return resolve_cover_asset("wireframes/portadas-fdl/main/5.png") is not None


def resolve_cover_asset(asset_path: str, *, extra_roots: list[Path] | None = None) -> Path | None:
    if not asset_path:
        return None
    rel = Path(asset_path)
    if rel.is_absolute() and rel.is_file():
        return rel
    roots = list(extra_roots or []) + cover_asset_search_roots()
    for root in roots:
        candidate = root / rel
        if candidate.is_file():
            return candidate
        candidate = root / asset_path
        if candidate.is_file():
            return candidate
    return None
