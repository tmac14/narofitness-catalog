import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { JobOut } from "./api";
import {
  executeJobCancel,
  executeJobDownload,
  resolveJobDownloadFilename,
  triggerBlobDownload,
} from "./jobActions";

const sampleJob: JobOut = {
  id: "job-1",
  job_type: "catalog_export_pdf",
  status: "succeeded",
  progress_percent: 100,
  message: null,
  error_message: null,
  catalog_id: "cat-1",
  catalog_name: "FDL Tarifa 2026",
  created_at: "2026-06-07T12:00:00Z",
  started_at: "2026-06-07T12:01:00Z",
  finished_at: "2026-06-07T12:02:00Z",
  download_available: true,
  can_cancel: false,
  metadata: { file_name: "fdl-tarifa-2026.pdf" },
};

function stubDocumentDownload() {
  const click = vi.fn();
  const remove = vi.fn();
  const anchor = {
    click,
    remove,
    href: "",
    download: "",
    rel: "",
    style: { display: "" },
  };
  const doc = {
    createElement: vi.fn(() => anchor),
    body: { appendChild: vi.fn(() => anchor) },
  };
  vi.stubGlobal("document", doc);
  return { anchor, click, remove, createElement: doc.createElement };
}

describe("jobActions", () => {
  beforeEach(() => {
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:mock"),
      revokeObjectURL: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("resolves download filename from metadata or catalog name", () => {
    expect(resolveJobDownloadFilename(sampleJob)).toBe("fdl-tarifa-2026.pdf");
    expect(
      resolveJobDownloadFilename({
        ...sampleJob,
        metadata: {},
        catalog_name: "Catálogo/A",
      }),
    ).toBe("Catálogo_A.pdf");
  });

  it("cancelJob helper calls injected cancel function", async () => {
    const cancelFn = vi.fn().mockResolvedValue({ cancelled: true });
    const result = await executeJobCancel("job-1", cancelFn);
    expect(cancelFn).toHaveBeenCalledWith("job-1");
    expect(result).toEqual({ ok: true });
  });

  it("cancelJob helper returns error message on failure", async () => {
    const cancelFn = vi.fn().mockRejectedValue(new Error("Job is already succeeded"));
    const result = await executeJobCancel("job-1", cancelFn);
    expect(result).toEqual({ ok: false, message: "Job is already succeeded" });
  });

  it("downloadJobResult helper downloads blob with resolved filename", async () => {
    const { anchor, click, createElement } = stubDocumentDownload();
    const blob = new Blob(["pdf"], { type: "application/pdf" });
    const downloadFn = vi.fn().mockResolvedValue(blob);

    const result = await executeJobDownload(sampleJob, downloadFn);

    expect(downloadFn).toHaveBeenCalledWith("job-1");
    expect(createElement).toHaveBeenCalledWith("a");
    expect(anchor.download).toBe("fdl-tarifa-2026.pdf");
    expect(click).toHaveBeenCalled();
    expect(result).toEqual({ ok: true, filename: "fdl-tarifa-2026.pdf" });
  });

  it("downloadJobResult helper returns error when download fails", async () => {
    const downloadFn = vi.fn().mockRejectedValue(new Error("Download not available"));
    const result = await executeJobDownload(sampleJob, downloadFn);
    expect(result).toEqual({ ok: false, message: "Download not available" });
  });

  it("triggerBlobDownload creates and clicks anchor", () => {
    const { anchor, click, remove } = stubDocumentDownload();

    triggerBlobDownload(new Blob(["x"]), "test.pdf");

    expect(anchor.download).toBe("test.pdf");
    expect(click).toHaveBeenCalled();
    expect(remove).toHaveBeenCalled();
  });
});
