"""Unit tests for PIM spec model constraints."""

from app.models.entities import SpecDefinition, Unit


def test_spec_definition_unique_key():
    assert SpecDefinition.__table__.c.key.unique is True


def test_unit_unique_code():
    assert Unit.__table__.c.code.unique is True


def test_spec_definition_required_fields():
    cols = {c.name for c in SpecDefinition.__table__.columns}
    assert {"key", "label", "data_type", "scope", "role"}.issubset(cols)


def test_master_spec_unique_constraint():
    {c.name for c in SpecDefinition.__table__.constraints}
    # UniqueConstraint on key is represented; master spec uniqueness is on product_master_specs
    from app.models.entities import ProductMasterSpec

    uq = [
        c.name
        for c in ProductMasterSpec.__table__.constraints
        if getattr(c, "name", None) == "uq_master_spec"
    ]
    assert uq, "Expected uq_master_spec constraint on product_master_specs"
