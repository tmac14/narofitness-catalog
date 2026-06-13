import { describe, expect, it } from "vitest";
import {
  afterCatalogOptionsSavedForExport,
  afterCatalogOptionsSavedNormally,
  getUnsavedExportBlockFromFreshness,
  shouldAutoRefreshPreviewBeforeExport,
} from "./catalogPreviewFreshness";

describe("catalogPreviewFreshness", () => {
  it("blocks export on unsaved order before presentation", () => {
    expect(
      getUnsavedExportBlockFromFreshness({
        previewStale: true,
        pendingPresentation: true,
        orderDirty: true,
      }),
    ).toBe("order");
  });

  it("blocks export on unsaved presentation config", () => {
    expect(
      getUnsavedExportBlockFromFreshness({
        previewStale: false,
        pendingPresentation: true,
        orderDirty: false,
      }),
    ).toBe("presentation");
  });

  it("does not block export when only PDF preview is stale", () => {
    expect(
      getUnsavedExportBlockFromFreshness({
        previewStale: true,
        pendingPresentation: false,
        orderDirty: false,
      }),
    ).toBeNull();
  });

  it("auto-refreshes preview before export only for stale PDF preview without unsaved edits", () => {
    expect(
      shouldAutoRefreshPreviewBeforeExport({
        previewStale: true,
        pendingPresentation: false,
        orderDirty: false,
      }),
    ).toBe(true);
    expect(
      shouldAutoRefreshPreviewBeforeExport({
        previewStale: true,
        pendingPresentation: true,
        orderDirty: false,
      }),
    ).toBe(false);
    expect(
      shouldAutoRefreshPreviewBeforeExport({
        previewStale: false,
        pendingPresentation: false,
        orderDirty: false,
      }),
    ).toBe(false);
  });

  it("afterCatalogOptionsSavedForExport refreshes visible preview instead of marking stale", () => {
    expect(afterCatalogOptionsSavedForExport(true)).toBe("refresh");
    expect(afterCatalogOptionsSavedForExport(false)).toBe("noop");
  });

  it("afterCatalogOptionsSavedNormally marks stale when preview is hidden", () => {
    expect(afterCatalogOptionsSavedNormally(true)).toBe("refresh");
    expect(afterCatalogOptionsSavedNormally(false)).toBe("markStale");
  });
});
