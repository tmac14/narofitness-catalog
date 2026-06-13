import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StaticRouter } from "react-router-dom/server";
import type { ProductMaster } from "@/lib/api";
import { ProductMasterCard } from "@/components/products/ProductMasterCard";
import { ProductVariantExpandSheetBody } from "@/components/products/ProductVariantExpandSheet";
import {
  MasterListPriceCell,
  ProductRowActions,
  VariantsExpandedPanel,
} from "@/pages/ProductsPage";
import { Table, TableBody, TableRow } from "@/components/ui/table";

function makeMaster(overrides: Partial<ProductMaster> = {}): ProductMaster {
  return {
    id: "master-1",
    name: "Test product",
    brand: null,
    category_id: null,
    master_key: null,
    notes: null,
    variant_count: 1,
    references: ["SKU-1"],
    price: "10,00 €",
    variant_columns: [],
    source_page: 30,
    source_pages: [30],
    variants: [
      {
        id: "v1",
        sku: "SKU-1",
        display_name: null,
        reference_label: null,
        price: "10,00 €",
        image_url: null,
        brand: null,
        brand_display: null,
        variant_label: null,
        attributes: {},
        source_page: 30,
        source_pages: [30],
      },
    ],
    ...overrides,
  };
}

describe("ProductsPage PDF origin icon popover", () => {
  it("does not render PDF badge in master PVP column", () => {
    const html = renderToStaticMarkup(
      <Table>
        <TableBody>
          <TableRow>
            <MasterListPriceCell master={makeMaster()} />
          </TableRow>
        </TableBody>
      </Table>,
    );
    expect(html).toContain("10,00 €");
    expect(html).not.toContain("PDF p.");
    expect(html).not.toContain("Origen PDF");
  });

  it("does not render PDF badge in expanded variant PVP column", () => {
    const html = renderToStaticMarkup(
      <VariantsExpandedPanel
        master={makeMaster({
          variant_count: 2,
          variants: [
            {
              id: "v1",
              sku: "SKU-1",
              display_name: null,
              reference_label: null,
              price: "10,00 €",
              image_url: null,
              brand: null,
              brand_display: null,
              variant_label: null,
              attributes: {},
              source_page: 38,
              source_pages: [38],
            },
            {
              id: "v2",
              sku: "SKU-2",
              display_name: null,
              reference_label: null,
              price: "12,00 €",
              image_url: null,
              brand: null,
              brand_display: null,
              variant_label: null,
              attributes: {},
              source_page: 40,
              source_pages: [40],
            },
          ],
        })}
      />,
    );
    expect(html).toContain("10,00 €");
    expect(html).not.toContain("PDF p.");
    expect(html).not.toContain("Origen PDF");
  });

  it("renders PDF origin icon next to the row actions menu when source pages exist", () => {
    const html = renderToStaticMarkup(
      <ProductRowActions master={makeMaster()} expanded={false} onToggleExpand={() => {}} />,
    );
    const originIndex = html.indexOf('aria-label="Ver origen PDF"');
    const actionsIndex = html.indexOf('aria-label="Más acciones para Test product"');
    expect(originIndex).toBeGreaterThan(-1);
    expect(actionsIndex).toBeGreaterThan(-1);
    expect(originIndex).toBeLessThan(actionsIndex);
  });

  it("does not render PDF origin icon when there are no source pages", () => {
    const html = renderToStaticMarkup(
      <ProductRowActions
        master={makeMaster({
          source_page: null,
          source_pages: [],
        })}
        expanded={false}
        onToggleExpand={() => {}}
      />,
    );
    expect(html).not.toContain('aria-label="Ver origen PDF"');
    expect(html).toContain('aria-label="Más acciones para Test product"');
  });

  it("keeps PDF origin out of the actions dropdown menu", () => {
    const html = renderToStaticMarkup(
      <ProductRowActions master={makeMaster()} expanded={false} onToggleExpand={() => {}} />,
    );
    expect(html).not.toMatch(/Origen PDF: página/);
    expect(html).not.toMatch(/Origen PDF: páginas/);
  });

  it("does not render PDF origin as a table header or column cell", () => {
    const triggerHtml = renderToStaticMarkup(
      <ProductRowActions master={makeMaster()} expanded={false} onToggleExpand={() => {}} />,
    );
    expect(triggerHtml).not.toContain("<th");
    expect(triggerHtml).not.toContain("PVP");
  });

  it("renders PDF origin icon on touch-first master cards", () => {
    const html = renderToStaticMarkup(
      <ProductMasterCard master={makeMaster()} index={0} onOpenVariants={() => {}} />,
    );
    expect(html).toContain('aria-label="Ver origen PDF"');
    expect(html).not.toContain("PDF p.");
  });

  it("renders PDF origin icon on variant cards inside the expand sheet", () => {
    const html = renderToStaticMarkup(
      <StaticRouter location="/products">
        <ProductVariantExpandSheetBody
          master={makeMaster({
            variant_count: 2,
            variants: [
              makeMaster().variants[0],
              {
                ...makeMaster().variants[0],
                id: "v2",
                sku: "SKU-2",
                source_page: 42,
                source_pages: [42],
              },
            ],
          })}
        />
      </StaticRouter>,
    );
    expect(html).toContain('aria-label="Ver origen PDF"');
    expect(html).not.toMatch(/Origen PDF: página/);
  });
});
