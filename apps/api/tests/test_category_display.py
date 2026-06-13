from types import SimpleNamespace

from app.services.category_display import master_category_labels


def test_master_category_labels_top_level_only():
    category = SimpleNamespace(name="Discos", parent_id=None, parent=None)

    assert master_category_labels(category) == ("Discos", None)


def test_master_category_labels_with_parent_and_sub():
    parent = SimpleNamespace(name="Crosstraining")
    category = SimpleNamespace(name="Discos", parent_id=1, parent=parent)

    assert master_category_labels(category) == ("Crosstraining", "Discos")


def test_master_category_labels_deduplicates_identical_parent_and_sub():
    parent = SimpleNamespace(name="Discos")
    category = SimpleNamespace(name="Discos", parent_id=1, parent=parent)

    assert master_category_labels(category) == ("Discos", None)
