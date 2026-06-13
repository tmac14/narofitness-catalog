import { describe, expect, it } from "vitest";
import {
  PREVIEW_PDF_PAGE_SURFACE_CLASS,
  PREVIEW_PDF_PAGE_VIEWPORT_CLASS,
  canGoToNextPage,
  canGoToPreviousPage,
  clampPreviewPage,
  computePdfPageFitScale,
  parsePreviewPageInput,
} from "./previewPageNav";

describe("previewPageNav", () => {
  it("clampPreviewPage enforces 1..totalPages", () => {
    expect(clampPreviewPage(0, 10)).toBe(1);
    expect(clampPreviewPage(-3, 10)).toBe(1);
    expect(clampPreviewPage(99, 10)).toBe(10);
    expect(clampPreviewPage(5, 10)).toBe(5);
    expect(clampPreviewPage(Number.NaN, 10)).toBe(1);
    expect(clampPreviewPage(2, 0)).toBe(1);
  });

  it("parsePreviewPageInput clamps valid pages and reverts invalid input", () => {
    expect(parsePreviewPageInput("3", 1, 10)).toBe(3);
    expect(parsePreviewPageInput("0", 4, 10)).toBe(1);
    expect(parsePreviewPageInput("999", 4, 10)).toBe(10);
    expect(parsePreviewPageInput("", 4, 10)).toBe(4);
    expect(parsePreviewPageInput("abc", 4, 10)).toBe(4);
    expect(parsePreviewPageInput("  ", 2, 5)).toBe(2);
  });

  it("canGoToPreviousPage is false only on page 1", () => {
    expect(canGoToPreviousPage(1)).toBe(false);
    expect(canGoToPreviousPage(2)).toBe(true);
  });

  it("canGoToNextPage is false only on last page", () => {
    expect(canGoToNextPage(1, 1)).toBe(false);
    expect(canGoToNextPage(1, 5)).toBe(true);
    expect(canGoToNextPage(5, 5)).toBe(false);
  });

  it("preview viewport classes avoid internal vertical scroll", () => {
    expect(PREVIEW_PDF_PAGE_VIEWPORT_CLASS).toContain("overflow-hidden");
    expect(PREVIEW_PDF_PAGE_VIEWPORT_CLASS).not.toContain("overflow-y-auto");
    expect(PREVIEW_PDF_PAGE_VIEWPORT_CLASS).not.toContain("overflow-y-scroll");
    expect(PREVIEW_PDF_PAGE_VIEWPORT_CLASS).toContain("absolute");
    expect(PREVIEW_PDF_PAGE_VIEWPORT_CLASS).toContain("inset-0");
  });

  it("page surface canvas avoids max-h/max-w shrink classes", () => {
    expect(PREVIEW_PDF_PAGE_SURFACE_CLASS).not.toContain("max-h-full");
    expect(PREVIEW_PDF_PAGE_SURFACE_CLASS).not.toContain("max-w-full");
  });

  it("computePdfPageFitScale fits A4 page into typical desktop viewport", () => {
    // A4 at 72dpi ≈ 595 × 842 pt
    const scale = computePdfPageFitScale(595, 842, 900, 700, 16);
    expect(scale).toBeGreaterThan(0.5);
    expect(scale).toBeLessThanOrEqual(1.2);
    const scaledWidth = 595 * scale;
    const scaledHeight = 842 * scale;
    expect(scaledWidth).toBeLessThanOrEqual(900 - 32);
    expect(scaledHeight).toBeLessThanOrEqual(700 - 32);
  });

  it("computePdfPageFitScale does not collapse when container is wide but short", () => {
    const scale = computePdfPageFitScale(595, 842, 1200, 800, 16);
    const scaleNarrow = computePdfPageFitScale(595, 842, 400, 800, 16);
    expect(scale).toBeGreaterThan(scaleNarrow);
  });
});
