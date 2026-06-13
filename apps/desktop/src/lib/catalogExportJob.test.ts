import { describe, expect, it, vi } from "vitest";
import { buildExportPreflight, exportPreflightBlocksExport } from "./catalogLayout";
import { getUnsavedExportBlockFromFreshness } from "./catalogPreviewFreshness";
import {
  CATALOG_PDF_EXPORT_PREPARING_LABEL,
  CATALOG_PDF_EXPORT_QUEUED_DESCRIPTION,
  CATALOG_PDF_EXPORT_QUEUED_TOAST,
  isDuplicatePdfExportError,
  queueCatalogPdfExportJob,
} from "./catalogExportJob";

describe("catalogExportJob", () => {
  it("queueCatalogPdfExportJob calls createJob instead of sync export", async () => {
    const createJob = vi.fn().mockResolvedValue({ id: "job-42" });
    const exportCatalogPdf = vi.fn();

    const result = await queueCatalogPdfExportJob("cat-1", { createJob });

    expect(createJob).toHaveBeenCalledWith("cat-1");
    expect(exportCatalogPdf).not.toHaveBeenCalled();
    expect(result).toEqual({ ok: true, jobId: "job-42" });
  });

  it("queueCatalogPdfExportJob does not return blob bytes for download", async () => {
    const createJob = vi.fn().mockResolvedValue({ id: "job-42" });

    const result = await queueCatalogPdfExportJob("cat-1", { createJob });

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result).not.toHaveProperty("blob");
      expect(result.jobId).toBe("job-42");
    }
  });

  it("success copy mentions queued/background export", () => {
    expect(CATALOG_PDF_EXPORT_QUEUED_TOAST).toMatch(/cola/i);
    expect(CATALOG_PDF_EXPORT_QUEUED_DESCRIPTION).toMatch(/segundo plano/i);
    expect(CATALOG_PDF_EXPORT_QUEUED_DESCRIPTION).toMatch(/Centro de procesos/i);
  });

  it("duplicate 409 error is detected and surfaced", async () => {
    const message = "Ya hay una exportacion PDF en curso para este catalogo";
    const createJob = vi.fn().mockRejectedValue(new Error(message));

    const result = await queueCatalogPdfExportJob("cat-1", { createJob });

    expect(result).toEqual({ ok: false, duplicate: true, message });
    expect(isDuplicatePdfExportError(message)).toBe(true);
  });

  it("non-duplicate errors are surfaced without duplicate flag", async () => {
    const createJob = vi.fn().mockRejectedValue(new Error("Servidor no disponible"));

    const result = await queueCatalogPdfExportJob("cat-1", { createJob });

    expect(result).toEqual({ ok: false, duplicate: false, message: "Servidor no disponible" });
  });

  it("preparing label covers only create-job request window", () => {
    expect(CATALOG_PDF_EXPORT_PREPARING_LABEL).toMatch(/Preparando exportación/i);
    expect(CATALOG_PDF_EXPORT_PREPARING_LABEL).not.toMatch(/Generando PDF/i);
  });

  it("preflight and unsaved freshness gates remain independent of async queue", () => {
    expect(
      getUnsavedExportBlockFromFreshness({
        previewStale: false,
        pendingPresentation: true,
        orderDirty: false,
      }),
    ).toBe("presentation");

    const preflight = buildExportPreflight(
      {
        summary: {
          total_products: 1,
          manual_overrides: 0,
          fallback_count: 0,
          warning_count: 0,
          diagnostics_count: 1,
          diagnostics_by_severity: { critical: 1, warning: 0, info: 0 },
          by_layout: {},
          by_section: {},
        },
        diagnostics: [
          {
            type: "fallback",
            severity: "critical",
            master_id: "m1",
            master_name: "Demo",
            message: "Layout fallback",
          },
        ],
      },
      { previewStale: false, pendingPreview: false },
    );

    expect(exportPreflightBlocksExport(preflight, false)).toBe(true);
    expect(preflight.safeToExport).toBe(false);
  });
});
