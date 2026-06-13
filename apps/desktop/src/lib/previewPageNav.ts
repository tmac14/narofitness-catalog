/** 1-based page navigation helpers for paginated PDF preview. */

export function clampPreviewPage(page: number, totalPages: number): number {
  const safeTotal = Math.max(1, Math.floor(totalPages) || 1);
  if (!Number.isFinite(page)) return 1;
  const n = Math.floor(page);
  if (n < 1) return 1;
  if (n > safeTotal) return safeTotal;
  return n;
}

export function parsePreviewPageInput(
  raw: string,
  currentPage: number,
  totalPages: number,
): number {
  const trimmed = raw.trim();
  if (!trimmed) return clampPreviewPage(currentPage, totalPages);
  const parsed = Number.parseInt(trimmed, 10);
  if (!Number.isFinite(parsed)) return clampPreviewPage(currentPage, totalPages);
  return clampPreviewPage(parsed, totalPages);
}

export function canGoToPreviousPage(currentPage: number): boolean {
  return currentPage > 1;
}

export function canGoToNextPage(currentPage: number, totalPages: number): boolean {
  return currentPage < Math.max(1, totalPages);
}

/** Fit PDF page (pt) inside available container (px), preserving aspect ratio. */
export function computePdfPageFitScale(
  pageWidth: number,
  pageHeight: number,
  containerWidth: number,
  containerHeight: number,
  paddingPx = 0,
): number {
  if (pageWidth <= 0 || pageHeight <= 0) return 1;
  const availableWidth = Math.max(containerWidth - paddingPx * 2, 1);
  const availableHeight = Math.max(containerHeight - paddingPx * 2, 1);
  const widthScale = availableWidth / pageWidth;
  const heightScale = availableHeight / pageHeight;
  return Math.min(widthScale, heightScale);
}

/** Minimum container height (px) when layout has not resolved yet. */
export const PREVIEW_PDF_VIEWPORT_MIN_HEIGHT_PX = 480;

export const PREVIEW_PDF_PAGE_VIEWPORT_PADDING_PX = 16;

/** Viewport fills the canvas shell; no internal vertical scroll. */
export const PREVIEW_PDF_PAGE_VIEWPORT_CLASS =
  "preview-pdf-page-viewport absolute inset-0 flex items-center justify-center overflow-hidden p-4";

export const PREVIEW_PDF_PAGE_SURFACE_CLASS = "preview-pdf-page-surface block bg-white shadow-lg";

export const PREVIEW_PDF_PAGE_CANVAS_WRAPPER_CLASS =
  "preview-pdf-page-canvas-wrapper absolute inset-0 min-h-0";
