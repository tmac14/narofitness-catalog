import { describe, expect, it } from "vitest";

import { BREAKPOINT_PX } from "@/lib/responsive/breakpoints";
import {
  PRICE_LIST_DIFF_VIEW_POLICY,
  PRODUCTS_LIST_VIEW_POLICY,
  SUPPLIERS_PROFILES_VIEW_POLICY,
  computeDataViewModeFromWidth,
} from "@/hooks/useDataViewMode";

describe("computeDataViewModeFromWidth", () => {
  it("uses cards on mobile for the products list policy", () => {
    const result = computeDataViewModeFromWidth(390, PRODUCTS_LIST_VIEW_POLICY);
    expect(result.platform).toBe("mobile");
    expect(result.mode).toBe("sheet");
    expect(result.showTable).toBe(false);
    expect(result.showCards).toBe(true);
  });

  it("uses cards on tablet for the products list policy", () => {
    const result = computeDataViewModeFromWidth(768, PRODUCTS_LIST_VIEW_POLICY);
    expect(result.platform).toBe("tablet");
    expect(result.mode).toBe("sheet");
    expect(result.showTable).toBe(false);
    expect(result.showCards).toBe(true);
  });

  it("uses table on desktop and wide for the products list policy", () => {
    for (const width of [BREAKPOINT_PX.desktopMin, BREAKPOINT_PX.wideMin]) {
      const result = computeDataViewModeFromWidth(width, PRODUCTS_LIST_VIEW_POLICY);
      expect(result.platform).toMatch(/^(desktop|wide)$/);
      expect(result.mode).toBe("table");
      expect(result.showTable).toBe(true);
      expect(result.showCards).toBe(false);
    }
  });

  it("reacts to boundary widths without duplicating breakpoint numbers in callers", () => {
    expect(
      computeDataViewModeFromWidth(BREAKPOINT_PX.mobileMax, PRODUCTS_LIST_VIEW_POLICY).platform,
    ).toBe("mobile");
    expect(
      computeDataViewModeFromWidth(BREAKPOINT_PX.tabletMin, PRODUCTS_LIST_VIEW_POLICY).platform,
    ).toBe("tablet");
    expect(
      computeDataViewModeFromWidth(BREAKPOINT_PX.desktopMin, PRODUCTS_LIST_VIEW_POLICY).platform,
    ).toBe("desktop");
  });

  it("uses cards on tablet for the suppliers profiles policy", () => {
    const result = computeDataViewModeFromWidth(768, SUPPLIERS_PROFILES_VIEW_POLICY);
    expect(result.platform).toBe("tablet");
    expect(result.showTable).toBe(false);
    expect(result.showCards).toBe(true);
  });

  it("uses table on desktop for the suppliers profiles policy", () => {
    const result = computeDataViewModeFromWidth(1024, SUPPLIERS_PROFILES_VIEW_POLICY);
    expect(result.platform).toBe("desktop");
    expect(result.mode).toBe("table");
    expect(result.showTable).toBe(true);
    expect(result.showCards).toBe(false);
  });

  it("uses cards on tablet for the price list diff policy", () => {
    const result = computeDataViewModeFromWidth(768, PRICE_LIST_DIFF_VIEW_POLICY);
    expect(result.platform).toBe("tablet");
    expect(result.showTable).toBe(false);
    expect(result.showCards).toBe(true);
  });

  it("uses table on desktop for the price list diff policy", () => {
    const result = computeDataViewModeFromWidth(1024, PRICE_LIST_DIFF_VIEW_POLICY);
    expect(result.platform).toBe("desktop");
    expect(result.mode).toBe("table");
    expect(result.showTable).toBe(true);
    expect(result.showCards).toBe(false);
  });
});
