import { useEffect, useRef, useState } from "react";
import { getDocument, type PDFDocumentProxy } from "pdfjs-dist";
import { ensurePdfJsWorker } from "@/lib/pdfjsSetup";
import {
  PREVIEW_PDF_CANVAS_SHELL_CLASS,
  PREVIEW_PDF_WORKSPACE_CLASS,
  PreviewPdfLoadError,
  fetchPreviewPdfForViewer,
  isPreviewFetchAbortError,
  toPreviewPdfErrorDetail,
  type PreviewPdfErrorDetail,
} from "@/lib/paginatedPreviewLoader";
import { clampPreviewPage } from "@/lib/previewPageNav";
import { PdfPageCanvas } from "./PdfPageCanvas";
import { PreviewPageNav } from "./PreviewPageNav";

type Props = {
  catalogId: string;
  previewKey: number;
  onLoad: () => void;
  onError: (detail: PreviewPdfErrorDetail) => void;
};

export function PaginatedPreviewWorkspace({ catalogId, previewKey, onLoad, onError }: Props) {
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [pdfEngine, setPdfEngine] = useState<string | null>(null);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const [fetching, setFetching] = useState(true);
  const loadGenerationRef = useRef(0);
  const onLoadRef = useRef(onLoad);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onLoadRef.current = onLoad;
  }, [onLoad]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    ensurePdfJsWorker();
    let cancelled = false;
    let blobUrl: string | null = null;
    let pdfDoc: PDFDocumentProxy | null = null;
    const abortController = new AbortController();
    const generation = ++loadGenerationRef.current;

    async function load() {
      setFetching(true);
      setPdf(null);
      setCurrentPage(1);
      setPdfEngine(null);
      setGeneratedAt(null);

      try {
        const result = await fetchPreviewPdfForViewer({
          catalogId,
          previewKey,
          signal: abortController.signal,
        });
        if (cancelled || generation !== loadGenerationRef.current) return;

        blobUrl = URL.createObjectURL(result.blob);
        const loadingTask = getDocument({ url: blobUrl });
        try {
          pdfDoc = await loadingTask.promise;
        } catch (pdfjsErr) {
          throw new PreviewPdfLoadError("pdfjs_load_failed", undefined, { cause: pdfjsErr });
        }
        if (cancelled || generation !== loadGenerationRef.current) {
          void pdfDoc.destroy();
          return;
        }

        const pageCount = Math.max(pdfDoc.numPages, result.totalPages, 1);
        setTotalPages(pageCount);
        setPdfEngine(result.pdfEngine);
        setGeneratedAt(result.generatedAt);
        setPdf(pdfDoc);
        setCurrentPage(1);
        setFetching(false);
        onLoadRef.current();
      } catch (err) {
        if (cancelled || generation !== loadGenerationRef.current) return;
        if (isPreviewFetchAbortError(err)) return;
        setFetching(false);
        onErrorRef.current(toPreviewPdfErrorDetail(err));
      }
    }

    void load();

    return () => {
      cancelled = true;
      abortController.abort();
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      if (pdfDoc) void pdfDoc.destroy();
    };
  }, [catalogId, previewKey]);

  function handlePageChange(page: number) {
    setCurrentPage(clampPreviewPage(page, totalPages));
  }

  const showNav = pdf != null && totalPages > 0 && !fetching;

  return (
    <div className={PREVIEW_PDF_WORKSPACE_CLASS}>
      {showNav && (
        <PreviewPageNav
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
      <div
        className={PREVIEW_PDF_CANVAS_SHELL_CLASS}
        style={{ backgroundColor: "var(--preview-canvas, #2a2a2a)" }}
      >
        {fetching ? (
          <p className="sr-only" aria-live="polite">
            Generando vista previa PDF…
          </p>
        ) : (
          <PdfPageCanvas
            pdf={pdf}
            pageNumber={currentPage}
            ariaLabel={`Página ${currentPage} de ${totalPages} del catálogo`}
          />
        )}
      </div>
      {showNav && (pdfEngine || generatedAt || totalPages > 0) && (
        <div className="shrink-0 border-t border-border px-4 py-1 text-xs text-muted-foreground">
          {totalPages > 0 && <span>{totalPages} páginas</span>}
          {pdfEngine && <span className={totalPages > 0 ? "ml-3" : ""}>Motor: {pdfEngine}</span>}
          {generatedAt && <span className="ml-3">Generado: {generatedAt}</span>}
        </div>
      )}
    </div>
  );
}
