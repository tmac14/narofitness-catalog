import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy } from "pdfjs-dist";
import {
  PREVIEW_PDF_PAGE_CANVAS_WRAPPER_CLASS,
  PREVIEW_PDF_PAGE_SURFACE_CLASS,
  PREVIEW_PDF_PAGE_VIEWPORT_CLASS,
  PREVIEW_PDF_PAGE_VIEWPORT_PADDING_PX,
  PREVIEW_PDF_VIEWPORT_MIN_HEIGHT_PX,
  computePdfPageFitScale,
} from "@/lib/previewPageNav";

type Props = {
  pdf: PDFDocumentProxy | null;
  pageNumber: number;
  ariaLabel: string;
};

const COLLAPSED_VIEWPORT_HEIGHT_PX = 48;

function measureViewportSize(el: HTMLElement): { width: number; height: number } {
  const width = Math.max(el.clientWidth, 1);
  const measuredHeight = el.clientHeight;
  const height =
    measuredHeight < COLLAPSED_VIEWPORT_HEIGHT_PX
      ? PREVIEW_PDF_VIEWPORT_MIN_HEIGHT_PX
      : Math.max(measuredHeight, 1);
  return { width, height };
}

export function PdfPageCanvas({ pdf, pageNumber, ariaLabel }: Props) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [rendering, setRendering] = useState(false);

  useEffect(() => {
    const viewportEl = viewportRef.current;
    const canvasEl = canvasRef.current;
    if (!pdf || !viewportEl || !canvasEl || pageNumber < 1) return;
    const pdfDoc = pdf;
    const viewportElement = viewportEl;
    const canvasElement = canvasEl;

    let cancelled = false;
    let renderGeneration = 0;
    let activeRender: { cancel: () => void; promise: Promise<void> } | null = null;

    async function renderPage() {
      const generation = ++renderGeneration;
      activeRender?.cancel();
      setRendering(true);

      try {
        const page = await pdfDoc.getPage(pageNumber);
        if (cancelled || generation !== renderGeneration) {
          page.cleanup();
          return;
        }

        const baseViewport = page.getViewport({ scale: 1 });
        const { width: containerWidth, height: containerHeight } =
          measureViewportSize(viewportElement);
        const scale = computePdfPageFitScale(
          baseViewport.width,
          baseViewport.height,
          containerWidth,
          containerHeight,
          PREVIEW_PDF_PAGE_VIEWPORT_PADDING_PX,
        );
        const viewport = page.getViewport({ scale });

        const context = canvasElement.getContext("2d");
        if (!context) {
          page.cleanup();
          return;
        }

        const cssWidth = Math.floor(viewport.width);
        const cssHeight = Math.floor(viewport.height);
        canvasElement.width = cssWidth;
        canvasElement.height = cssHeight;
        canvasElement.style.width = `${cssWidth}px`;
        canvasElement.style.height = `${cssHeight}px`;

        const task = page.render({ canvasContext: context, viewport });
        activeRender = task;
        await task.promise;
        if (!cancelled && generation === renderGeneration) page.cleanup();
      } catch {
        // Parent handles fetch/load errors; per-page render failures keep the last frame.
      } finally {
        if (!cancelled && generation === renderGeneration) setRendering(false);
      }
    }

    void renderPage();

    const observer = new ResizeObserver(() => {
      void renderPage();
    });
    observer.observe(viewportEl);

    return () => {
      cancelled = true;
      observer.disconnect();
      activeRender?.cancel();
    };
  }, [pdf, pageNumber]);

  return (
    <div className={PREVIEW_PDF_PAGE_CANVAS_WRAPPER_CLASS}>
      <div ref={viewportRef} className={PREVIEW_PDF_PAGE_VIEWPORT_CLASS}>
        <canvas
          ref={canvasRef}
          className={PREVIEW_PDF_PAGE_SURFACE_CLASS}
          aria-label={ariaLabel}
          role="img"
        />
        {rendering && (
          <span className="sr-only" aria-live="polite">
            Renderizando página {pageNumber}
          </span>
        )}
      </div>
    </div>
  );
}
