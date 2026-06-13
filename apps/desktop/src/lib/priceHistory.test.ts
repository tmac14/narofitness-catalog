import { describe, expect, it } from "vitest";
import type { ProductVariant, VariantPriceHistoryItem } from "./api";
import {
  buildMonthlyPriceSeries,
  formatPriceDisplay,
  getPriceHistoryPointDate,
  getPriceHistorySourceLabel,
  masterPriceSummaryLabel,
  parsePriceAmount,
} from "./priceHistory";

function historyItem(overrides: Partial<VariantPriceHistoryItem> = {}): VariantPriceHistoryItem {
  return {
    list_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    imported_at: "2026-03-15T10:30:00Z",
    effective_date: null,
    price_amount: "19,39",
    source_filename: null,
    delta_pct_vs_previous: null,
    ...overrides,
  };
}

function variant(overrides: Partial<ProductVariant> = {}): ProductVariant {
  return {
    id: "v1",
    product_master_id: "master-1",
    supplier_id: "supplier-1",
    sku: "SKU-1",
    supplier_code: null,
    ean: null,
    display_name: null,
    specs: [],
    latest_price: null,
    source_page: null,
    source_pages: [],
    ...overrides,
  };
}

describe("getPriceHistoryPointDate", () => {
  it("uses effective_date when present", () => {
    const item = historyItem({
      effective_date: "2026-02-01",
      imported_at: "2026-03-15T10:30:00Z",
    });
    expect(getPriceHistoryPointDate(item)).toBe("2026-02-01");
  });

  it("uses imported_at when effective_date is absent", () => {
    const item = historyItem({
      effective_date: null,
      imported_at: "2026-03-15T10:30:00Z",
    });
    expect(getPriceHistoryPointDate(item)).toBe("2026-03-15T10:30:00Z");
  });

  it("uses imported_at when effective_date is empty string", () => {
    const item = historyItem({
      effective_date: "   ",
      imported_at: "2026-01-10T08:00:00Z",
    });
    expect(getPriceHistoryPointDate(item)).toBe("2026-01-10T08:00:00Z");
  });

  it("returns null when both dates are missing", () => {
    const item = historyItem({
      effective_date: null,
      imported_at: "",
    });
    expect(getPriceHistoryPointDate(item)).toBeNull();
  });
});

describe("getPriceHistorySourceLabel", () => {
  it("returns source_filename when present", () => {
    const item = historyItem({
      source_filename: "FDL_2026_Q1.pdf",
      list_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    });
    expect(getPriceHistorySourceLabel(item)).toBe("FDL_2026_Q1.pdf");
  });

  it("returns list_id when source_filename is absent", () => {
    const item = historyItem({
      source_filename: null,
      list_id: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    });
    expect(getPriceHistorySourceLabel(item)).toBe("b2c3d4e5-f6a7-8901-bcde-f12345678901");
  });

  it("returns null when no source metadata exists", () => {
    const item = historyItem({
      source_filename: null,
      list_id: "",
    });
    expect(getPriceHistorySourceLabel(item)).toBeNull();
  });

  it("does not invent legacy source fields", () => {
    const item = historyItem({
      source_filename: null,
      list_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    });
    expect(getPriceHistorySourceLabel(item)).toBe(item.list_id);
    expect(getPriceHistorySourceLabel(item)).not.toContain("unknown");
  });
});

describe("parsePriceAmount", () => {
  it("parses comma decimal strings", () => {
    expect(parsePriceAmount("19,39")).toBe(19.39);
  });

  it("parses dot decimal strings", () => {
    expect(parsePriceAmount("19.39 €")).toBe(19.39);
  });
});

describe("formatPriceDisplay", () => {
  it("returns null for empty input", () => {
    expect(formatPriceDisplay(null)).toBeNull();
    expect(formatPriceDisplay("")).toBeNull();
    expect(formatPriceDisplay("   ")).toBeNull();
  });

  it("formats dot-decimal API amounts in European style", () => {
    expect(formatPriceDisplay("3381.30")).toBe("3.381,30 €");
  });

  it("normalizes comma-decimal amounts with euro symbol", () => {
    expect(formatPriceDisplay("19,39 €")).toBe("19,39 €");
    expect(formatPriceDisplay("10,00 €")).toBe("10,00 €");
  });

  it("formats plain comma-decimal amounts", () => {
    expect(formatPriceDisplay("93,11")).toBe("93,11 €");
  });
});

describe("buildMonthlyPriceSeries", () => {
  it("returns empty array for 0 items", () => {
    expect(buildMonthlyPriceSeries([])).toEqual([]);
  });

  it("returns one point for one item", () => {
    const series = buildMonthlyPriceSeries([
      historyItem({
        effective_date: "2026-01-15",
        price_amount: "10,00",
        source_filename: "lista.pdf",
        delta_pct_vs_previous: "5.00",
      }),
    ]);
    expect(series).toHaveLength(1);
    expect(series[0].monthKey).toBe("2026-01");
    expect(series[0].price).toBe(10);
    expect(series[0].sourceLabel).toBe("lista.pdf");
    expect(series[0].deltaPct).toBe("5.00");
    expect(series[0].item.price_amount).toBe("10,00");
  });

  it("groups multiple items in same month using the latest by date", () => {
    const series = buildMonthlyPriceSeries([
      historyItem({
        list_id: "1",
        effective_date: "2026-03-01",
        price_amount: "10,00",
        imported_at: "2026-03-01T08:00:00Z",
      }),
      historyItem({
        list_id: "2",
        effective_date: "2026-03-20",
        price_amount: "12,50",
        imported_at: "2026-03-20T08:00:00Z",
      }),
    ]);
    expect(series).toHaveLength(1);
    expect(series[0].price).toBe(12.5);
    expect(series[0].item.list_id).toBe("2");
  });

  it("orders months chronologically ascending", () => {
    const series = buildMonthlyPriceSeries([
      historyItem({ list_id: "b", effective_date: "2026-04-01", price_amount: "15,00" }),
      historyItem({ list_id: "a", effective_date: "2026-02-01", price_amount: "10,00" }),
    ]);
    expect(series.map((point) => point.monthKey)).toEqual(["2026-02", "2026-04"]);
  });

  it("prefers effective_date over imported_at for month grouping", () => {
    const series = buildMonthlyPriceSeries([
      historyItem({
        effective_date: "2026-05-01",
        imported_at: "2026-03-01T10:00:00Z",
        price_amount: "20,00",
      }),
    ]);
    expect(series[0].monthKey).toBe("2026-05");
  });
});

describe("masterPriceSummaryLabel", () => {
  it("returns no price label when no variants have price", () => {
    expect(masterPriceSummaryLabel([variant(), variant({ latest_price: null })])).toBe(
      "Sin precio registrado",
    );
  });

  it("returns single variant price", () => {
    expect(masterPriceSummaryLabel([variant({ latest_price: "19,39 €" })])).toBe("19,39 €");
  });

  it("returns same price when all variants match", () => {
    expect(
      masterPriceSummaryLabel([
        variant({ latest_price: "10,00 €" }),
        variant({ latest_price: "10,00 €" }),
      ]),
    ).toBe("10,00 €");
  });

  it("returns range when prices differ", () => {
    expect(
      masterPriceSummaryLabel([
        variant({ latest_price: "8,50 €" }),
        variant({ latest_price: "12,00 €" }),
      ]),
    ).toBe("8,50 € – 12,00 €");
  });
});
