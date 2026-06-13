import { useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BULK_SKIP_DISPLAY_LIMIT, type BulkLayoutFeedback } from "@/lib/catalogLayout";

type Props = {
  feedback: BulkLayoutFeedback;
};

export function BulkLayoutFeedbackPanel({ feedback }: Props) {
  const [expanded, setExpanded] = useState(false);

  const hasSkipped = feedback.skippedCount > 0;
  const hasApplied = feedback.applied > 0 || feedback.cleared > 0;
  const visibleItems = expanded ? feedback.skippedAll : feedback.skippedDetails;
  const canExpand = feedback.skippedOverflow > 0;

  if (!hasSkipped && !hasApplied) {
    return null;
  }

  return (
    <div
      className="rounded-lg border border-border bg-card shadow-sm overflow-hidden"
      role="status"
      aria-live="polite"
    >
      <div className="flex flex-wrap items-center gap-3 border-b border-border bg-muted/30 px-4 py-3">
        <p className="text-sm font-semibold text-foreground">Resultado de la aplicación masiva</p>
        <div className="flex flex-wrap gap-2 text-sm">
          {feedback.applied > 0 && (
            <span className="inline-flex items-center gap-1 rounded-md bg-success/10 px-2 py-0.5 font-medium text-success">
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
              {feedback.applied} aplicados
            </span>
          )}
          {feedback.cleared > 0 && (
            <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 font-medium text-foreground">
              {feedback.cleared} overrides eliminados
            </span>
          )}
          {hasSkipped && (
            <span className="inline-flex items-center gap-1 rounded-md bg-warning/15 px-2 py-0.5 font-medium text-warning">
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
              {feedback.skippedCount} omitidos
            </span>
          )}
        </div>
      </div>

      {hasSkipped && (
        <div className="px-4 py-3 space-y-2">
          <p className="text-xs text-muted-foreground">
            Los productos omitidos no se modificaron. Motivos más frecuentes:
          </p>
          <ul className="space-y-2 text-sm">
            {visibleItems.map((s) => (
              <li
                key={s.masterId}
                className="rounded-md border border-border/60 bg-muted/20 px-3 py-2"
              >
                <span className="font-medium text-foreground">{s.masterName}</span>
                <p className="mt-0.5 text-muted-foreground leading-snug">{s.reason}</p>
              </li>
            ))}
          </ul>
          {canExpand && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 gap-1 text-xs"
              onClick={() => setExpanded((v) => !v)}
              aria-expanded={expanded}
            >
              {expanded ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
                  Mostrar menos
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
                  Ver los {feedback.skippedCount} omitidos
                  {feedback.skippedOverflow > 0 && ` (+${feedback.skippedOverflow} más)`}
                </>
              )}
            </Button>
          )}
          {!expanded && feedback.skippedOverflow > 0 && (
            <p className="text-xs text-muted-foreground tabular-nums">
              Mostrando {BULK_SKIP_DISPLAY_LIMIT} de {feedback.skippedCount} omitidos.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
