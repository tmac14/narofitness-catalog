import { describe, expect, it } from "vitest";
import type { JobOut } from "./api";
import {
  applyActiveJobsPoll,
  buildJobRowViewModel,
  centerStatusLabel,
  fetchActiveJobsSafely,
  jobStatusLabel,
  jobTitle,
  jobsPollIntervalMs,
  shouldShowRecentTerminal,
} from "./jobLabels";

function makeJob(overrides: Partial<JobOut> = {}): JobOut {
  return {
    id: "job-1",
    job_type: "catalog_export_pdf",
    status: "queued",
    progress_percent: null,
    message: null,
    error_message: null,
    catalog_id: "cat-1",
    catalog_name: "FDL Tarifa 2026",
    created_at: "2026-06-07T12:00:00Z",
    started_at: null,
    finished_at: null,
    download_available: false,
    can_cancel: true,
    metadata: {},
    ...overrides,
  };
}

describe("centerStatusLabel", () => {
  it("returns idle label when there are no jobs", () => {
    expect(centerStatusLabel([], null)).toBe("Sin tareas activas");
  });

  it("shows export progress for a single running PDF job", () => {
    const job = makeJob({ status: "running", progress_percent: 43 });
    expect(centerStatusLabel([job], null)).toBe("Exportando PDF… 43%");
  });

  it("shows single active job count for non-export running jobs", () => {
    const job = makeJob({ job_type: "other_job", status: "running" });
    expect(centerStatusLabel([job], null)).toBe("1 proceso en curso");
  });

  it("shows multiple active jobs count", () => {
    const jobs = [
      makeJob({ id: "job-1", status: "queued" }),
      makeJob({ id: "job-2", status: "running" }),
    ];
    expect(centerStatusLabel(jobs, null)).toBe("2 procesos en curso");
  });

  it("shows failed recent terminal label", () => {
    const failed = makeJob({ status: "failed" });
    expect(centerStatusLabel([], failed)).toBe("Error en exportación");
  });

  it("shows succeeded recent terminal label", () => {
    const succeeded = makeJob({ status: "succeeded" });
    expect(centerStatusLabel([], succeeded)).toBe("Exportación completada");
  });
});

describe("job row view model", () => {
  it("builds export title from catalog name", () => {
    expect(jobTitle(makeJob())).toBe("Exportar PDF — FDL Tarifa 2026");
    expect(jobStatusLabel("queued")).toBe("En cola");
  });

  it("includes progress value for accessible progress bar", () => {
    const vm = buildJobRowViewModel(makeJob({ status: "running", progress_percent: 67 }));
    expect(vm.progressPercent).toBe(67);
    expect(vm.progressAria).toContain("67");
    expect(vm.canCancel).toBe(true);
  });

  it("exposes download when available", () => {
    const vm = buildJobRowViewModel(
      makeJob({ status: "succeeded", download_available: true, can_cancel: false }),
    );
    expect(vm.downloadAvailable).toBe(true);
    expect(vm.statusLabel).toBe("Completado");
  });
});

describe("jobs polling helpers", () => {
  it("uses faster polling while jobs are active", () => {
    expect(jobsPollIntervalMs(2, false)).toBe(2000);
    expect(jobsPollIntervalMs(0, true)).toBe(10000);
    expect(jobsPollIntervalMs(0, false)).toBe(15000);
  });

  it("tracks disappeared active job ids", () => {
    const previous = new Set(["job-1", "job-2"]);
    const current = [makeJob({ id: "job-2", status: "running" })];
    const result = applyActiveJobsPoll(previous, current);
    expect(result.disappearedIds).toEqual(["job-1"]);
    expect(result.nextActiveIds).toEqual(new Set(["job-2"]));
  });

  it("does not crash when active jobs poll fails", async () => {
    const result = await fetchActiveJobsSafely(() => Promise.reject(new Error("network")));
    expect(result).toEqual({ items: null, error: true });
  });

  it("expires recent terminal highlight after ttl", () => {
    const job = makeJob({ status: "succeeded" });
    const now = 1_000_000;
    expect(shouldShowRecentTerminal(job, now - 5_000, now)).toBe(true);
    expect(shouldShowRecentTerminal(job, now - 20_000, now)).toBe(false);
  });
});
