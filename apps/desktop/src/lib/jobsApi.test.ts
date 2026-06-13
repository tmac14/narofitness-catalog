import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { JobOut } from "./api";
import { cancelJob, createCatalogPdfExportJob, downloadJobResult, getJob, listJobs } from "./api";

function mockJsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  } as Response;
}

function mockBlobResponse(body?: Blob): Response {
  const blob = body ?? new Blob(["%PDF-1.4"], { type: "application/pdf" });
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/pdf" }),
    blob: () => Promise.resolve(blob),
    text: () => Promise.resolve(""),
  } as Response;
}

const sampleJob: JobOut = {
  id: "job-1",
  job_type: "catalog_export_pdf",
  status: "queued",
  progress_percent: 0,
  message: "Exportacion PDF en cola",
  error_message: null,
  catalog_id: "cat-1",
  catalog_name: "QA Stress Catalog",
  created_at: "2026-06-07T12:00:00Z",
  started_at: null,
  finished_at: null,
  download_available: false,
  can_cancel: true,
  metadata: { catalog_name: "QA Stress Catalog", extra: true },
};

describe("jobs API helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("listJobs builds query params correctly", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockJsonResponse({ items: [sampleJob], total: 1 }));

    await listJobs({
      status: "running",
      job_type: "catalog_export_pdf",
      catalog_id: "cat-1",
      active_only: true,
      limit: 10,
    });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("/jobs?");
    expect(url).toContain("status=running");
    expect(url).toContain("job_type=catalog_export_pdf");
    expect(url).toContain("catalog_id=cat-1");
    expect(url).toContain("active_only=true");
    expect(url).toContain("limit=10");
  });

  it("getJob calls correct endpoint", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockJsonResponse(sampleJob));

    const result = await getJob("job-1");

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/jobs/job-1");
    expect(init?.method).toBeUndefined();
    expect(result.id).toBe("job-1");
    expect(result.metadata.extra).toBe(true);
  });

  it("cancelJob calls POST and parses JobCancelResponse", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({
        job: { ...sampleJob, status: "cancelled", can_cancel: false },
        cancelled: true,
      }),
    );

    const result = await cancelJob("job-1");

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/jobs/job-1/cancel");
    expect(init?.method).toBe("POST");
    expect(result.cancelled).toBe(true);
    expect(result.job.status).toBe("cancelled");
  });

  it("downloadJobResult returns Blob on 200", async () => {
    const mockFetch = vi.mocked(fetch);
    const pdfBlob = new Blob(["pdf"], { type: "application/pdf" });
    mockFetch.mockResolvedValueOnce(mockBlobResponse(pdfBlob));

    const result = await downloadJobResult("job-1");

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/jobs/job-1/download");
    expect(result).toBe(pdfBlob);
  });

  it("downloadJobResult throws on 409 with backend message", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({ detail: "Download not available for this job" }, 409),
    );

    await expect(downloadJobResult("job-1")).rejects.toThrow("Download not available for this job");
  });

  it("createCatalogPdfExportJob calls correct endpoint and parses JobOut", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(mockJsonResponse(sampleJob, 202));

    const result = await createCatalogPdfExportJob("cat-1");

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/catalogs/cat-1/exports/pdf/jobs");
    expect(init?.method).toBe("POST");
    expect(result.job_type).toBe("catalog_export_pdf");
    expect(result.status).toBe("queued");
  });

  it("createCatalogPdfExportJob throws on 409 duplicate active export", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(
      mockJsonResponse({ detail: "Ya hay una exportacion PDF en curso para este catalogo" }, 409),
    );

    await expect(createCatalogPdfExportJob("cat-1")).rejects.toThrow(
      "Ya hay una exportacion PDF en curso para este catalogo",
    );
  });

  it("JobOut type compiles with metadata object", () => {
    const job: JobOut = {
      ...sampleJob,
      metadata: { catalog_name: "Test", page_count: 12 },
    };
    expect(job.metadata.page_count).toBe(12);
  });
});
