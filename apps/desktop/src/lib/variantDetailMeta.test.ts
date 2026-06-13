import { describe, expect, it } from "vitest";
import type { ProductVariant, SpecValue } from "./api";
import {
  formatVariantField,
  topVariantSpecs,
  variantDisplayTitle,
  variantSpecsWithValue,
} from "./variantDetailMeta";

function spec(key: string, value: string | null): SpecValue {
  return {
    spec_definition_id: key,
    key,
    label: key,
    data_type: "text",
    value,
  };
}

function makeVariant(overrides: Partial<ProductVariant> = {}): ProductVariant {
  return {
    id: "v1",
    product_master_id: "m1",
    supplier_id: "s1",
    supplier_code: "FDL",
    sku: "CRO095",
    ean: null,
    display_name: "5 kg Naranja",
    latest_price: "10,00 €",
    specs: [],
    source_page: null,
    source_pages: [],
    ...overrides,
  };
}

describe("variantDetailMeta", () => {
  it("uses display_name for variant title when present", () => {
    expect(variantDisplayTitle(makeVariant())).toBe("5 kg Naranja");
    expect(variantDisplayTitle(makeVariant({ display_name: null }))).toBe("CRO095");
  });

  it("formats empty EAN as dash", () => {
    expect(formatVariantField(null)).toBe("—");
    expect(formatVariantField("  ")).toBe("—");
    expect(formatVariantField("8412345678901")).toBe("8412345678901");
  });

  it("returns specs with values only", () => {
    const specs = variantSpecsWithValue([
      spec("peso_kg", "5 kg"),
      spec("color", null),
      spec("color", "  "),
    ]);
    expect(specs).toHaveLength(1);
    expect(specs[0].key).toBe("peso_kg");
  });

  it("limits top variant specs", () => {
    const variant = makeVariant({
      specs: [
        spec("peso_kg", "5 kg"),
        spec("color", "Naranja"),
        spec("capacidad_balones", "12"),
        spec("material", "PVC"),
      ],
    });
    const top = topVariantSpecs(variant, 3);
    expect(top).toHaveLength(3);
    expect(top.map((s) => s.key)).toEqual(["peso_kg", "color", "capacidad_balones"]);
  });
});
