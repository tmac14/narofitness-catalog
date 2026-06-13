import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { LayoutStatusSummary } from "@/lib/catalogLayout";

type Props = {
  summary: LayoutStatusSummary;
  statusLoading?: boolean;
};

export function BuilderStatsCards({ summary, statusLoading }: Props) {
  const items = [
    { label: "Productos", value: summary.total_products },
    { label: "Overrides manuales", value: summary.manual_overrides },
    { label: "Fallbacks", value: summary.fallback_count, highlight: summary.fallback_count > 0 },
    { label: "Avisos compat.", value: summary.warning_count, highlight: summary.warning_count > 0 },
    { label: "Categorías", value: Object.keys(summary.by_section).length },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {items.map((item) => (
        <Card key={item.label} className="builder-stat-card">
          <CardContent className="pt-4 pb-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {item.label}
            </p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{item.value}</p>
            {item.highlight && (
              <Badge variant="warning" className="mt-2">
                Revisar
              </Badge>
            )}
          </CardContent>
        </Card>
      ))}
      {statusLoading && (
        <p className="text-xs text-muted-foreground col-span-full">Actualizando asignaciones…</p>
      )}
    </div>
  );
}
