import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { ProductVariant } from "@/lib/api";
import { ProductVariantDetailPanel } from "@/components/products/ProductVariantDetailPanel";

const baseVariant: ProductVariant & { images?: [] } = {
  id: "variant-1",
  product_master_id: "master-1",
  supplier_id: "supplier-1",
  supplier_code: "FDL",
  sku: "BOC006",
  ean: null,
  display_name: "Barra Tecnica - 2 Mts AZUL",
  specs: [],
  latest_price: "93.11",
  source_page: 14,
  source_pages: [14],
  images: [],
};

const noop = async () => {};

describe("ProductVariantDetailPanel", () => {
  it("renders without crash when onAddImageFromUrl is provided", () => {
    const html = renderToStaticMarkup(
      <ProductVariantDetailPanel
        variant={baseVariant}
        apiBase="http://127.0.0.1:8000"
        historyState={{ status: "loaded", items: [] }}
        onUploadImage={noop}
        onAddImageFromUrl={noop}
        onDeleteImage={noop}
      />,
    );
    expect(html).toContain("BOC006");
    expect(html).toContain("Usar URL externa");
  });

  it("renders variant image gallery with external URL action", () => {
    const html = renderToStaticMarkup(
      <ProductVariantDetailPanel
        variant={baseVariant}
        apiBase="http://127.0.0.1:8000"
        historyState={{ status: "loaded", items: [] }}
        onUploadImage={noop}
        onAddImageFromUrl={noop}
        onDeleteImage={noop}
      />,
    );
    expect(html).toContain("Imagen de variante");
    expect(html).toContain("Usar URL externa");
  });
});
