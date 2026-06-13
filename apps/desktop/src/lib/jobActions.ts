import type { JobOut } from "@/lib/api";

export function resolveJobDownloadFilename(job: JobOut): string {
  const fileName = job.metadata.file_name;
  if (typeof fileName === "string" && fileName.trim()) {
    return fileName.trim();
  }
  if (job.catalog_name) {
    const safe = job.catalog_name.replace(/[<>:"/\\|?*]+/g, "_").trim();
    if (safe) return `${safe}.pdf`;
  }
  return `catalog_export_${job.id}.pdf`;
}

export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export async function executeJobCancel(
  jobId: string,
  cancelFn: (id: string) => Promise<unknown>,
): Promise<{ ok: true } | { ok: false; message: string }> {
  try {
    await cancelFn(jobId);
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof Error ? error.message : "No se pudo cancelar la tarea",
    };
  }
}

export async function executeJobDownload(
  job: JobOut,
  downloadFn: (id: string) => Promise<Blob>,
): Promise<{ ok: true; filename: string } | { ok: false; message: string }> {
  try {
    const blob = await downloadFn(job.id);
    const filename = resolveJobDownloadFilename(job);
    triggerBlobDownload(blob, filename);
    return { ok: true, filename };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof Error ? error.message : "No se pudo descargar el archivo",
    };
  }
}
