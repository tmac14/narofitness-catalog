import { describe, expect, it } from "vitest";
import type {
  ProductMaster,
  ProductMasterDetail,
  ProductMasterListVariant,
  ProductVariant,
  SpecValue,
} from "./api";
import {
  collectVariantSpecColumns,
  formatSpecLabel,
  getListVariantAttributeValue,
  hasAnyDisplayedSpecs,
  listVariantsInApiOrder,
  masterSpecsForDisplay,
  resolveListVariantColumns,
  variantSpecValue,
} from "./productSpecs";

function spec(key: string, label: string, value: string | null, sortOrder = 0): SpecValue {
  return {
    spec_definition_id: key,
    key,
    label,
    data_type: "text",
    value,
    sort_order: sortOrder,
  };
}

function listVariant(
  sku: string,
  attributes: Record<string, string | null>,
  displayName?: string,
): ProductMasterListVariant {
  return {
    id: sku,
    sku,
    display_name: displayName ?? sku,
    reference_label: null,
    price: "10,00 €",
    image_url: null,
    brand: null,
    brand_display: null,
    variant_label: null,
    attributes,
    source_page: null,
    source_pages: [],
  };
}

function wallBallsMaster(): ProductMaster {
  return {
    id: "master-wall-balls",
    name: "Wall Balls Libras",
    brand: "FDL",
    category_id: "cat-1",
    master_key: null,
    notes: null,
    variant_count: 3,
    references: ["CRO083", "CRO084", "CRO085"],
    price: null,
    variant_columns: [{ key: "peso", label: "PESO" }],
    source_page: null,
    source_pages: [],
    variants: [
      listVariant("CRO083", { peso: "12 lb" }),
      listVariant("CRO084", { peso: "14 lb" }),
      listVariant("CRO085", { peso: "16 lb" }),
    ],
  };
}

function powerBagsMaster(): ProductMaster {
  return {
    id: "master-power-bags",
    name: "Power Bags Color",
    brand: "FDL",
    category_id: "cat-2",
    master_key: null,
    notes: null,
    variant_count: 3,
    references: ["CRO095", "CRO100", "CRO143"],
    price: null,
    variant_columns: [
      { key: "peso", label: "PESO" },
      { key: "color", label: "COLOR" },
    ],
    source_page: null,
    source_pages: [],
    variants: [
      listVariant("CRO095", { peso: "5 kg", color: "Naranja" }),
      listVariant("CRO100", { peso: "10 kg", color: "Rojo" }),
      listVariant("CRO143", { peso: "30 kg", color: null }),
    ],
  };
}

function sop063Detail(): ProductMasterDetail {
  return {
    id: "master-sop063",
    name: "SOP063",
    brand: "FDL",
    category_id: "cat-3",
    master_key: null,
    notes: null,
    variant_count: 1,
    references: ["SOP063"],
    price: "25,00 €",
    variant_columns: [],
    source_page: null,
    source_pages: [],
    variants: [
      {
        id: "var-sop063",
        product_master_id: "master-sop063",
        supplier_id: "sup-1",
        supplier_code: "FDL",
        sku: "SOP063",
        ean: null,
        display_name: "SOP063",
        latest_price: "25,00 €",
        specs: [spec("capacidad_balones", "Capacidad (balones)", "12", 10)],
        source_page: null,
        source_pages: [],
      },
    ],
    images: [],
    specs: [],
  };
}

describe("product list variant columns", () => {
  it("uses API labels PESO and COLOR", () => {
    const master = powerBagsMaster();
    const columns = resolveListVariantColumns(master);
    expect(columns.map((column) => column.label)).toEqual(["PESO", "COLOR"]);
  });

  it("renders Power Bags with PESO and COLOR values", () => {
    const master = powerBagsMaster();
    const columns = resolveListVariantColumns(master);
    const variant = master.variants[0];

    expect(getListVariantAttributeValue(variant, columns[0].key)).toBe("5 kg");
    expect(getListVariantAttributeValue(variant, columns[1].key)).toBe("Naranja");
    expect(getListVariantAttributeValue(master.variants[2], "color")).toBe("—");
  });

  it("does not use Variante when API sends real spec columns", () => {
    const master = wallBallsMaster();
    const columns = resolveListVariantColumns(master);
    expect(columns.some((column) => column.label === "Variante")).toBe(false);
    expect(columns[0].label).toBe("PESO");
    expect(getListVariantAttributeValue(master.variants[0], "peso")).toBe("12 lb");
  });

  it("respects API column order", () => {
    const master: ProductMaster = {
      ...powerBagsMaster(),
      variant_columns: [
        { key: "color", label: "COLOR" },
        { key: "peso", label: "PESO" },
      ],
    };
    expect(resolveListVariantColumns(master).map((column) => column.key)).toEqual([
      "color",
      "peso",
    ]);
  });

  it("preserves API variant order", () => {
    const master = wallBallsMaster();
    const ordered = listVariantsInApiOrder(master.variants);
    expect(ordered.map((variant) => variant.sku)).toEqual(["CRO083", "CRO084", "CRO085"]);
  });

  it("does not add COLOR column when API omits it for uniform color families", () => {
    const master: ProductMaster = {
      ...powerBagsMaster(),
      variant_columns: [{ key: "peso", label: "PESO" }],
      variants: powerBagsMaster().variants.map((variant) => ({
        ...variant,
        attributes: { peso: variant.attributes.peso ?? null },
      })),
    };
    expect(resolveListVariantColumns(master).map((column) => column.label)).toEqual(["PESO"]);
  });
});

describe("product detail characteristics", () => {
  it("shows master specs when present", () => {
    const master: ProductMasterDetail = {
      ...sop063Detail(),
      specs: [spec("material", "Material", "PVC")],
    };
    expect(masterSpecsForDisplay(master.specs).map((item) => item.label)).toEqual(["Material"]);
    expect(hasAnyDisplayedSpecs(master)).toBe(true);
  });

  it("shows variant specs for SOP063 with capacidad_balones label", () => {
    const master = sop063Detail();
    const columns = collectVariantSpecColumns(master.variants);
    expect(columns[0].label).toBe("Capacidad (balones)");
    expect(variantSpecValue(master.variants[0], "capacidad_balones")).toBe("12");
    expect(hasAnyDisplayedSpecs(master)).toBe(true);
  });

  it("builds multi-variant spec table columns for Power Bags detail", () => {
    const variants: ProductVariant[] = powerBagsMaster().variants.map((variant, index) => ({
      id: `var-${index}`,
      product_master_id: "master-power-bags",
      supplier_id: "sup-1",
      supplier_code: "FDL",
      sku: variant.sku,
      ean: null,
      display_name: variant.display_name,
      latest_price: variant.price,
      source_page: variant.source_page,
      source_pages: variant.source_pages,
      specs: [
        spec("peso_kg", "Peso", variant.attributes.peso ?? null, 10),
        spec("color", "Color", variant.attributes.color, 20),
      ],
    }));

    const columns = collectVariantSpecColumns(variants);
    expect(columns.map((column) => column.label)).toEqual(["Peso", "Color"]);
    expect(variantSpecValue(variants[2], "color")).toBe("—");
  });

  it("uses API label for peso_kg and peso_lb keys when label is provided", () => {
    expect(formatSpecLabel(spec("peso_lb", "Peso", "12 lb"))).toBe("Peso");
    expect(formatSpecLabel(spec("peso_kg", "", "5 kg"))).toBe("Peso");
  });

  it("shows empty state only when master and variant specs are empty", () => {
    const empty: ProductMasterDetail = {
      ...sop063Detail(),
      specs: [],
      variants: [{ ...sop063Detail().variants[0], specs: [] }],
    };
    expect(hasAnyDisplayedSpecs(empty)).toBe(false);

    const withVariantSpecs = sop063Detail();
    expect(hasAnyDisplayedSpecs(withVariantSpecs)).toBe(true);
  });
});
