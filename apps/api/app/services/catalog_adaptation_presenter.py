"""Serialize catalog adaptation aggregates for API responses."""

from __future__ import annotations

from app.models.entities import CatalogAdaptationProject
from app.schemas import CatalogAdaptationProjectOut, CatalogAdaptationRecipeVersionOut


def recipe_to_out(recipe) -> CatalogAdaptationRecipeVersionOut:
    return CatalogAdaptationRecipeVersionOut(
        id=recipe.id,
        project_id=recipe.project_id,
        version_number=recipe.version_number,
        schema_version=recipe.schema_version,
        recipe_fingerprint=recipe.recipe_fingerprint,
        recipe=recipe.recipe_json,
        created_at=recipe.created_at,
    )


def project_to_out(project: CatalogAdaptationProject) -> CatalogAdaptationProjectOut:
    active_recipe = None
    if project.active_recipe_version_id is not None:
        active = next(
            (r for r in project.recipe_versions if r.id == project.active_recipe_version_id),
            None,
        )
        if active is not None:
            active_recipe = recipe_to_out(active)
    return CatalogAdaptationProjectOut(
        id=project.id,
        source_document_id=project.source_document_id,
        analysis_snapshot_id=project.analysis_snapshot_id,
        name=project.name,
        status=project.status,
        profile_key=project.profile_key,
        profile_version=project.profile_version,
        active_recipe_version_id=project.active_recipe_version_id,
        active_recipe=active_recipe,
        created_at=project.created_at,
        updated_at=project.updated_at,
        created_by=project.created_by,
    )
