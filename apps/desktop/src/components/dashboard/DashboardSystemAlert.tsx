import type { ReactNode } from "react";
import { AlertTriangle, FileText, WifiOff } from "lucide-react";
import type { HealthSnapshot } from "@/context/statusBarContextShared";
import { pdfEngineUserLabel } from "@/lib/statusBarLabels";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DashboardSystemAlertProps = {
  health: HealthSnapshot;
  jobsError: string | null;
  onOpenProcesses?: () => void;
};

type AlertRowProps = {
  icon: ReactNode;
  message: string;
  alert?: boolean;
};

function AlertRow({ icon, message, alert }: AlertRowProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-lg border px-3 py-2.5 text-sm",
        alert ? "border-amber-500/30 bg-amber-950/20 text-foreground" : "border-border bg-muted/10",
      )}
    >
      <span className="mt-0.5 shrink-0">{icon}</span>
      <p>{message}</p>
    </div>
  );
}

export function DashboardSystemAlert({
  health,
  jobsError,
  onOpenProcesses,
}: DashboardSystemAlertProps) {
  const connected = health.connected;
  const pdfDegraded = connected === true && !health.pdfEngine;
  const rows: AlertRowProps[] = [];

  if (connected === false) {
    rows.push({
      icon: <WifiOff className="h-4 w-4 text-amber-300" aria-hidden="true" />,
      message: "Sin conexión con la aplicación. Compruebe que el servicio esté en ejecución.",
      alert: true,
    });
  }

  if (pdfDegraded || health.pdfEngineError) {
    rows.push({
      icon: <FileText className="h-4 w-4 text-amber-300" aria-hidden="true" />,
      message: pdfEngineUserLabel(health.pdfEngine, connected),
      alert: true,
    });
  }

  if (jobsError) {
    rows.push({
      icon: <AlertTriangle className="h-4 w-4 text-amber-300" aria-hidden="true" />,
      message: jobsError,
      alert: true,
    });
  }

  if (rows.length === 0) return null;

  return (
    <section
      className="dashboard-system-alert space-y-2"
      aria-labelledby="dashboard-system-alert-title"
    >
      <h2 id="dashboard-system-alert-title" className="text-sm font-semibold text-foreground">
        Incidencias del sistema
      </h2>
      <div className="space-y-2">
        {rows.map((row, index) => (
          <AlertRow key={index} icon={row.icon} message={row.message} alert={row.alert} />
        ))}
      </div>
      {jobsError && onOpenProcesses ? (
        <Button type="button" size="sm" variant="secondary" onClick={onOpenProcesses}>
          Ver procesos
        </Button>
      ) : null}
    </section>
  );
}
