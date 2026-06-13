import { describe, expect, it } from "vitest";
import type { ProductMaster, ProductMasterDetail } from "./api";
import {
  BRAND_COLUMN_KEY,
  MIXED_BRAND_DISPLAY,
  VARIANT_LABEL_COLUMN_KEY,
  characteristicsVariantColumns,
  getDetailVariantCellValue,
  getListVariantAttributeValue,
  isMixedBrandMaster,
  layoutListVariantColumns,
  masterBrandDisplay,
  masterBrandTitle,
  orderVariantColumnsForDisplay,
  presentationDynamicKeysAfterReference,
  resolveDetailVariantColumns,
} from "./variantRepresentation";
import { resolveListVariantColumns } from "./productSpecs";

function listVariant(sku: string, overrides: Partial<ProductMaster["variants"][number]> = {}) {
  return {
    id: sku,
    sku,
    display_name: sku,
    reference_label: null,
    price: "10,00 €",
    image_url: null,
    brand: null,
    brand_display: null,
    variant_label: null,
    attributes: {},
    source_page: null,
    source_pages: [],
    ...overrides,
  };
}

function sacoGusanoMaster(): ProductMaster {
  return {
    id: "master-worm-bag",
    name: "CRO-SACO-GUSANO",
    brand: null,
    brand_mode: "mixed",
    brand_display: MIXED_BRAND_DISPLAY,
    show_brand_column: true,
    show_variant_name_column: true,
    category_id: "cat-1",
    master_key: null,
    notes: null,
    variant_count: 2,
    references: ["CRO107", "CRO107NEXO"],
    price: null,
    source_page: null,
    source_pages: [],
    variant_columns: [
      { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
      { key: BRAND_COLUMN_KEY, label: "Marca" },
    ],
    variants: [
      listVariant("CRO107", {
        variant_label: "2 personas - 160x30cms (60kgs)",
        attributes: {
          variant_label: "2 personas - 160x30cms (60kgs)",
          brand: "Sin marca",
        },
        brand_display: "Sin marca",
      }),
      listVariant("CRO107NEXO", {
        variant_label: "2 personas - 160x30cms (60kgs) - LOGO NEXO",
        attributes: {
          variant_label: "2 personas - 160x30cms (60kgs) - LOGO NEXO",
          brand: "NEXO",
        },
        brand_display: "NEXO",
      }),
    ],
  };
}

function crossfitBarsMaster(): ProductMaster {
  return {
    id: "master-bars",
    name: "Barras Crossfit",
    brand: null,
    brand_mode: "none",
    brand_display: "Sin marca",
    show_brand_column: false,
    show_variant_name_column: true,
    category_id: "cat-2",
    master_key: null,
    notes: null,
    variant_count: 2,
    references: ["BOC001", "BOC004"],
    price: null,
    source_page: null,
    source_pages: [],
    variant_columns: [
      { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
      { key: "peso", label: "PESO" },
      { key: "color", label: "COLOR" },
    ],
    variants: [
      listVariant("BOC001", {
        variant_label: "Barra 2,20 Mts - Agarre 28 mm PLATA",
        attributes: {
          variant_label: "Barra 2,20 Mts - Agarre 28 mm PLATA",
          peso: "20 kg",
          color: "Plata",
        },
      }),
      listVariant("BOC004", {
        variant_label: "Barra 2,20 Mts - Agarre 28 mm NEGRA",
        attributes: {
          variant_label: "Barra 2,20 Mts - Agarre 28 mm NEGRA",
          peso: "20 kg",
          color: "Negro",
        },
      }),
    ],
  };
}

function dobhtMaster(): ProductMaster {
  return {
    id: "master-dobht",
    name: "Disco Olimpico Bumper Hi-Temp (Casquillo de Acero)",
    brand: null,
    brand_mode: "none",
    brand_display: "Sin marca",
    show_brand_column: false,
    show_variant_name_column: false,
    category_id: "cat-3",
    master_key: "DOBHT",
    notes: null,
    variant_count: 2,
    references: ["DOBHT005", "DOBHT010"],
    price: null,
    source_page: null,
    source_pages: [],
    variant_columns: [{ key: "peso", label: "PESO" }],
    variants: [
      listVariant("DOBHT005", {
        variant_label: null,
        attributes: { peso: "5 kg" },
      }),
      listVariant("DOBHT010", {
        variant_label: null,
        attributes: { peso: "10 kg" },
      }),
    ],
  };
}

describe("orderVariantColumnsForDisplay", () => {
  it("partitions DOBHT post-backend with only peso", () => {
    const layout = orderVariantColumnsForDisplay([{ key: "peso", label: "PESO" }]);
    expect(layout.leadingColumns).toEqual([]);
    expect(layout.identityColumns).toEqual([]);
    expect(layout.specColumns.map((column) => column.key)).toEqual(["peso"]);
    expect(presentationDynamicKeysAfterReference(layout)).toEqual(["peso"]);
  });

  it("keeps Referencia-first layout when variant_label is absent", () => {
    const layout = orderVariantColumnsForDisplay([
      { key: "peso", label: "PESO" },
      { key: "color", label: "COLOR" },
    ]);
    expect(layout.leadingColumns).toEqual([]);
    expect(layout.identityColumns).toEqual([]);
    expect(layout.specColumns.map((column) => column.key)).toEqual(["peso", "color"]);
  });

  it("places Saco Gusano brand in identityColumns after Referencia in presentation", () => {
    const layout = orderVariantColumnsForDisplay([
      { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
      { key: BRAND_COLUMN_KEY, label: "Marca" },
    ]);
    expect(layout.leadingColumns.map((column) => column.key)).toEqual([VARIANT_LABEL_COLUMN_KEY]);
    expect(layout.identityColumns.map((column) => column.key)).toEqual([BRAND_COLUMN_KEY]);
    expect(layout.specColumns).toEqual([]);
    expect(presentationDynamicKeysAfterReference(layout)).toEqual([BRAND_COLUMN_KEY]);
  });

  it("places brand before specs in presentation order after Referencia", () => {
    const layout = orderVariantColumnsForDisplay([
      { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
      { key: "peso", label: "PESO" },
      { key: BRAND_COLUMN_KEY, label: "Marca" },
    ]);
    expect(layout.leadingColumns.map((column) => column.key)).toEqual([VARIANT_LABEL_COLUMN_KEY]);
    expect(layout.identityColumns.map((column) => column.key)).toEqual([BRAND_COLUMN_KEY]);
    expect(layout.specColumns.map((column) => column.key)).toEqual(["peso"]);
    expect(presentationDynamicKeysAfterReference(layout)).toEqual(["brand", "peso"]);
  });

  it("does not place brand last when specs exist", () => {
    const layout = orderVariantColumnsForDisplay([
      { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
      { key: "peso", label: "PESO" },
      { key: "color", label: "COLOR" },
      { key: BRAND_COLUMN_KEY, label: "Marca" },
    ]);
    const dynamicKeys = presentationDynamicKeysAfterReference(layout);
    expect(dynamicKeys.indexOf(BRAND_COLUMN_KEY)).toBeLessThan(dynamicKeys.indexOf("peso"));
    expect(dynamicKeys.indexOf(BRAND_COLUMN_KEY)).toBeLessThan(dynamicKeys.indexOf("color"));
    expect(dynamicKeys).toEqual(["brand", "peso", "color"]);
  });

  it("preserves spec column order from API", () => {
    const layout = orderVariantColumnsForDisplay([
      { key: "color", label: "COLOR" },
      { key: "peso", label: "PESO" },
    ]);
    expect(layout.specColumns.map((column) => column.key)).toEqual(["color", "peso"]);
  });

  it("layoutListVariantColumns puts variant_label in leading for Barras Crossfit", () => {
    const layout = layoutListVariantColumns(crossfitBarsMaster());
    expect(layout.leadingColumns.map((column) => column.key)).toEqual([VARIANT_LABEL_COLUMN_KEY]);
    expect(layout.identityColumns).toEqual([]);
    expect(layout.specColumns.map((column) => column.key)).toEqual(["peso", "color"]);
  });

  it("layoutListVariantColumns has no leading column for DOBHT", () => {
    const layout = layoutListVariantColumns(dobhtMaster());
    expect(layout.leadingColumns).toEqual([]);
    expect(layout.identityColumns).toEqual([]);
    expect(layout.specColumns.map((column) => column.key)).toEqual(["peso"]);
  });

  it("Saco Gusano with peso keeps presentation order brand before peso", () => {
    const layout = orderVariantColumnsForDisplay([
      { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
      { key: "peso", label: "PESO" },
      { key: BRAND_COLUMN_KEY, label: "Marca" },
    ]);
    expect(presentationDynamicKeysAfterReference(layout)).toEqual(["brand", "peso"]);
  });
});

describe("master brand display", () => {
  it("uses brand_display for mixed master", () => {
    const master = sacoGusanoMaster();
    expect(masterBrandDisplay(master)).toBe(MIXED_BRAND_DISPLAY);
    expect(isMixedBrandMaster(master)).toBe(true);
    expect(masterBrandTitle(master)).toBe("Marcas distintas por variante");
  });

  it("shows uniform NEXO brand from brand_display", () => {
    const master: ProductMaster = {
      ...crossfitBarsMaster(),
      name: "Barras Crossfit - NEXO",
      brand_mode: "uniform",
      brand_display: "NEXO",
      brand: "NEXO",
    };
    expect(masterBrandDisplay(master)).toBe("NEXO");
    expect(isMixedBrandMaster(master)).toBe(false);
  });
});

describe("list variant columns from API", () => {
  it("shows MARCA column when API sends brand in variant_columns", () => {
    const master = sacoGusanoMaster();
    const columns = resolveListVariantColumns(master);
    expect(columns.some((column) => column.key === BRAND_COLUMN_KEY)).toBe(true);
    expect(getListVariantAttributeValue(master.variants[0], BRAND_COLUMN_KEY)).toBe("Sin marca");
    expect(getListVariantAttributeValue(master.variants[1], BRAND_COLUMN_KEY)).toBe("NEXO");
  });

  it("shows Variante column when API sends variant_label in variant_columns", () => {
    const master = crossfitBarsMaster();
    const columns = resolveListVariantColumns(master);
    expect(columns.some((column) => column.key === VARIANT_LABEL_COLUMN_KEY)).toBe(true);
    expect(getListVariantAttributeValue(master.variants[0], VARIANT_LABEL_COLUMN_KEY)).toBe(
      "Barra 2,20 Mts - Agarre 28 mm PLATA",
    );
  });

  it("reads attribute values from attributes map", () => {
    const master = dobhtMaster();
    expect(resolveListVariantColumns(master).map((column) => column.key)).toEqual(["peso"]);
    expect(getListVariantAttributeValue(master.variants[0], "peso")).toBe("5 kg");
  });

  it("uses brand_display when brand attribute is missing", () => {
    const variant = listVariant("X", {
      brand_display: "NEXO",
      attributes: {},
    });
    expect(getListVariantAttributeValue(variant, BRAND_COLUMN_KEY)).toBe("NEXO");
  });

  it("does not fallback variant_label to display_name", () => {
    const variant = listVariant("X", {
      display_name: "Fallback name",
      variant_label: null,
      attributes: {},
    });
    expect(getListVariantAttributeValue(variant, VARIANT_LABEL_COLUMN_KEY)).toBe("—");
  });
});

function detailVariant(
  sku: string,
  overrides: Partial<ProductMasterDetail["variants"][number]> = {},
) {
  return {
    id: `var-${sku}`,
    product_master_id: "master-1",
    supplier_id: "sup-1",
    supplier_code: "FDL",
    sku,
    ean: null,
    display_name: sku,
    variant_label: null,
    brand_display: null,
    latest_price: "10,00 €",
    specs: [],
    source_page: null,
    source_pages: [],
    ...overrides,
  };
}

function weightSpec(key: "peso_kg" | "peso_lb", value: string) {
  return {
    spec_definition_id: key,
    key,
    label: "Peso",
    data_type: "number" as const,
    value,
    sort_order: 10,
  };
}

describe("getDetailVariantCellValue synthetic peso", () => {
  it("resolves peso column from peso_kg spec", () => {
    const variant = detailVariant("CRO131", {
      specs: [weightSpec("peso_kg", "60 kg")],
    });
    expect(getDetailVariantCellValue(variant, "peso")).toBe("60 kg");
  });

  it("resolves peso column from peso_lb spec", () => {
    const variant = detailVariant("CRO083", {
      specs: [weightSpec("peso_lb", "12 lb")],
    });
    expect(getDetailVariantCellValue(variant, "peso")).toBe("12 lb");
  });

  it("does not use display_name when variant_label is absent", () => {
    const variant = detailVariant("X", {
      display_name: "Should not appear as Variante",
      variant_label: null,
    });
    expect(getDetailVariantCellValue(variant, VARIANT_LABEL_COLUMN_KEY)).toBe("—");
  });
});

describe("detail variant columns", () => {
  it("maps brand column on detail variants", () => {
    const master: ProductMasterDetail = {
      ...sacoGusanoMaster(),
      images: [],
      specs: [],
      variants: sacoGusanoMaster().variants.map((variant, index) => ({
        id: `var-${index}`,
        product_master_id: "master-worm-bag",
        supplier_id: "sup-1",
        supplier_code: "FDL",
        sku: variant.sku,
        ean: null,
        display_name: variant.display_name,
        variant_label: variant.variant_label,
        brand_display: variant.brand_display,
        latest_price: variant.price,
        specs: [],
        source_page: variant.source_page,
        source_pages: variant.source_pages,
      })),
    };

    const columns = resolveDetailVariantColumns(master);
    expect(columns.map((column) => column.key)).toEqual([
      VARIANT_LABEL_COLUMN_KEY,
      BRAND_COLUMN_KEY,
    ]);
    expect(getDetailVariantCellValue(master.variants[1], BRAND_COLUMN_KEY)).toBe("NEXO");
  });

  it("excludes brand and variant_label from characteristics spec columns", () => {
    const master: ProductMaster = {
      ...crossfitBarsMaster(),
      variant_columns: [
        { key: "peso", label: "PESO" },
        { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
        { key: BRAND_COLUMN_KEY, label: "Marca" },
      ],
    };
    expect(characteristicsVariantColumns(master).map((column) => column.key)).toEqual(["peso"]);
  });

  it("returns empty columns when variant_columns is empty", () => {
    const master: ProductMasterDetail = {
      ...dobhtMaster(),
      images: [],
      specs: [],
      variant_columns: [],
      variants: [
        detailVariant("DOBHT005", {
          display_name: "Disco Bumper Hi Temp 5 kgs",
          latest_price: "19,39 €",
        }),
      ],
    };
    expect(resolveDetailVariantColumns(master)).toEqual([]);
  });

  it("characteristics excludes variant_label and brand from spec columns", () => {
    const master: ProductMaster = {
      ...sacoGusanoMaster(),
      variant_columns: [
        { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
        { key: "peso", label: "PESO" },
        { key: BRAND_COLUMN_KEY, label: "Marca" },
      ],
    };
    expect(characteristicsVariantColumns(master).map((column) => column.key)).toEqual(["peso"]);
  });

  it("Saco Gusano detail resolves synthetic peso from peso_kg", () => {
    const master: ProductMasterDetail = {
      ...sacoGusanoMaster(),
      variant_columns: [
        { key: VARIANT_LABEL_COLUMN_KEY, label: "Variante" },
        { key: "peso", label: "PESO" },
        { key: BRAND_COLUMN_KEY, label: "Marca" },
      ],
      images: [],
      specs: [],
      variants: [
        detailVariant("CRO131", {
          variant_label: "2 personas - 160x30cms (60kgs)",
          brand_display: "Sin marca",
          specs: [weightSpec("peso_kg", "60 kg")],
        }),
      ],
    };
    expect(getDetailVariantCellValue(master.variants[0], "peso")).toBe("60 kg");
    expect(getDetailVariantCellValue(master.variants[0], VARIANT_LABEL_COLUMN_KEY)).toBe(
      "2 personas - 160x30cms (60kgs)",
    );
    expect(characteristicsVariantColumns(master).map((c) => c.key)).toEqual(["peso"]);
    expect(getDetailVariantCellValue(master.variants[0], "peso")).toBe("60 kg");
  });
});
