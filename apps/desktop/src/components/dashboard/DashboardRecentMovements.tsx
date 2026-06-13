import { Link } from "react-router-dom";
import { BookOpen, FileText, Loader2 } from "lucide-react";
import type { RecentMovement } from "@/lib/dashboardData";
import { jobStatusLabel } from "@/lib/jobLabels";
import { Badge } from "@/components/ui/badge";

type DashboardRecentMovementsProps = {
  movements: RecentMovement[];
  priceListsError?: boolean;
  jobsError?: boolean;
};

function MovementIcon({ kind }: { kind: RecentMovement["kind"] }) {
  if (kind === "price_list")
    return <FileText className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />;
  if (kind === "job")
    return <Loader2 className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />;
  return <BookOpen className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />;
}

export function DashboardRecentMovements({
  movements,
  priceListsError,
  jobsError,
}: DashboardRecentMovementsProps) {
  if (movements.length === 0 && !priceListsError && !jobsError) {
    return (
      <p className="text-sm text-muted-foreground">
        Aún no hay movimientos recientes. Importe una tarifa o cree un catálogo para empezar.
      </p>
    );
  }

  return (
    <section aria-labelledby="dashboard-recent-movements">
      <h2 id="dashboard-recent-movements" className="mb-3 text-sm font-semibold text-foreground">
        Últimos movimientos
      </h2>
      <ul className="dashboard-movements space-y-1">
        {movements.map((movement) => (
          <li
            key={movement.id}
            className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/15"
          >
            <MovementIcon kind={movement.kind} />
            <div className="min-w-0 flex-1">
              {movement.href ? (
                <Link
                  to={movement.href}
                  className="block truncate text-sm font-medium text-primary hover:underline"
                  title={movement.label}
                >
                  {movement.label}
                </Link>
              ) : (
                <p className="truncate text-sm font-medium text-foreground" title={movement.label}>
                  {movement.label}
                </p>
              )}
              {movement.meta ? (
                <p className="text-xs text-muted-foreground">{movement.meta}</p>
              ) : null}
            </div>
            {movement.status ? (
              <Badge variant="outline" className="shrink-0 font-normal">
                {jobStatusLabel(movement.status)}
              </Badge>
            ) : null}
          </li>
        ))}
      </ul>
      {priceListsError ? (
        <p className="mt-2 text-xs text-muted-foreground">No se pudieron cargar las tarifas.</p>
      ) : null}
      {jobsError ? (
        <p className="mt-2 text-xs text-muted-foreground">
          No se pudieron cargar las tareas recientes.
        </p>
      ) : null}
    </section>
  );
}
