import { describe, expect, it } from "vitest";
import {
  EXPORT_PREFLIGHT_STALE_BODY,
  EXPORT_PREFLIGHT_STALE_DETAIL,
  EXPORT_PREFLIGHT_STALE_TITLE,
  HTML_FALLBACK_SHOWS_PAGE_COUNT,
  HTML_FALLBACK_TITLE,
  HTML_FALLBACK_WARNING,
  PREVIEW_PDF_ERROR_PAGINATION_HINT,
  PREVIEW_PDF_ERROR_TITLE,
  getPreviewPdfErrorBody,
  getPreviewStaleBannerText,
  previewCopyMentionsPdf,
} from "./catalogPreviewCopy";

describe("catalogPreviewCopy", () => {
  it("stale preview copy mentions PDF-backed preview and pagination", () => {
    const banner = getPreviewStaleBannerText();
    expect(previewCopyMentionsPdf(banner)).toBe(true);
    expect(banner).toContain("paginación");
    expect(previewCopyMentionsPdf(EXPORT_PREFLIGHT_STALE_TITLE)).toBe(true);
    expect(previewCopyMentionsPdf(EXPORT_PREFLIGHT_STALE_BODY)).toBe(true);
    expect(previewCopyMentionsPdf(EXPORT_PREFLIGHT_STALE_DETAIL)).toBe(true);
  });

  it("degraded PDF error copy is explicit", () => {
    expect(PREVIEW_PDF_ERROR_TITLE).toContain("vista previa PDF");
    expect(PREVIEW_PDF_ERROR_PAGINATION_HINT).toContain("motor PDF");
    expect(getPreviewPdfErrorBody("engine_unavailable")).toContain("motor PDF");
    expect(getPreviewPdfErrorBody("engine_unavailable").toLowerCase()).toContain("disponible");
  });

  it("HTML fallback is labelled approximate without page count", () => {
    expect(HTML_FALLBACK_TITLE).toContain("aproximada");
    expect(HTML_FALLBACK_WARNING).toContain("paginación");
    expect(HTML_FALLBACK_SHOWS_PAGE_COUNT).toBe(false);
  });
});
