import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { ProductMasterDetail, ProductVariant } from "@/lib/api";
import {
  ProductVariantsPanel,
  VariantListPriceCell,
  VariantRowDetailControls,
} from "@/components/products/ProductVariantsPanel";
import { Table, TableBody, TableRow } from "@/components/ui/table";

function makeVariant(
  overrides: Partial<ProductVariant> & Pick<ProductVariant, "id" | "sku">,
): ProductVariant {
  return {
    product_master_id: "master-1",
    supplier_id: "supplier-1",
    supplier_code: null,
    ean: null,
    display_name: null,
    specs: [],
    latest_price: "10,00 €",
    source_page: null,
    source_pages: [],
    ...overrides,
  };
}

function makeMaster(variants: ProductVariant[]): ProductMasterDetail {
  return {
    id: "master-1",
    name: "Test product",
    brand: null,
    category_id: null,
    master_key: null,
    notes: null,
    variant_count: variants.length,
    references: variants.map((v) => v.sku),
    price: null,
    variant_columns: [],
    source_page: null,
    source_pages: [],
    images: [],
    variants,
  };
}

const noop = async () => {};

function renderPanel(master: ProductMasterDetail, expandedVariantId: string | null = null) {
  return renderToStaticMarkup(
    <ProductVariantsPanel
      master={master}
      apiBase="http://127.0.0.1:8000"
      expandedVariantId={expandedVariantId}
      historyState={{ status: "loaded", items: [] }}
      onToggleExpand={() => {}}
      onUploadVariantImage={noop}
      onAddVariantImageFromUrl={noop}
      onDeleteVariantImage={noop}
    />,
  );
}

describe("ProductVariantsPanel UX polish", () => {
  it("does not render PDF badge in the price column", () => {
    const html = renderPanel(
      makeMaster([
        makeVariant({
          id: "v1",
          sku: "SKU-1",
          source_page: 38,
          source_pages: [38],
        }),
      ]),
    );
    expect(html).not.toContain("PDF p.");
    expect(html).not.toContain("Sin página");
  });

  it("renders formatted price in the price column", () => {
    const html = renderToStaticMarkup(
      <Table>
        <TableBody>
          <TableRow>
            <VariantListPriceCell
              variant={makeVariant({
                id: "v1",
                sku: "SKU-1",
                latest_price: "3381.30",
              })}
            />
          </TableRow>
        </TableBody>
      </Table>,
    );
    expect(html).toContain("3.381,30 €");
    expect(html).not.toContain("3381.30");
  });

  it("renders PDF origin icon outside the price column next to detail control", () => {
    const html = renderToStaticMarkup(
      <Table>
        <TableBody>
          <TableRow>
            <VariantRowDetailControls
              variant={makeVariant({
                id: "v1",
                sku: "SKU-1",
                source_page: 4,
                source_pages: [4],
              })}
              expanded={false}
              onToggleExpand={() => {}}
            />
          </TableRow>
        </TableBody>
      </Table>,
    );
    const originIndex = html.indexOf('aria-label="Ver origen PDF"');
    const detailIndex = html.indexOf('aria-label="Ver detalle de SKU-1"');
    expect(originIndex).toBeGreaterThan(-1);
    expect(detailIndex).toBeGreaterThan(-1);
    expect(originIndex).toBeLessThan(detailIndex);
  });

  it("omits PDF origin icon when variant has no source pages", () => {
    const html = renderToStaticMarkup(
      <VariantRowDetailControls
        variant={makeVariant({
          id: "v1",
          sku: "SKU-NONE",
          source_page: null,
          source_pages: [],
        })}
        expanded={false}
        onToggleExpand={() => {}}
      />,
    );
    expect(html).not.toContain('aria-label="Ver origen PDF"');
  });

  it("marks expanded row with active state attributes", () => {
    const html = renderPanel(
      makeMaster([
        makeVariant({
          id: "v1",
          sku: "SKU-1",
          source_page: 38,
          source_pages: [38],
        }),
      ]),
      "v1",
    );
    expect(html).toContain('data-expanded="true"');
    expect(html).toContain("product-variants-table-row");
    expect(html).toContain("is-expanded");
  });

  it("reflects open detail control state with Ocultar label", () => {
    const html = renderToStaticMarkup(
      <VariantRowDetailControls
        variant={makeVariant({ id: "v1", sku: "SKU-1" })}
        expanded={true}
        onToggleExpand={() => {}}
      />,
    );
    expect(html).toContain('aria-expanded="true"');
    expect(html).toContain("Ocultar");
    expect(html).toContain('aria-label="Ocultar detalle de SKU-1"');
  });

  it("reflects closed detail control state with Detalle label", () => {
    const html = renderToStaticMarkup(
      <VariantRowDetailControls
        variant={makeVariant({ id: "v1", sku: "SKU-1" })}
        expanded={false}
        onToggleExpand={() => {}}
      />,
    );
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain("Detalle");
  });

  it("renders expanded variant detail without crash", () => {
    const html = renderPanel(
      makeMaster([
        makeVariant({
          id: "v1",
          sku: "SKU-1",
          source_page: 38,
          source_pages: [38],
        }),
      ]),
      "v1",
    );
    expect(html).toContain("SKU-1");
    expect(html).toContain("Usar URL externa");
    expect(html).toContain("Variante seleccionada");
  });

  it("does not add a new table column for PDF origin", () => {
    const html = renderPanel(
      makeMaster([
        makeVariant({
          id: "v1",
          sku: "SKU-1",
          source_page: 38,
          source_pages: [38],
        }),
      ]),
    );
    const headerMatches = html.match(/<th[^>]*>/g) ?? [];
    expect(headerMatches.some((tag) => tag.includes("Origen PDF"))).toBe(false);
    expect(headerMatches.some((tag) => tag.includes("PDF"))).toBe(false);
  });
});
