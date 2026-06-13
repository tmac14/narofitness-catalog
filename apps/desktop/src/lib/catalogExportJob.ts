/** Async catalogue PDF export — queue background job (PRES-5C.3). */

export const CATALOG_PDF_EXPORT_QUEUED_TOAST = "Exportación PDF en cola";

export const CATALOG_PDF_EXPORT_QUEUED_DESCRIPTION =
  "La exportación se está generando en segundo plano. Puedes seguir el progreso en el Centro de procesos.";

export const CATALOG_PDF_EXPORT_PREPARING_LABEL = "Preparando exportación…";

export const CATALOG_PDF_EXPORT_BACKGROUND_NOTE =
  "La exportación se ejecutará en segundo plano. Sigue el progreso en el Centro de procesos y descarga el PDF cuando finalice.";

export function isDuplicatePdfExportError(message: string): boolean {
  return /exportaci[oó]n pdf en curso/i.test(message);
}

export type QueueCatalogPdfExportDeps = {
  createJob: (catalogId: string) => Promise<{ id: string }>;
};

export type QueueCatalogPdfExportResult =
  | { ok: true; jobId: string }
  | { ok: false; duplicate: boolean; message: string };

export async function queueCatalogPdfExportJob(
  catalogId: string,
  deps: QueueCatalogPdfExportDeps,
): Promise<QueueCatalogPdfExportResult> {
  try {
    const job = await deps.createJob(catalogId);
    return { ok: true, jobId: job.id };
  } catch (e) {
    const message = e instanceof Error ? e.message : "Error al encolar exportación PDF";
    return { ok: false, duplicate: isDuplicatePdfExportError(message), message };
  }
}
