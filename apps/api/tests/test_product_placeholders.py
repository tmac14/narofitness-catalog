"""Product placeholder resolution by presentation layout."""

from app.pdf.layouts.registry import LAYOUT_REGISTRY
from app.services.app_assets import (
    placeholder_filename,
    placeholder_path,
    resolve_placeholder_url,
)


def test_each_layout_has_placeholder_file():
    for layout_id, layout in LAYOUT_REGISTRY.items():
        path = placeholder_path(layout.placeholder_aspect_ratio)
        assert path.is_file(), f"Missing placeholder for {layout_id}: {path}"


def test_layout_placeholder_aspect_ratios():
    assert LAYOUT_REGISTRY["single_standard"].placeholder_aspect_ratio == "4_3"
    assert LAYOUT_REGISTRY["variant_row_wide"].placeholder_aspect_ratio == "16_9"
    assert LAYOUT_REGISTRY["variant_grid_50_50"].placeholder_aspect_ratio == "1_1"
    assert LAYOUT_REGISTRY["family_variant_table"].placeholder_aspect_ratio == "4_3"


def test_resolve_placeholder_url_html():
    url = resolve_placeholder_url(
        "variant_row_wide",
        for_html=True,
        api_base="http://127.0.0.1:8000",
    )
    assert url == (
        f"http://127.0.0.1:8000/api/v1/assets/placeholders/{placeholder_filename('16_9')}"
    )


def test_resolve_placeholder_url_pdf():
    url = resolve_placeholder_url(
        "variant_grid_50_50",
        for_html=False,
        api_base="http://127.0.0.1:8000",
    )
    assert url.startswith("file:")
    assert placeholder_filename("1_1") in url


def test_list_layouts_includes_placeholder_aspect_ratio():
    from app.pdf.layouts import list_layouts

    for item in list_layouts():
        assert "placeholder_aspect_ratio" in item
        assert item["placeholder_aspect_ratio"]
