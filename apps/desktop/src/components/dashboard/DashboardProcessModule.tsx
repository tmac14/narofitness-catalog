import { Loader2 } from "lucide-react";
import { useStatusBar } from "@/context/useStatusBar";
import { centerStatusLabel, isActiveJobStatus } from "@/lib/jobLabels";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DashboardProcessModuleProps = {
  onOpenProcesses: () => void;
};

export function DashboardProcessModule({ onOpenProcesses }: DashboardProcessModuleProps) {
  const { activeJobs, recentTerminalJob } = useStatusBar();
  const label = centerStatusLabel(activeJobs, recentTerminalJob);
  const hasActive = activeJobs.some((job) => isActiveJobStatus(job.status));

  return (
    <section
      className="dashboard-process-module rounded-lg border border-border bg-muted/10 p-4"
      aria-labelledby="dashboard-process-title"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-2">
          <Loader2
            className={cn(
              "mt-0.5 h-4 w-4 shrink-0 text-primary",
              hasActive && "motion-safe:animate-spin motion-reduce:animate-none",
            )}
            aria-hidden="true"
          />
          <div className="min-w-0">
            <h2 id="dashboard-process-title" className="text-sm font-semibold text-foreground">
              Procesos en curso
            </h2>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </div>
        <Button type="button" size="sm" variant="secondary" onClick={onOpenProcesses}>
          Ver procesos
        </Button>
      </div>
    </section>
  );
}
