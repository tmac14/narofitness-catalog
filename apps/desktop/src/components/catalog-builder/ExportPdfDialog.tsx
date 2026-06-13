import { useState } from "react";
import { AlertCircle, AlertTriangle, Info, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  CATALOG_PDF_EXPORT_BACKGROUND_NOTE,
  CATALOG_PDF_EXPORT_PREPARING_LABEL,
} from "@/lib/catalogExportJob";
import {
  EXPORT_PREFLIGHT_STALE_BODY,
  EXPORT_PREFLIGHT_STALE_TITLE,
} from "@/lib/catalogPreviewCopy";
import {
  diagnosticTypeLabel,
  exportPreflightBlocksExport,
  type DiagnosticSeverity,
  type ExportPreflight,
  type LayoutDiagnostic,
} from "@/lib/catalogLayout";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  catalogName: string;
  preflight: ExportPreflight;
  isExporting: boolean;
  onExport: () => void;
  onRefreshPreview: () => void;
};

const SEVERITY_META: Record<
  DiagnosticSeverity,
  { label: string; variant: "destructive" | "warning" | "secondary"; icon: typeof Info }
> = {
  critical: { label: "Crítico", variant: "destructive", icon: AlertCircle },
  warning: { label: "Advertencia", variant: "warning", icon: AlertTriangle },
  info: { label: "Informativo", variant: "secondary", icon: Info },
};

export function ExportPdfDialog({
  open,
  onOpenChange,
  catalogName,
  preflight,
  isExporting,
  onExport,
  onRefreshPreview,
}: Props) {
  const [acknowledged, setAcknowledged] = useState(false);

  const exportDisabled = isExporting || exportPreflightBlocksExport(preflight, acknowledged);

  const canExportSafely =
    !preflight.previewStale &&
    !preflight.pendingPreview &&
    preflight.bySeverity.critical === 0 &&
    preflight.bySeverity.warning === 0;

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) setAcknowledged(false);
        onOpenChange(next);
      }}
    >
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Exportar PDF</DialogTitle>
          <DialogDescription>
            Revisión previa para <strong>{catalogName}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {preflight.previewStale && (
            <div className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-sm">
              <AlertTriangle className="h-4 w-4 shrink-0 text-warning mt-0.5" />
              <div>
                <p className="font-medium">{EXPORT_PREFLIGHT_STALE_TITLE}</p>
                <p className="text-muted-foreground mt-0.5">{EXPORT_PREFLIGHT_STALE_BODY}</p>
              </div>
            </div>
          )}
          {preflight.pendingPreview && (
            <div className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-sm">
              <AlertTriangle className="h-4 w-4 shrink-0 text-warning mt-0.5" />
              <div>
                <p className="font-medium">Cambios de presentación sin guardar</p>
                <p className="text-muted-foreground mt-0.5">
                  Guarda la configuración en la pestaña Presentación antes de exportar, o exporta
                  con la configuración ya guardada en el servidor.
                </p>
              </div>
            </div>
          )}

          <div>
            <p className="text-sm font-medium mb-2">Resumen por severidad</p>
            <div className="flex flex-wrap gap-2">
              {(["critical", "warning", "info"] as const).map((severity) => {
                const meta = SEVERITY_META[severity];
                const Icon = meta.icon;
                const count = preflight.bySeverity[severity];
                return (
                  <Badge key={severity} variant={meta.variant} className="gap-1">
                    <Icon className="h-3 w-3" />
                    {meta.label}: {count}
                  </Badge>
                );
              })}
            </div>
          </div>

          {Object.keys(preflight.byType).length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">Incidencias por tipo</p>
              <ul className="space-y-1 text-sm text-muted-foreground">
                {Object.entries(preflight.byType).map(([type, count]) => (
                  <li key={type}>
                    · {diagnosticTypeLabel(type as LayoutDiagnostic["type"])}:{" "}
                    <span className="font-medium text-foreground">{count}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-sm leading-relaxed">{preflight.headline}</p>

          <p className="text-xs text-muted-foreground leading-relaxed">
            {CATALOG_PDF_EXPORT_BACKGROUND_NOTE}
          </p>

          {canExportSafely && preflight.bySeverity.info > 0 && (
            <p className="text-xs text-muted-foreground">
              Las incidencias informativas (sin imagen, sin categoría) no bloquean la exportación.
            </p>
          )}

          {preflight.requiresExplicitAck && (
            <label className="flex items-start gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                className="mt-1 rounded border-border"
                checked={acknowledged}
                onChange={(e) => setAcknowledged(e.target.checked)}
              />
              <span>Entiendo las incidencias críticas y deseo exportar de todos modos.</span>
            </label>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button
            type="button"
            variant="ghost"
            disabled={isExporting}
            onClick={() => onOpenChange(false)}
          >
            Cancelar
          </Button>
          {preflight.previewStale && (
            <Button
              type="button"
              variant="secondary"
              disabled={isExporting}
              onClick={() => {
                onRefreshPreview();
                onOpenChange(false);
              }}
            >
              <RefreshCw className="h-4 w-4" />
              Regenerar vista previa PDF
            </Button>
          )}
          <Button
            type="button"
            disabled={exportDisabled}
            onClick={onExport}
            title={
              exportDisabled && preflight.requiresExplicitAck && !acknowledged
                ? "Confirma que entiendes las incidencias críticas"
                : undefined
            }
          >
            {isExporting
              ? CATALOG_PDF_EXPORT_PREPARING_LABEL
              : preflight.requiresExplicitAck || preflight.previewStale || preflight.pendingPreview
                ? "Exportar de todos modos"
                : "Exportar PDF"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
