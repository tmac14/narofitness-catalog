import { Link } from "react-router-dom";
import { LayoutDashboard } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DashboardAction } from "@/lib/dashboardData";
import { formatDashboardGreeting } from "@/lib/dashboardData";

type DashboardHeroProps = {
  statusSummary: string;
  connected: boolean | null;
  primaryAction: DashboardAction;
  secondaryAction: DashboardAction;
};

export function DashboardHero({
  statusSummary,
  connected,
  primaryAction,
  secondaryAction,
}: DashboardHeroProps) {
  const connectionLabel =
    connected === null ? null : connected ? "Conexión activa" : "Sin conexión";
  const connectionTone = connected === null ? "outline" : connected ? "secondary" : "outline";

  return (
    <header className="dashboard-hero mb-6 rounded-lg border border-border bg-card p-4 shadow-sm sm:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 flex-1 space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
              <LayoutDashboard className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <p className="text-sm text-muted-foreground">{formatDashboardGreeting()}</p>
              <h1 className="text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
                Inicio
              </h1>
            </div>
            {connectionLabel ? (
              <Badge variant={connectionTone} className="font-normal">
                {connectionLabel}
              </Badge>
            ) : null}
          </div>
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">{statusSummary}</p>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Button asChild size="sm">
            <Link to={primaryAction.to}>{primaryAction.label}</Link>
          </Button>
          <Button asChild variant="secondary" size="sm">
            <Link to={secondaryAction.to}>{secondaryAction.label}</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
