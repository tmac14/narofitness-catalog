import { getUnsavedExportBlock, type UnsavedExportBlock } from "@/lib/exportPdf";

/** Whether PDF preview is behind saved server state (cosmetic; export uses fresh server PDF). */
export type PreviewFreshnessInput = {
  previewStale: boolean;
  pendingPresentation: boolean;
  orderDirty: boolean;
};

export function getUnsavedExportBlockFromFreshness(
  input: PreviewFreshnessInput,
): UnsavedExportBlock | null {
  return getUnsavedExportBlock(input.orderDirty, input.pendingPresentation);
}

/** Auto-refresh PDF preview once before export when only the preview is behind saved data. */
export function shouldAutoRefreshPreviewBeforeExport(input: PreviewFreshnessInput): boolean {
  return input.previewStale && !input.pendingPresentation && !input.orderDirty;
}

/**
 * After persisting general-tab options during PDF export, avoid marking preview stale:
 * export reads server state. Refresh the PDF preview when it is visible instead.
 */
export function afterCatalogOptionsSavedForExport(showPreview: boolean): "refresh" | "noop" {
  return showPreview ? "refresh" : "noop";
}

/** After persisting general-tab options outside export (user clicked Save). */
export function afterCatalogOptionsSavedNormally(showPreview: boolean): "refresh" | "markStale" {
  return showPreview ? "refresh" : "markStale";
}
