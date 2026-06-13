import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type DashboardKpiCardProps = {
  label: string;
  value: number | null;
  icon: LucideIcon;
  href?: string;
  error?: boolean;
  className?: string;
};

export function DashboardKpiCard({
  label,
  value,
  icon: Icon,
  href,
  error,
  className,
}: DashboardKpiCardProps) {
  const displayValue = error ? "—" : (value ?? 0).toLocaleString("es-ES");

  const content = (
    <Card
      className={cn(
        "dashboard-kpi builder-panel h-full",
        href && "transition-colors hover:bg-muted/20",
        className,
      )}
    >
      <CardContent className="flex items-center gap-3 p-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border bg-muted/20 text-primary">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="text-2xl font-semibold tabular-nums text-foreground">{displayValue}</p>
        </div>
      </CardContent>
    </Card>
  );

  if (href && !error) {
    return (
      <Link
        to={href}
        className="block h-full rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        {content}
      </Link>
    );
  }

  return content;
}
