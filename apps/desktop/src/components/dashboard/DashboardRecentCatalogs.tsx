import { Link } from "react-router-dom";
import type { CatalogListItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ErrorState";

type DashboardRecentCatalogsProps = {
  catalogs: CatalogListItem[];
  error?: boolean;
  onRetry?: () => void;
};

export function DashboardRecentCatalogs({
  catalogs,
  error,
  onRetry,
}: DashboardRecentCatalogsProps) {
  if (error) {
    return (
      <ErrorState
        title="No se pudieron cargar los catálogos"
        description="Compruebe la conexión e inténtelo de nuevo."
        action={
          onRetry ? (
            <Button type="button" size="sm" variant="secondary" onClick={onRetry}>
              Reintentar
            </Button>
          ) : undefined
        }
        className="py-6"
      />
    );
  }

  if (catalogs.length === 0) return null;

  return (
    <section aria-labelledby="dashboard-recent-catalogs">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 id="dashboard-recent-catalogs" className="text-sm font-semibold text-foreground">
          Catálogos recientes
        </h2>
        <Button variant="link" size="sm" asChild className="h-auto p-0">
          <Link to="/catalogs">Ver todos</Link>
        </Button>
      </div>
      <ul className="space-y-1">
        {catalogs.map((catalog) => (
          <li
            key={catalog.id}
            className="flex items-center justify-between gap-2 rounded-lg px-2 py-2 transition-colors hover:bg-muted/15"
          >
            <Link
              to={`/catalogs/${catalog.id}`}
              className="min-w-0 truncate text-sm font-medium text-primary hover:underline"
              title={catalog.name}
            >
              {catalog.name}
            </Link>
            {!catalog.cover_image_url?.trim() ? (
              <Badge variant="outline" className="shrink-0 text-[0.65rem] font-normal">
                Sin portada
              </Badge>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
