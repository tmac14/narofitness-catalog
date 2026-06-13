import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { ProductMasterDetail, ProductVariant } from "@/lib/api";
import { ProductDetailContent } from "@/components/products/ProductDetailContent";
import { ProductSummaryCard } from "@/components/products/ProductSummaryCard";
import { ProductVariantsPanel } from "@/components/products/ProductVariantsPanel";
import { SingleVariantCommercialCard } from "@/components/products/SingleVariantProductDetails";

function makeVariant(
  overrides: Partial<ProductVariant> & Pick<ProductVariant, "id" | "sku">,
): ProductVariant {
  return {
    product_master_id: "master-1",
    supplier_id: "supplier-1",
    supplier_code: "FDL",
    ean: "8436123456789",
    display_name: "Variante única",
    specs: [
      {
        spec_definition_id: "cap",
        key: "capacidad",
        label: "Capacidad",
        data_type: "text",
        value: "12",
      },
    ],
    latest_price: "3.381,30 €",
    source_page: 4,
    source_pages: [4],
    ...overrides,
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

const noop = async () => {};

const baseContentProps = {
  apiBase: "http://127.0.0.1:8000",
  productName: "Test product",
  formId: "product-general-form",
  saving: false,
  categories: [],
  attrKey: "",
  attrVal: "",
  onMasterChange: () => {},
  onSave: () => {},
  onAttrKeyChange: () => {},
  onAttrValChange: () => {},
  onSaveAttribute: () => {},
  expandedVariantId: null,
  expandedHistoryState: { status: "loaded" as const, items: [] },
  onToggleExpand: () => {},
  onUploadMasterImage: noop,
  onAddMasterImageFromUrl: noop,
  onDeleteMasterImage: noop,
  onSetMasterImagePrimary: noop,
  onUploadVariantImage: noop,
  onAddVariantImageFromUrl: noop,
  onDeleteVariantImage: noop,
  onSetVariantImagePrimary: noop,
  singleVariantHistoryState: { status: "loaded" as const, items: [] },
};

describe("ProductDetail single-variant dedicated layout", () => {
  it("does not render Variantes tab or variant table for one variant", () => {
    const html = renderToStaticMarkup(
      <ProductDetailContent
        {...baseContentProps}
        master={makeMaster([makeVariant({ id: "v1", sku: "BOC006" })])}
      />,
    );
    expect(html).not.toContain("Variantes (1)");
    expect(html).not.toContain("product-variants-detail-table");
    expect(html).not.toContain('role="tablist"');
  });

  it("shows commercial reference, supplier, EAN, price and PDF origin", () => {
    const html = renderToStaticMarkup(
      <SingleVariantCommercialCard variant={makeVariant({ id: "v1", sku: "BOC006" })} />,
    );
    expect(html).toContain("Referencia comercial");
    expect(html).toContain("BOC006");
    expect(html).toContain("FDL");
    expect(html).toContain("8436123456789");
    expect(html).toContain("3.381,30 €");
    expect(html).toContain('aria-label="Ver origen PDF"');
  });

  it("shows image empty state, specs and price evolution in integrated layout", () => {
    const html = renderToStaticMarkup(
      <ProductDetailContent
        {...baseContentProps}
        master={makeMaster([makeVariant({ id: "v1", sku: "BOC006" })])}
      />,
    );
    expect(html).toContain("Imagen de variante");
    expect(html).toContain("Sin imagen de variante");
    expect(html).toContain("Capacidad");
    expect(html).toContain("Precio y evolución");
  });

  it("hides variant count row in summary card for single-product mode", () => {
    const html = renderToStaticMarkup(
      <ProductSummaryCard
        master={makeMaster([makeVariant({ id: "v1", sku: "BOC006" })])}
        singleProductMode
      />,
    );
    expect(html).not.toContain("1 variante");
    expect(html).toContain("Resumen");
  });
});

describe("ProductDetail multi-variant layout", () => {
  it("keeps Variantes tab and tablist for multi-variant products", () => {
    const html = renderToStaticMarkup(
      <ProductDetailContent
        {...baseContentProps}
        master={makeMaster([
          makeVariant({ id: "v1", sku: "SKU-1" }),
          makeVariant({ id: "v2", sku: "SKU-2", source_pages: [8], source_page: 8 }),
        ])}
      />,
    );
    expect(html).toContain("Variantes (2)");
    expect(html).toContain('role="tablist"');
    expect(html).not.toContain("Referencia comercial");
  });

  it("keeps variant table and expandable detail controls", () => {
    const html = renderToStaticMarkup(
      <ProductVariantsPanel
        master={makeMaster([
          makeVariant({ id: "v1", sku: "SKU-1" }),
          makeVariant({ id: "v2", sku: "SKU-2" }),
        ])}
        apiBase="http://127.0.0.1:8000"
        expandedVariantId="v1"
        historyState={{ status: "loaded", items: [] }}
        onToggleExpand={() => {}}
        onUploadVariantImage={noop}
        onAddVariantImageFromUrl={noop}
        onDeleteVariantImage={noop}
      />,
    );
    expect(html).toContain("product-variants-detail-table");
    expect(html).toContain("Detalle");
    expect(html).toContain("Variante seleccionada");
  });
});
