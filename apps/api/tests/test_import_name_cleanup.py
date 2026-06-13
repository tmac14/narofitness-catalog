"""Tests for product name cleanup during PDF import."""

from app.services.import_name_cleanup import clean_product_name


def test_remove_brand_suffix_with_dash():
    name = clean_product_name(
        "Air Ski Trainer Eco - Xebex",
        brand="XEBEX",
        category_main="CARDIO",
        category_sub="SKI",
    )
    assert name == "Air Ski Trainer Eco"


def test_remove_brand_and_subcategory_prefix():
    name = clean_product_name(
        "Bici Reebok Jet 300 Series",
        brand="REEBOK",
        category_main="CARDIO",
        category_sub="BICIS",
    )
    assert name == "Jet 300 Series"


def test_remove_cinta_de_correr_and_brand():
    name = clean_product_name(
        "Cinta de Correr Reebok Zjet 430 Black + Bluetooth",
        brand="REEBOK",
        category_main="CARDIO",
        category_sub="CINTA",
    )
    assert name == "Zjet 430 Black + Bluetooth"


def test_does_not_strip_bicicleta_when_subcategory_is_bici():
    name = clean_product_name(
        "Bicicleta Air Bike Xebex (NO smart conect)",
        brand="XEBEX",
        category_main="CARDIO",
        category_sub="BICI",
    )
    assert name == "Bicicleta Air Bike (NO smart conect)"


def test_remove_leading_brand_token():
    name = clean_product_name(
        "XEBEX Consola Bluetooth AB-1000 SMART CONECT",
        brand="XEBEX",
        category_main="CARDIO",
        category_sub="BICI",
    )
    assert name == "Consola Bluetooth AB-1000 SMART CONECT"


def test_remove_inline_brand_and_subcategory():
    name = clean_product_name(
        "Cinta Xebex ST-6000",
        brand="XEBEX",
        category_main="CARDIO",
        category_sub="CINTA",
    )
    assert name == "ST-6000"
