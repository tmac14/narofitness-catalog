import { fetchCatalogPreviewPdf, type CatalogPreviewPdfResult } from "./api";

export type PreviewPdfFailureKind = "engine_unavailable" | "fetch_failed" | "pdfjs_load_failed";

export type PreviewPdfErrorDetail = {
  kind: PreviewPdfFailureKind;
  message?: string;
};

export class PreviewPdfLoadError extends Error {
  readonly kind: PreviewPdfFailureKind;

  constructor(kind: PreviewPdfFailureKind, message?: string, options?: { cause?: unknown }) {
    super(message ?? kind);
    this.name = "PreviewPdfLoadError";
    this.kind = kind;
    if (options?.cause !== undefined) {
      this.cause = options.cause;
    }
  }
}

export function classifyPreviewPdfFailure(error: unknown): PreviewPdfFailureKind {
  if (error instanceof PreviewPdfLoadError) return error.kind;
  if (error instanceof Error) {
    const msg = error.message.toLowerCase();
    if (msg.includes("motor pdf no disponible") || msg.includes("503")) {
      return "engine_unavailable";
    }
  }
  return "fetch_failed";
}

export function toPreviewPdfErrorDetail(error: unknown): PreviewPdfErrorDetail {
  const kind = classifyPreviewPdfFailure(error);
  return {
    kind,
    message: error instanceof Error ? error.message : undefined,
  };
}

export type PreviewPdfFetchParams = {
  catalogId: string;
  previewKey: number;
  signal?: AbortSignal;
};

export type PreviewPdfFetchOptions = {
  signal?: AbortSignal;
};

export type PreviewPdfFetchFn = (
  catalogId: string,
  cacheBust?: string | number,
  options?: PreviewPdfFetchOptions,
) => Promise<CatalogPreviewPdfResult>;

export function isPreviewFetchAbortError(error: unknown): boolean {
  return (
    (error instanceof DOMException && error.name === "AbortError") ||
    (error instanceof Error && error.name === "AbortError")
  );
}

/** Fetch catalog preview PDF bytes for the paginated viewer. */
export async function fetchPreviewPdfForViewer(
  params: PreviewPdfFetchParams,
  fetchFn: PreviewPdfFetchFn = fetchCatalogPreviewPdf,
): Promise<CatalogPreviewPdfResult> {
  return fetchFn(params.catalogId, params.previewKey, { signal: params.signal });
}

export function shouldRefetchPreviewPdf(prevKey: number | null, nextKey: number): boolean {
  return prevKey !== nextKey;
}

export const PREVIEW_PDF_CANVAS_SHELL_CLASS =
  "preview-pdf-canvas-shell relative min-h-0 flex-1 overflow-hidden";

export const PREVIEW_PDF_WORKSPACE_CLASS =
  "preview-pdf-workspace flex min-h-0 flex-1 flex-col overflow-hidden";

export type PreviewPdfLoadStatus = "loading" | "ready" | "error";

export function derivePreviewPdfLoadStatus(input: {
  fetching: boolean;
  failed: boolean;
}): PreviewPdfLoadStatus {
  if (input.failed) return "error";
  if (input.fetching) return "loading";
  return "ready";
}
