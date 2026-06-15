"""Tests for bundled FDL cover asset resolution."""

from __future__ import annotations

import hashlib

import pytest

from app.services.direct_adaptation.cover_assets import (
    bundled_cover_assets_available,
    resolve_cover_asset,
)

FDL_COVER_ASSETS = [
    ("wireframes/portadas-fdl/main/5.png", "d0cf29c0bbd478bab8b8a829a3fb7b919032d00a8a2dca89f218c35461efdc6a"),
    ("wireframes/portadas-fdl/categorias/01-cardio.png", "cd62fd671a6c03950c2c37e86e397e70551bccd2a3b5c05e60dc83aeb4e68ec9"),
    ("wireframes/portadas-fdl/categorias/02-crosstraining.png", "b7dbccc37ac40f84795d35ab5448f4282e09e0b84e12dc0dc51fb1f70a877dc4"),
    ("wireframes/portadas-fdl/categorias/03-suelo.png", "e12b867668f4ad3f247fad8aef0c67915ace9ddbfeacd5ea982a8c8a8689986e"),
    ("wireframes/portadas-fdl/categorias/04-discos-y-barras.png", "c0a2917cb4cfe2f376302d5c09aa43be95344e1ea9e35619abd6edc3cf4ba74a"),
    ("wireframes/portadas-fdl/categorias/05-mancuernas.png", "c19bd8218b36a13e56254d5943f277868746a997f9273b1555e90d24422f7d24"),
    ("wireframes/portadas-fdl/categorias/06-material-de-estudio.png", "abf50fd346b0f9dc6750e5712e23a9a496dee4421122e914516bcff2704d6971"),
    ("wireframes/portadas-fdl/categorias/07-boxeo.png", "5647ea9ae6a569d5544598447cf8e1a8d16b6738f3e0bce0b8cdf7f5e5a0c3ba"),
    ("wireframes/portadas-fdl/categorias/08-agarres.png", "983ad2019f5c0d3f9362065f76135ded3536522184781f503e6723bbc1539e08"),
]


@pytest.mark.skipif(not bundled_cover_assets_available(), reason="FDL cover assets not mounted")
def test_bundled_fdl_cover_assets_resolve_with_expected_sha256():
    assert bundled_cover_assets_available()
    for asset_path, expected_sha in FDL_COVER_ASSETS:
        resolved = resolve_cover_asset(asset_path)
        assert resolved is not None, asset_path
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
        assert digest == expected_sha, asset_path
