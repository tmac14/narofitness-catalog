import {
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  X,
  FileDown,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CATALOG_PDF_EXPORT_PREPARING_LABEL } from "@/lib/catalogExportJob";
import { getPreviewStaleBannerText } from "@/lib/catalogPreviewCopy";
import type { PreviewPdfErrorDetail } from "@/lib/paginatedPreviewLoader";
import {
  previewStatusLabel,
  shouldShowPreviewErrorPanel,
  type PreviewState,
} from "@/lib/previewState";
import { PaginatedPreviewWorkspace } from "./PaginatedPreviewWorkspace";
import { PreviewPdfDegradedPanel } from "./PreviewPdfDegradedPanel";

export type { PreviewState };

type Props = {
  catalogId: string;
  previewKey: number;
  previewState: PreviewState;
  exportWarnings?: number;
  pendingPreview?: boolean;
  exportingPdf?: boolean;
  onRefresh: () => void;
  previewErrorDetail?: PreviewPdfErrorDetail | null;
  onLoad: () => void;
  onError: (detail: PreviewPdfErrorDetail) => void;
  onClose: () => void;
  onExportPdf: () => void;
  onExportWarningsClick?: () => void;
};

export function PreviewWorkspace({
  catalogId,
  previewKey,
  previewState,
  exportWarnings = 0,
  pendingPreview = false,
  exportingPdf = false,
  previewErrorDetail = null,
  onRefresh,
  onLoad,
  onError,
  onClose,
  onExportPdf,
  onExportWarningsClick,
}: Props) {
  const statusVariant = (() => {
    switch (previewState) {
      case "ready":
        return "success" as const;
      case "stale":
        return "warning" as const;
      case "error":
        return "destructive" as const;
      case "loading":
        return "secondary" as const;
      default:
        return "secondary" as const;
    }
  })();

  const StatusIcon =
    previewState === "ready"
      ? CheckCircle2
      : previewState === "error"
        ? AlertCircle
        : previewState === "loading"
          ? Loader2
          : AlertCircle;

  return (
    <div className="preview-workspace flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <div className="preview-workspace-toolbar flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/20 px-4 py-3 min-h-[3.25rem]">
        <div className="flex min-w-0 flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-center sm:gap-2">
          <div>
            <h2 className="text-sm font-semibold">Vista previa del catálogo</h2>
            <p className="text-xs text-muted-foreground">
              Revisa el catálogo antes de exportar el PDF
            </p>
          </div>
          <Badge
            variant={statusVariant}
            className="gap-1 min-w-[7rem] justify-center self-start sm:self-center"
          >
            <StatusIcon className={cnIconSpin(previewState)} />
            {previewStatusLabel(previewState)}
          </Badge>
          {pendingPreview && previewState !== "loading" && (
            <Badge variant="warning">Cambios pendientes</Badge>
          )}
          {exportWarnings > 0 && onExportWarningsClick && (
            <button
              type="button"
              className="inline-flex"
              onClick={onExportWarningsClick}
              aria-label={`${exportWarnings} avisos en exportación`}
            >
              <Badge variant="warning">{exportWarnings} avisos exportación</Badge>
            </button>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={previewState === "loading"}
            onClick={onRefresh}
          >
            <RefreshCw className={cnIconSpin(previewState === "loading" ? "loading" : "ready")} />
            Regenerar vista previa PDF
          </Button>
          <Button type="button" size="sm" disabled={exportingPdf} onClick={onExportPdf}>
            <FileDown className="h-4 w-4" />
            {exportingPdf ? CATALOG_PDF_EXPORT_PREPARING_LABEL : "Exportar PDF"}
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
            Salir de vista previa
          </Button>
        </div>
      </div>

      <div className="preview-workspace-body relative flex min-h-0 flex-1 flex-col">
        {previewState === "stale" && !shouldShowPreviewErrorPanel(previewState) && (
          <div className="flex shrink-0 items-center gap-2 border-b border-warning/30 bg-warning/10 px-4 py-2 text-sm text-warning">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{getPreviewStaleBannerText()}</span>
          </div>
        )}
        {previewState === "loading" && !exportingPdf && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 bg-background/70">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Generando vista previa PDF…</p>
          </div>
        )}
        {shouldShowPreviewErrorPanel(previewState) ? (
          <PreviewPdfDegradedPanel
            catalogId={catalogId}
            previewKey={previewKey}
            errorDetail={previewErrorDetail}
            onRetry={onRefresh}
          />
        ) : (
          <PaginatedPreviewWorkspace
            catalogId={catalogId}
            previewKey={previewKey}
            onLoad={onLoad}
            onError={onError}
          />
        )}
      </div>
    </div>
  );
}

function cnIconSpin(state: PreviewState | "loading" | "ready"): string {
  const base = "h-3 w-3";
  if (state === "loading") return `${base} animate-spin`;
  return base;
}
