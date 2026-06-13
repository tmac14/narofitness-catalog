import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchCatalogPreviewPdf } from "./api";

function mockPdfResponse(options: {
  ok?: boolean;
  status?: number;
  headers?: Record<string, string>;
  body?: Blob;
  text?: string;
}): Response {
  const blob = options.body ?? new Blob(["%PDF-1.4"], { type: "application/pdf" });
  return {
    ok: options.ok ?? true,
    status: options.status ?? 200,
    headers: new Headers(options.headers),
    blob: () => Promise.resolve(blob),
    text: () => Promise.resolve(options.text ?? ""),
  } as Response;
}

describe("fetchCatalogPreviewPdf", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("calls POST preview/pdf without cacheBust", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockPdfResponse({
        headers: {
          "X-Total-Pages": "3",
          "X-Pdf-Engine": "playwright",
          "X-Preview-Generated-At": "2026-06-07T12:00:00+00:00",
        },
      }),
    );

    const result = await fetchCatalogPreviewPdf("cat-1");

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toMatch(/\/catalogs\/cat-1\/preview\/pdf$/);
    expect(init?.method).toBe("POST");
    expect(result.blob).toBeInstanceOf(Blob);
    expect(result.totalPages).toBe(3);
    expect(result.pdfEngine).toBe("playwright");
    expect(result.generatedAt).toBe("2026-06-07T12:00:00+00:00");
  });

  it("calls POST preview/pdf with cache_bust query", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockPdfResponse({ headers: { "X-Total-Pages": "1" } }));

    await fetchCatalogPreviewPdf("cat-1", 1717770000);

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/catalogs/cat-1/preview/pdf?cache_bust=1717770000");
  });

  it("reads Blob response body", async () => {
    const mockFetch = vi.mocked(fetch);
    const pdfBlob = new Blob(["pdf-bytes"], { type: "application/pdf" });
    mockFetch.mockResolvedValueOnce(
      mockPdfResponse({ body: pdfBlob, headers: { "X-Total-Pages": "2" } }),
    );

    const result = await fetchCatalogPreviewPdf("cat-1");
    expect(result.blob).toBe(pdfBlob);
    expect(result.blob.type).toBe("application/pdf");
  });

  it("parses X-Total-Pages header", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockPdfResponse({ headers: { "X-Total-Pages": "12" } }));

    const result = await fetchCatalogPreviewPdf("cat-1");
    expect(result.totalPages).toBe(12);
  });

  it("reads X-Pdf-Engine and X-Preview-Generated-At when present", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockPdfResponse({
        headers: {
          "X-Total-Pages": "1",
          "X-Pdf-Engine": "weasyprint",
          "X-Preview-Generated-At": "2026-01-15T08:30:00Z",
        },
      }),
    );

    const result = await fetchCatalogPreviewPdf("cat-1");
    expect(result.pdfEngine).toBe("weasyprint");
    expect(result.generatedAt).toBe("2026-01-15T08:30:00Z");
  });

  it("falls back to 1 when X-Total-Pages is missing or invalid", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockPdfResponse({ headers: {} }));
    expect((await fetchCatalogPreviewPdf("cat-1")).totalPages).toBe(1);

    mockFetch.mockResolvedValueOnce(mockPdfResponse({ headers: { "X-Total-Pages": "0" } }));
    expect((await fetchCatalogPreviewPdf("cat-1")).totalPages).toBe(1);

    mockFetch.mockResolvedValueOnce(mockPdfResponse({ headers: { "X-Total-Pages": "abc" } }));
    expect((await fetchCatalogPreviewPdf("cat-1")).totalPages).toBe(1);
  });

  it("throws on non-OK response using existing error style", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockPdfResponse({
        ok: false,
        status: 404,
        text: JSON.stringify({ detail: "Catalog not found" }),
      }),
    );

    await expect(fetchCatalogPreviewPdf("missing")).rejects.toThrow("Catalog not found");
  });

  it("passes abort signal to fetch", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockPdfResponse({ headers: { "X-Total-Pages": "1" } }));
    const controller = new AbortController();

    await fetchCatalogPreviewPdf("cat-1", 3, { signal: controller.signal });

    const init = mockFetch.mock.calls[0][1] as RequestInit;
    expect(init.signal).toBeDefined();
  });

  it("prefixes 503 errors with motor PDF message", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockPdfResponse({
        ok: false,
        status: 503,
        text: JSON.stringify({ detail: "engine offline" }),
      }),
    );

    await expect(fetchCatalogPreviewPdf("cat-1")).rejects.toThrow("Motor PDF no disponible");
  });
});
