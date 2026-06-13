import { Link } from "react-router-dom";
import { AlertCircle } from "lucide-react";
import type { DashboardRecommendation } from "@/lib/dashboardData";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DashboardRecommendationsProps = {
  items: DashboardRecommendation[];
};

export function DashboardRecommendations({ items }: DashboardRecommendationsProps) {
  if (items.length === 0) return null;

  return (
    <section aria-labelledby="dashboard-recommendations-title">
      <h2
        id="dashboard-recommendations-title"
        className="mb-3 text-sm font-semibold text-foreground"
      >
        Recomendaciones
      </h2>
      <ul className="space-y-2">
        {items.map((item) => (
          <li
            key={item.id}
            className={cn(
              "flex flex-col gap-2 rounded-lg border px-3 py-3 sm:flex-row sm:items-center sm:justify-between",
              item.tone === "warning"
                ? "border-amber-500/30 bg-amber-950/15"
                : "border-border bg-muted/10",
            )}
          >
            <div className="flex min-w-0 items-start gap-2">
              <AlertCircle
                className={cn(
                  "mt-0.5 h-4 w-4 shrink-0",
                  item.tone === "warning" ? "text-amber-300" : "text-muted-foreground",
                )}
                aria-hidden="true"
              />
              <p className="text-sm text-foreground">{item.message}</p>
            </div>
            {item.actionLabel && item.actionTo ? (
              <Button asChild size="sm" variant="secondary" className="shrink-0">
                <Link to={item.actionTo}>{item.actionLabel}</Link>
              </Button>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
