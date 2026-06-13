import { describe, expect, it } from "vitest";
import type { ProductMasterDetail, ProductVariant } from "@/lib/api";
import {
  getSingleVariant,
  isSingleVariantProduct,
  shouldShowVariantsTab,
} from "@/lib/productDetailLayout";

function makeVariant(id: string, sku: string): ProductVariant {
  return {
    id,
    product_master_id: "master-1",
    supplier_id: "supplier-1",
    supplier_code: "FDL",
    sku,
    ean: "8436123456789",
    display_name: null,
    specs: [],
    latest_price: "10,00 €",
    source_page: 4,
    source_pages: [4],
  };
}

function makeMaster(variants: ProductVariant[]): ProductMasterDetail {
  return {
    id: "master-1",
    name: "Test product",
    brand: "FDL",
    category_id: null,
    master_key: null,
    notes: null,
    variant_count: variants.length,
    references: variants.map((variant) => variant.sku),
    price: null,
    variant_columns: [],
    source_page: null,
    source_pages: [],
    images: [],
    specs: [],
    variants,
  };
}

describe("productDetailLayout", () => {
  it("detects single-variant products", () => {
    expect(isSingleVariantProduct(makeMaster([makeVariant("v1", "SKU-1")]))).toBe(true);
    expect(
      isSingleVariantProduct(makeMaster([makeVariant("v1", "SKU-1"), makeVariant("v2", "SKU-2")])),
    ).toBe(false);
  });

  it("shows variants tab only for multi-variant products", () => {
    expect(shouldShowVariantsTab(1)).toBe(false);
    expect(shouldShowVariantsTab(2)).toBe(true);
  });

  it("returns the sole variant for single-variant products", () => {
    const variant = makeVariant("v1", "SKU-1");
    expect(getSingleVariant(makeMaster([variant]))).toEqual(variant);
    expect(getSingleVariant(makeMaster([]))).toBeNull();
  });
});
