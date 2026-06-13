from app.services.category_display import master_category_labels
from tests.model_test_factories import make_category


def test_master_category_labels_top_level_only():
    category = make_category("Discos")

    assert master_category_labels(category) == ("Discos", None)


def test_master_category_labels_with_parent_and_sub():
    parent = make_category("Crosstraining")
    category = make_category("Discos", parent_id=parent.id, parent=parent)

    assert master_category_labels(category) == ("Crosstraining", "Discos")


def test_master_category_labels_deduplicates_identical_parent_and_sub():
    parent = make_category("Discos")
    category = make_category("Discos", parent_id=parent.id, parent=parent)

    assert master_category_labels(category) == ("Discos", None)
