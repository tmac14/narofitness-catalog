import type { PreviewPdfFailureKind } from "./paginatedPreviewLoader";

export const PREVIEW_STALE_BANNER =
  "La vista previa PDF está desactualizada. Regenera la vista previa para ver la paginación final.";

export const PREVIEW_STALE_FOLLOWUP = "Los cambios se reflejarán al regenerar la vista previa PDF.";

export function getPreviewStaleBannerText(): string {
  return `${PREVIEW_STALE_BANNER} ${PREVIEW_STALE_FOLLOWUP}`;
}

export const PREVIEW_PDF_ERROR_TITLE = "No se pudo generar la vista previa PDF.";

export const PREVIEW_PDF_ERROR_PAGINATION_HINT = "La paginación exacta requiere el motor PDF.";

export const PREVIEW_PDF_ERROR_RETRY_LABEL = "Reintentar";

export const HTML_FALLBACK_TITLE = "Vista aproximada HTML";

export const HTML_FALLBACK_WARNING = "La paginación puede no coincidir con el PDF exportado.";

export const HTML_FALLBACK_SHOW_LABEL = "Ver vista aproximada HTML";

export const EXPORT_PREFLIGHT_STALE_TITLE = "Vista previa PDF desactualizada";

export const EXPORT_PREFLIGHT_STALE_BODY =
  "Regenera la vista previa PDF para revisar la paginación final, o exporta con la configuración actual del servidor.";

export const EXPORT_PREFLIGHT_STALE_DETAIL =
  "La vista previa PDF puede no reflejar los últimos cambios guardados.";

export function getPreviewPdfErrorBody(kind: PreviewPdfFailureKind): string {
  switch (kind) {
    case "engine_unavailable":
      return "El motor PDF no está disponible en este momento. Comprueba que el servicio de generación PDF está en marcha.";
    case "pdfjs_load_failed":
      return "El PDF se recibió pero no se pudo abrir en el visor. Inténtalo de nuevo.";
    case "fetch_failed":
    default:
      return "Comprueba que la API está en marcha e inténtalo de nuevo.";
  }
}

export function previewCopyMentionsPdf(text: string): boolean {
  return text.toLowerCase().includes("pdf");
}

/** HTML fallback must never show paginated page controls or total page count. */
export const HTML_FALLBACK_SHOWS_PAGE_COUNT = false;
