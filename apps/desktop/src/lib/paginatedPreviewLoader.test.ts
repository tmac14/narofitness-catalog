import { describe, expect, it, vi } from "vitest";
import {
  PREVIEW_PDF_CANVAS_SHELL_CLASS,
  PREVIEW_PDF_WORKSPACE_CLASS,
  PreviewPdfLoadError,
  classifyPreviewPdfFailure,
  derivePreviewPdfLoadStatus,
  fetchPreviewPdfForViewer,
  isPreviewFetchAbortError,
  shouldRefetchPreviewPdf,
  toPreviewPdfErrorDetail,
} from "./paginatedPreviewLoader";

describe("paginatedPreviewLoader", () => {
  it("calls fetchCatalogPreviewPdf with catalogId and previewKey", async () => {
    const fetchFn = vi.fn().mockResolvedValue({
      blob: new Blob(["pdf"]),
      totalPages: 4,
      pdfEngine: "playwright",
      generatedAt: "2026-06-08T10:00:00Z",
    });

    const result = await fetchPreviewPdfForViewer({ catalogId: "cat-42", previewKey: 7 }, fetchFn);

    expect(fetchFn).toHaveBeenCalledOnce();
    expect(fetchFn).toHaveBeenCalledWith("cat-42", 7, { signal: undefined });
    expect(result.totalPages).toBe(4);
  });

  it("forwards abort signal to preview fetch", async () => {
    const fetchFn = vi.fn().mockResolvedValue({
      blob: new Blob(["pdf"]),
      totalPages: 1,
      pdfEngine: null,
      generatedAt: null,
    });
    const controller = new AbortController();

    await fetchPreviewPdfForViewer(
      { catalogId: "cat-42", previewKey: 2, signal: controller.signal },
      fetchFn,
    );

    expect(fetchFn).toHaveBeenCalledWith("cat-42", 2, { signal: controller.signal });
  });

  it("isPreviewFetchAbortError detects cancelled fetches", () => {
    expect(isPreviewFetchAbortError(new DOMException("aborted", "AbortError"))).toBe(true);
    expect(isPreviewFetchAbortError(new Error("timeout"))).toBe(false);
  });

  it("refetches when previewKey changes", () => {
    expect(shouldRefetchPreviewPdf(1, 1)).toBe(false);
    expect(shouldRefetchPreviewPdf(1, 2)).toBe(true);
    expect(shouldRefetchPreviewPdf(null, 0)).toBe(true);
  });

  it("classifies 503 and PDF engine errors as engine_unavailable", () => {
    expect(
      classifyPreviewPdfFailure(new Error("Motor PDF no disponible. Service unavailable")),
    ).toBe("engine_unavailable");
    expect(toPreviewPdfErrorDetail(new PreviewPdfLoadError("pdfjs_load_failed")).kind).toBe(
      "pdfjs_load_failed",
    );
    expect(classifyPreviewPdfFailure(new Error("Network error"))).toBe("fetch_failed");
  });

  it("derivePreviewPdfLoadStatus reports loading and error states", () => {
    expect(derivePreviewPdfLoadStatus({ fetching: true, failed: false })).toBe("loading");
    expect(derivePreviewPdfLoadStatus({ fetching: false, failed: true })).toBe("error");
    expect(derivePreviewPdfLoadStatus({ fetching: false, failed: false })).toBe("ready");
    expect(derivePreviewPdfLoadStatus({ fetching: true, failed: true })).toBe("error");
  });

  it("preview layout classes avoid internal vertical scroll", () => {
    expect(PREVIEW_PDF_CANVAS_SHELL_CLASS).toContain("overflow-hidden");
    expect(PREVIEW_PDF_CANVAS_SHELL_CLASS).not.toContain("overflow-y-auto");
    expect(PREVIEW_PDF_CANVAS_SHELL_CLASS).not.toContain("overflow-y-scroll");
    expect(PREVIEW_PDF_CANVAS_SHELL_CLASS).toContain("relative");
    expect(PREVIEW_PDF_CANVAS_SHELL_CLASS).not.toContain("items-center");
    expect(PREVIEW_PDF_WORKSPACE_CLASS).toContain("overflow-hidden");
    expect(PREVIEW_PDF_WORKSPACE_CLASS).toContain("flex-1");
  });
});
