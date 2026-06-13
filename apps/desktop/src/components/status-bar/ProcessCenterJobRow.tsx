import { Download, Loader2, XCircle } from "lucide-react";
import type { JobOut } from "@/lib/api";
import { buildJobRowViewModel } from "@/lib/jobLabels";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ProcessCenterJobRowProps = {
  job: JobOut;
  onCancel: (jobId: string) => Promise<void>;
  onDownload: (job: JobOut) => Promise<void>;
  busy?: boolean;
};

const STATUS_TONE: Record<string, string> = {
  queued: "text-muted-foreground",
  running: "text-primary",
  succeeded: "text-success",
  failed: "text-destructive",
  cancelled: "text-muted-foreground",
};

export function ProcessCenterJobRow({ job, onCancel, onDownload, busy }: ProcessCenterJobRowProps) {
  const vm = buildJobRowViewModel(job);

  return (
    <article
      className="rounded-lg border border-border bg-muted/20 p-4"
      aria-labelledby={`job-title-${vm.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-1">
          <h3 id={`job-title-${vm.id}`} className="truncate text-sm font-medium text-foreground">
            {vm.title}
          </h3>
          <p className={cn("text-xs font-medium uppercase tracking-wide", STATUS_TONE[vm.status])}>
            {vm.statusLabel}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {vm.canCancel && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={busy}
              aria-label={`Cancelar ${vm.title}`}
              onClick={() => void onCancel(vm.id)}
            >
              {busy ? (
                <Loader2
                  className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none"
                  aria-hidden="true"
                />
              ) : (
                <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              <span className="ml-1.5">Cancelar</span>
            </Button>
          )}
          {vm.downloadAvailable && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={busy}
              aria-label={`Descargar resultado de ${vm.title}`}
              onClick={() => void onDownload(job)}
            >
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="ml-1.5">Descargar</span>
            </Button>
          )}
        </div>
      </div>

      {vm.progressPercent != null && (
        <div className="mt-3 space-y-1">
          <div
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={vm.progressPercent}
            aria-label={vm.progressAria ?? `Progreso: ${vm.progressPercent}%`}
            className="h-1.5 overflow-hidden rounded-full bg-muted"
          >
            <div
              className="h-full rounded-full bg-primary transition-[width] duration-300 motion-reduce:transition-none"
              style={{ width: `${Math.min(100, Math.max(0, vm.progressPercent))}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground">{vm.progressPercent}%</p>
        </div>
      )}

      {vm.message && <p className="mt-2 text-sm text-muted-foreground">{vm.message}</p>}
      {vm.errorMessage && (
        <p className="mt-2 text-sm text-destructive" role="alert">
          {vm.errorMessage}
        </p>
      )}

      <dl className="mt-3 grid gap-1 text-xs text-muted-foreground sm:grid-cols-3">
        <div>
          <dt className="font-medium text-foreground/80">Creada</dt>
          <dd>{vm.createdAt}</dd>
        </div>
        <div>
          <dt className="font-medium text-foreground/80">Iniciada</dt>
          <dd>{vm.startedAt}</dd>
        </div>
        <div>
          <dt className="font-medium text-foreground/80">Finalizada</dt>
          <dd>{vm.finishedAt}</dd>
        </div>
      </dl>

      {(vm.engineLabel || vm.generatedAt) && (
        <p className="mt-2 text-xs text-muted-foreground">
          {vm.engineLabel && <span>Motor: {vm.engineLabel}</span>}
          {vm.engineLabel && vm.generatedAt && <span> · </span>}
          {vm.generatedAt && <span>Generado: {vm.generatedAt}</span>}
        </p>
      )}
    </article>
  );
}
