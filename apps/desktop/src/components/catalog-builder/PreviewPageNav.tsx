import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { canGoToNextPage, canGoToPreviousPage, parsePreviewPageInput } from "@/lib/previewPageNav";

type Props = {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
};

export function PreviewPageNav({ currentPage, totalPages, onPageChange }: Props) {
  const [pageDraft, setPageDraft] = useState(String(currentPage));
  const prevDisabled = !canGoToPreviousPage(currentPage);
  const nextDisabled = !canGoToNextPage(currentPage, totalPages);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setPageDraft(String(currentPage));
    });
    return () => cancelAnimationFrame(frame);
  }, [currentPage]);

  function commitInput(raw: string) {
    const next = parsePreviewPageInput(raw, currentPage, totalPages);
    onPageChange(next);
    setPageDraft(String(next));
  }

  return (
    <nav
      className="preview-page-nav flex shrink-0 flex-wrap items-center justify-center gap-2 border-b border-border bg-muted/10 px-4 py-2"
      aria-label="Navegación de páginas del catálogo"
    >
      <Button
        type="button"
        variant="secondary"
        size="sm"
        disabled={prevDisabled}
        onClick={() => onPageChange(currentPage - 1)}
        aria-label="Página anterior"
      >
        <ChevronLeft className="h-4 w-4" />
        Anterior
      </Button>

      <div className="flex items-center gap-1.5 text-sm">
        <span>Página</span>
        <Input
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          value={pageDraft}
          className="h-8 w-16 text-center tabular-nums"
          aria-label="Ir a página"
          onChange={(e) => {
            const next = e.target.value.replace(/\D/g, "");
            setPageDraft(next);
            if (next) {
              onPageChange(parsePreviewPageInput(next, currentPage, totalPages));
            }
          }}
          onBlur={(e) => commitInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.currentTarget.blur();
            }
          }}
        />
        <span>
          de <span className="font-medium tabular-nums">{totalPages}</span>
        </span>
      </div>

      <Button
        type="button"
        variant="secondary"
        size="sm"
        disabled={nextDisabled}
        onClick={() => onPageChange(currentPage + 1)}
        aria-label="Página siguiente"
      >
        Siguiente
        <ChevronRight className="h-4 w-4" />
      </Button>

      <p className="sr-only" aria-live="polite" aria-atomic="true">
        Página {currentPage} de {totalPages}
      </p>
    </nav>
  );
}
