import { describe, expect, it } from "vitest";
import type { ProductMasterDetail } from "./api";
import {
  categoryBreadcrumb,
  formatReferencesSummary,
  primaryReference,
  productDetailBadges,
  variantCountLabel,
} from "./productDetailMeta";
import { masterBrandDisplay } from "./variantRepresentation";

function buildDefaultVariants(): ProductMasterDetail["variants"] {
  return [
    {
      id: "v1",
      product_master_id: "master-1",
      supplier_id: "s1",
      supplier_code: "FDL",
      sku: "CRO095",
      ean: null,
      display_name: "5 kg",
      latest_price: "10,00 €",
      specs: [],
      source_page: null,
      source_pages: [],
    },
    {
      id: "v2",
      product_master_id: "master-1",
      supplier_id: "s1",
      supplier_code: "FDL",
      sku: "CRO100",
      ean: null,
      display_name: "10 kg",
      latest_price: "12,00 €",
      specs: [],
      source_page: null,
      source_pages: [],
    },
  ];
}

function makeMaster(overrides: Partial<ProductMasterDetail> = {}): ProductMasterDetail {
  return {
    id: "master-1",
    name: "Power Bags Color",
    brand: "FDL",
    category_id: "cat-1",
    category_parent_name: "Accesorios",
    category_sub_name: "Power Bags",
    master_key: null,
    notes: "Nota interna",
    variant_count: 3,
    references: ["CRO095", "CRO100"],
    price: null,
    variant_columns: [],
    images: [],
    specs: [],
    ...overrides,
    source_page: overrides.source_page ?? null,
    source_pages: overrides.source_pages ?? [],
    variants: overrides.variants ?? buildDefaultVariants(),
  };
}

describe("productDetailMeta", () => {
  it("formats variant count label", () => {
    expect(variantCountLabel(1)).toBe("1 variante");
    expect(variantCountLabel(3)).toBe("3 variantes");
  });

  it("builds category breadcrumb", () => {
    expect(categoryBreadcrumb(makeMaster())).toBe("Accesorios › Power Bags");
    expect(
      categoryBreadcrumb(
        makeMaster({ category_parent_name: "Discos", category_sub_name: "Discos" }),
      ),
    ).toBe("Discos");
  });

  it("resolves primary reference", () => {
    expect(primaryReference(makeMaster())).toBe("CRO095");
    expect(primaryReference(makeMaster({ references: [], variants: [] }))).toBeNull();
  });

  it("summarizes references with overflow", () => {
    expect(formatReferencesSummary(makeMaster())).toBe("CRO095, CRO100");
    expect(formatReferencesSummary(makeMaster({ references: ["A", "B", "C", "D"] }))).toBe(
      "A, B +2",
    );
  });

  it("adds informational badges when images and specs are missing", () => {
    const badges = productDetailBadges(makeMaster());
    expect(badges.map((b) => b.label)).toEqual(["Sin imágenes", "Sin características"]);
  });

  it("uses brand_display for product detail brand label", () => {
    expect(masterBrandDisplay(makeMaster({ brand_display: "NEXO", brand: "Legacy" }))).toBe("NEXO");
    expect(
      masterBrandDisplay(
        makeMaster({ brand_mode: "mixed", brand_display: "Varias marcas", brand: "NEXO" }),
      ),
    ).toBe("Varias marcas");
  });

  it("omits badges when product has images and specs", () => {
    const master = makeMaster({
      images: [
        {
          id: "img-1",
          url: "/media/x.jpg",
          is_primary: true,
          status: "confirmed",
          variant_id: null,
          source_type: "upload",
          external_url: null,
        },
      ],
      specs: [
        {
          spec_definition_id: "mat",
          key: "material",
          label: "Material",
          data_type: "text",
          value: "PVC",
        },
      ],
      variants: [
        {
          ...buildDefaultVariants()[0],
          specs: [
            {
              spec_definition_id: "cap",
              key: "capacidad_balones",
              label: "Capacidad (balones)",
              data_type: "text",
              value: "12",
            },
          ],
        },
      ],
    });
    expect(productDetailBadges(master)).toEqual([]);
  });
});
