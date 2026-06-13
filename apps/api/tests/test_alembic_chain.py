"""Verify Alembic migration chain integrity."""

from pathlib import Path

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def _load_revisions() -> dict[str, dict]:
    revisions: dict[str, dict] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        namespace: dict = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        rev = namespace.get("revision")
        if not rev:
            continue
        revisions[rev] = {
            "path": path.name,
            "down_revision": namespace.get("down_revision"),
        }
    return revisions


def test_single_migration_head():
    revisions = _load_revisions()
    assert revisions, "No migration revisions found"

    referenced = {info["down_revision"] for info in revisions.values() if info["down_revision"]}
    heads = [rev for rev in revisions if rev not in referenced]
    assert len(heads) == 1, f"Expected one head, found {heads}"
    assert heads[0] == "007_product_image_source"


def test_migration_chain_order():
    revisions = _load_revisions()
    assert "001_pim_schema" in revisions
    assert "002_taxonomy_mapping_notes" in revisions
    assert "003_catalog_show_desc_column" in revisions
    assert "004_catalog_covers" in revisions
    assert "005_background_jobs" in revisions
    assert "006_variant_brand_id" in revisions
    assert "007_product_image_source" in revisions
    assert revisions["001_pim_schema"]["down_revision"] in (None, ())
    assert revisions["002_taxonomy_mapping_notes"]["down_revision"] == "001_pim_schema"
    assert (
        revisions["003_catalog_show_desc_column"]["down_revision"] == "002_taxonomy_mapping_notes"
    )
    assert revisions["004_catalog_covers"]["down_revision"] == "003_catalog_show_desc_column"
    assert revisions["005_background_jobs"]["down_revision"] == "004_catalog_covers"
    assert revisions["006_variant_brand_id"]["down_revision"] == "005_background_jobs"
    assert revisions["007_product_image_source"]["down_revision"] == "006_variant_brand_id"


def test_no_orphan_revisions():
    revisions = _load_revisions()
    down_revisions = {info["down_revision"] for info in revisions.values() if info["down_revision"]}
    for down in down_revisions:
        assert down in revisions, f"Missing parent revision: {down}"
