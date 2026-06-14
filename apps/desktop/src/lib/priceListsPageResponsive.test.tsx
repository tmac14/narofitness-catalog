import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { PriceDiffCard } from "@/components/price-lists/PriceDiffCard";
import { PriceDiffCardList } from "@/components/price-lists/PriceDiffCardList";
import { PriceListsToolbar } from "@/components/price-lists/PriceListsToolbar";
import type { PriceDiffRow } from "@/components/price-lists/priceDiffLabels";
import {
  PRICE_LIST_DIFF_VIEW_POLICY,
  computeDataViewModeFromWidth,
} from "@/hooks/useDataViewMode";

function makeDiffRow(overrides: Partial<PriceDiffRow> = {}): PriceDiffRow {
  return {
    sku: "SKU-001",
    name: "Producto de prueba",
    price_a: "10,00 €",
    price_b: "12,00 €",
    delta_abs: "2,00 €",
    delta_pct: "20",
    change_type: "changed",
    ...overrides,
  };
}

describe("PriceListsPage responsive cards and toolbar", () => {
  it("renders PriceDiffCard with BEM classes, change badge, and no table markup", () => {
    const html = renderToStaticMarkup(<PriceDiffCard row={makeDiffRow()} index={0} />);
    expect(html).toContain("responsive-data-card");
    expect(html).toContain("Producto de prueba");
    expect(html).toContain("SKU-001");
    expect(html).toContain("Cambiado");
    expect(html).not.toContain("<table");
  });

  it("renders PriceDiffCardList with SKU, prices, and deltas", () => {
    const html = renderToStaticMarkup(
      <PriceDiffCardList
        items={[
          makeDiffRow(),
          makeDiffRow({
            sku: "SKU-002",
            name: "Solo en tarifa A",
            price_b: null,
            delta_abs: null,
            delta_pct: null,
            change_type: "only_a",
          }),
        ]}
      />,
    );
    expect(html).toContain("responsive-data-card-list__items");
    expect(html).toContain("10,00 €");
    expect(html).toContain("12,00 €");
    expect(html).toContain("2,00 €");
    expect(html).toContain("20%");
    expect(html).toContain("Solo en A");
    expect(html).toContain("responsive-data-card--only_a");
    expect(html).not.toContain("<table");
  });

  it("maps price list diff policy to cards below desktop and table at desktop+", () => {
    for (const width of [360, 640, 1023]) {
      expect(computeDataViewModeFromWidth(width, PRICE_LIST_DIFF_VIEW_POLICY).showCards).toBe(true);
    }
    expect(computeDataViewModeFromWidth(1024, PRICE_LIST_DIFF_VIEW_POLICY).showTable).toBe(true);
  });

  it("renders toolbar filter toggle with aria-expanded and Compare min-h-11", () => {
    const html = renderToStaticMarkup(
      <PriceListsToolbar
        lists={[
          {
            id: "a",
            source_filename: "tarifa-a.pdf",
            imported_at: "2026-01-01T00:00:00Z",
          },
          {
            id: "b",
            source_filename: "tarifa-b.pdf",
            imported_at: "2026-02-01T00:00:00Z",
          },
        ]}
        listA="a"
        listB="b"
        onlyChanges={true}
        minPct="5"
        direction="up"
        comparing={false}
        collapseFilters={true}
        defaultFiltersExpanded={false}
        onListAChange={() => {}}
        onListBChange={() => {}}
        onOnlyChangesChange={() => {}}
        onMinPctChange={() => {}}
        onDirectionChange={() => {}}
        onCompare={() => {}}
      />,
    );
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain("responsive-collapsible-panel__toggle");
    expect(html).toContain("min-h-11");
    expect(html).toContain("Comparar");
  });
});
