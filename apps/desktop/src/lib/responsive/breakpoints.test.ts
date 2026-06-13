import { describe, expect, it } from "vitest";
import {
  BREAKPOINT_PX,
  LEGACY_TAILWIND_MIN_WIDTH_PX,
  TAILWIND_SEMANTIC_SCREENS,
} from "./breakpoints";
import { assertPlatformBandsContiguous, classifyPlatformWidth } from "./platform";
import { allowsHorizontalScroll, resolveDataViewMode } from "./tablePolicy";

describe("BREAKPOINT_PX boundaries", () => {
  const boundaryWidths = [0, 639, 640, 1023, 1024, 1279, 1280] as const;

  it("classifies exact boundary widths without gaps or overlaps", () => {
    expect(classifyPlatformWidth(0)).toBe("mobile");
    expect(classifyPlatformWidth(639)).toBe("mobile");
    expect(classifyPlatformWidth(640)).toBe("tablet");
    expect(classifyPlatformWidth(1023)).toBe("tablet");
    expect(classifyPlatformWidth(1024)).toBe("desktop");
    expect(classifyPlatformWidth(1279)).toBe("desktop");
    expect(classifyPlatformWidth(1280)).toBe("wide");

    for (const width of boundaryWidths) {
      expect(() => classifyPlatformWidth(width)).not.toThrow();
    }
  });

  it("covers every integer between bands contiguously", () => {
    assertPlatformBandsContiguous();

    for (let width = 0; width <= 1400; width += 1) {
      const platform = classifyPlatformWidth(width);
      expect(["mobile", "tablet", "desktop", "wide"]).toContain(platform);
    }
  });

  it("aligns TAILWIND_SEMANTIC_SCREENS with BREAKPOINT_PX", () => {
    expect(TAILWIND_SEMANTIC_SCREENS.mobile).toEqual({ max: "639px" });
    expect(TAILWIND_SEMANTIC_SCREENS.tablet).toEqual({ min: "640px", max: "1023px" });
    expect(TAILWIND_SEMANTIC_SCREENS.desktop).toEqual({ min: "1024px", max: "1279px" });
    expect(TAILWIND_SEMANTIC_SCREENS.wide).toBe("1280px");
  });

  it("keeps legacy Tailwind min-width entry points unchanged", () => {
    expect(LEGACY_TAILWIND_MIN_WIDTH_PX.sm).toBe(BREAKPOINT_PX.tabletMin);
    expect(LEGACY_TAILWIND_MIN_WIDTH_PX.lg).toBe(BREAKPOINT_PX.desktopMin);
    expect(LEGACY_TAILWIND_MIN_WIDTH_PX.xl).toBe(BREAKPOINT_PX.wideMin);
    expect(LEGACY_TAILWIND_MIN_WIDTH_PX.md).toBe(768);
  });
});

describe("resolveDataViewMode", () => {
  it("never defaults to table on mobile", () => {
    expect(
      resolveDataViewMode({
        platform: "mobile",
        columnCount: 2,
        complexity: "simple",
      }),
    ).toBe("cards");

    expect(
      resolveDataViewMode({
        platform: "mobile",
        columnCount: 8,
        complexity: "complex",
        requiresComparison: true,
      }),
    ).toBe("cards");
  });

  it("uses sheet on mobile when row detail or bulk actions are required", () => {
    expect(
      resolveDataViewMode({
        platform: "mobile",
        columnCount: 3,
        complexity: "simple",
        hasRowDetail: true,
      }),
    ).toBe("sheet");
  });

  it("allows tablet tables for moderate column sets and comparison tasks", () => {
    expect(
      resolveDataViewMode({
        platform: "tablet",
        columnCount: 4,
        complexity: "moderate",
      }),
    ).toBe("table");

    expect(
      resolveDataViewMode({
        platform: "tablet",
        columnCount: 5,
        complexity: "moderate",
        requiresComparison: true,
      }),
    ).toBe("table");
  });

  it("prefers cards or sheet on tablet when columns exceed policy threshold", () => {
    expect(
      resolveDataViewMode({
        platform: "tablet",
        columnCount: 6,
        complexity: "moderate",
      }),
    ).toBe("cards");

    expect(
      resolveDataViewMode({
        platform: "tablet",
        columnCount: 6,
        complexity: "complex",
        hasRowDetail: true,
      }),
    ).toBe("sheet");
  });

  it("defaults to table on desktop and wide", () => {
    expect(
      resolveDataViewMode({
        platform: "desktop",
        columnCount: 6,
        complexity: "moderate",
      }),
    ).toBe("table");

    expect(
      resolveDataViewMode({
        platform: "wide",
        columnCount: 6,
        complexity: "moderate",
      }),
    ).toBe("table");
  });

  it("escapes very wide complex desktop tables to cards or sheet", () => {
    expect(
      resolveDataViewMode({
        platform: "desktop",
        columnCount: 9,
        complexity: "complex",
      }),
    ).toBe("cards");

    expect(
      resolveDataViewMode({
        platform: "wide",
        columnCount: 10,
        complexity: "complex",
        hasRowDetail: true,
      }),
    ).toBe("sheet");
  });
});

describe("allowsHorizontalScroll", () => {
  it("permits horizontal scroll only for table mode on non-mobile platforms", () => {
    expect(allowsHorizontalScroll("table", "tablet")).toBe(true);
    expect(allowsHorizontalScroll("table", "desktop")).toBe(true);
    expect(allowsHorizontalScroll("table", "mobile")).toBe(false);
    expect(allowsHorizontalScroll("cards", "tablet")).toBe(false);
    expect(allowsHorizontalScroll("sheet", "desktop")).toBe(false);
  });
});
