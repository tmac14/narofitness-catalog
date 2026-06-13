import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  HTML_FALLBACK_SHOW_LABEL,
  PREVIEW_PDF_ERROR_PAGINATION_HINT,
  PREVIEW_PDF_ERROR_RETRY_LABEL,
  PREVIEW_PDF_ERROR_TITLE,
  getPreviewPdfErrorBody,
} from "@/lib/catalogPreviewCopy";
import type { PreviewPdfErrorDetail } from "@/lib/paginatedPreviewLoader";
import { ApproximateHtmlPreview } from "./ApproximateHtmlPreview";

type Props = {
  catalogId: string;
  previewKey: number;
  errorDetail?: PreviewPdfErrorDetail | null;
  onRetry: () => void;
};

export function PreviewPdfDegradedPanel({ catalogId, previewKey, errorDetail, onRetry }: Props) {
  const [showHtmlFallback, setShowHtmlFallback] = useState(false);
  const kind = errorDetail?.kind ?? "fetch_failed";

  function handleRetry() {
    setShowHtmlFallback(false);
    onRetry();
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <p className="text-sm font-medium">{PREVIEW_PDF_ERROR_TITLE}</p>
        <p className="max-w-md text-xs text-muted-foreground">{getPreviewPdfErrorBody(kind)}</p>
        <p className="max-w-md text-xs font-medium text-muted-foreground">
          {PREVIEW_PDF_ERROR_PAGINATION_HINT}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2">
          <Button type="button" variant="secondary" size="sm" onClick={handleRetry}>
            {PREVIEW_PDF_ERROR_RETRY_LABEL}
          </Button>
          {!showHtmlFallback && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowHtmlFallback(true)}
            >
              {HTML_FALLBACK_SHOW_LABEL}
            </Button>
          )}
        </div>
      </div>
      {showHtmlFallback && <ApproximateHtmlPreview catalogId={catalogId} previewKey={previewKey} />}
    </div>
  );
}
