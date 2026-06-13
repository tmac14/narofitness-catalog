import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2, Wifi, WifiOff } from "lucide-react";
import { toast } from "sonner";
import { useStatusBar } from "@/context/useStatusBar";
import type { JobOut } from "@/lib/api";
import {
  connectionStatusLabel,
  formatLastHealthCheck,
  pdfEngineDetailMessage,
  pdfEngineUserLabel,
} from "@/lib/statusBarLabels";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { ProcessCenterJobRow } from "./ProcessCenterJobRow";

function SystemRow({
  label,
  value,
  detail,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string;
  detail?: string;
  icon: React.ComponentType<{ className?: string }>;
  tone?: "default" | "success" | "warning" | "error";
}) {
  const toneClass =
    tone === "success"
      ? "text-success"
      : tone === "warning"
        ? "text-warning"
        : tone === "error"
          ? "text-destructive"
          : "text-foreground";

  return (
    <div className="rounded-lg border border-border bg-muted/20 p-4">
      <div className="flex items-start gap-3">
        <Icon className={cn("mt-0.5 h-5 w-5 shrink-0", toneClass)} aria-hidden="true" />
        <div className="min-w-0 space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className={cn("text-sm font-medium", toneClass)}>{value}</p>
          {detail && <p className="text-sm leading-relaxed text-muted-foreground">{detail}</p>}
        </div>
      </div>
    </div>
  );
}

export function ProcessCenterPanel() {
  const {
    health,
    panelOpen,
    setPanelOpen,
    statusBarTriggerRef,
    refreshHealth,
    panelJobs,
    jobsError,
    refreshJobs,
    cancelJobById,
    downloadJobById,
  } = useStatusBar();
  const wasOpen = useRef(false);
  const [busyJobId, setBusyJobId] = useState<string | null>(null);

  const connected = health.connected;
  const pdfDegraded = connected === true && !health.pdfEngine;
  const pdfOk = connected === true && !!health.pdfEngine;

  useEffect(() => {
    if (wasOpen.current && !panelOpen) {
      statusBarTriggerRef.current?.focus();
    }
    wasOpen.current = panelOpen;
  }, [panelOpen, statusBarTriggerRef]);

  const connectionTone = connected === null ? "default" : connected ? "success" : "error";
  const pdfTone = connected !== true ? "default" : pdfOk ? "success" : "warning";

  const handleCancel = async (jobId: string) => {
    setBusyJobId(jobId);
    try {
      const result = await cancelJobById(jobId);
      if (result.ok) {
        toast.success("Tarea cancelada");
        await refreshJobs();
      } else {
        toast.error(result.message);
      }
    } finally {
      setBusyJobId(null);
    }
  };

  const handleDownload = async (job: JobOut) => {
    setBusyJobId(job.id);
    try {
      const result = await downloadJobById(job);
      if (result.ok) {
        toast.success("Descarga iniciada");
      } else {
        toast.error(result.message);
      }
    } finally {
      setBusyJobId(null);
    }
  };

  return (
    <Sheet open={panelOpen} onOpenChange={setPanelOpen}>
      <SheetContent
        id="process-center-panel"
        className="pb-6"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <SheetHeader>
          <SheetTitle>Centro de procesos</SheetTitle>
          <SheetDescription>
            Estado del sistema, conexión y tareas en curso o recientes.
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-6">
          <section aria-labelledby="process-center-jobs-heading">
            <div className="mb-2 flex items-center justify-between gap-2">
              <h2
                id="process-center-jobs-heading"
                className="text-sm font-semibold text-foreground"
              >
                Tareas
              </h2>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => void refreshJobs()}
              >
                Actualizar
              </Button>
            </div>

            {jobsError && (
              <p className="mb-2 text-sm text-warning" role="status">
                {jobsError}. La información de conexión sigue disponible.
              </p>
            )}

            {connected !== true ? (
              <p className="rounded-lg border border-border bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
                Conecte la aplicación al servicio para ver las tareas.
              </p>
            ) : panelJobs.length === 0 ? (
              <p className="rounded-lg border border-border bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
                No hay tareas recientes.
              </p>
            ) : (
              <ul className="space-y-3" role="list">
                {panelJobs.map((job) => (
                  <li key={job.id}>
                    <ProcessCenterJobRow
                      job={job}
                      busy={busyJobId === job.id}
                      onCancel={handleCancel}
                      onDownload={handleDownload}
                    />
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="process-center-system-heading" className="space-y-3">
            <h2
              id="process-center-system-heading"
              className="text-sm font-semibold text-foreground"
            >
              Sistema
            </h2>

            <SystemRow
              label="Conexión con la aplicación"
              value={connectionStatusLabel(connected)}
              detail={
                connected === false
                  ? "No se puede contactar con el servicio. Compruebe que la aplicación esté en ejecución e inténtelo de nuevo."
                  : connected === true
                    ? "La aplicación puede guardar datos y consultar productos."
                    : "Comprobando la conexión…"
              }
              icon={connected === null ? Loader2 : connected ? Wifi : WifiOff}
              tone={connectionTone}
            />

            <SystemRow
              label="Exportación PDF"
              value={pdfEngineUserLabel(health.pdfEngine, connected)}
              detail={pdfEngineDetailMessage(health.pdfEngine, health.pdfEngineError, connected, {
                available: health.pdfEnginesAvailable,
                fallback: health.pdfEngineFallback,
              })}
              icon={pdfDegraded ? AlertTriangle : pdfOk ? CheckCircle2 : Loader2}
              tone={pdfTone}
            />

            <div className="rounded-lg border border-border bg-card px-4 py-3 text-sm text-muted-foreground">
              <p>
                <span className="font-medium text-foreground">Última comprobación:</span>{" "}
                {formatLastHealthCheck(health.lastCheckedAt)}
              </p>
              {health.version && (
                <p className="mt-1">
                  <span className="font-medium text-foreground">Versión del servicio:</span>{" "}
                  {health.version}
                </p>
              )}
            </div>

            <div className="flex justify-end pt-1">
              <Button type="button" variant="secondary" size="sm" onClick={refreshHealth}>
                Comprobar de nuevo
              </Button>
            </div>
          </section>
        </div>
      </SheetContent>
    </Sheet>
  );
}
