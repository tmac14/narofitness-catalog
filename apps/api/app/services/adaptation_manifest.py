"""Direct adaptation render manifest builders (Phase 2B stub)."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from app.models.entities import (
    CatalogAdaptationProject,
    CatalogAdaptationRecipeVersion,
    DocumentAnalysisSnapshot,
    SourceDocument,
)

MANIFEST_SCHEMA_VERSION = "direct-adaptation-manifest/v1"
RENDERER_KEY_STUB = "fdl_direct_stub"
RENDERER_VERSION_STUB = "0.0.0"


def manifest_fingerprint(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_stub_preview_manifest(
    *,
    project: CatalogAdaptationProject,
    recipe: CatalogAdaptationRecipeVersion,
    source: SourceDocument,
    snapshot: DocumentAnalysisSnapshot | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "export_kind": "preview",
        "renderer_key": RENDERER_KEY_STUB,
        "renderer_version": RENDERER_VERSION_STUB,
        "status": "stub",
        "project_id": str(project.id),
        "project_name": project.name,
        "source_document_id": str(source.id),
        "source_sha256": source.sha256,
        "recipe_version_id": str(recipe.id),
        "recipe_fingerprint": recipe.recipe_fingerprint,
        "profile_key": project.profile_key,
        "profile_version": project.profile_version,
        "page_count": source.page_count,
        "note": "Phase 2B scaffold — manifest only; PDF renderer deferred to Phase 2C+",
    }
    if snapshot is not None:
        body["analysis_snapshot_id"] = str(snapshot.id)
        body["snapshot_fingerprint"] = snapshot.snapshot_fingerprint
    fingerprint = manifest_fingerprint(body)
    body["manifest_fingerprint"] = fingerprint
    return body
