import type { CatalogListItem, JobOut } from "@/lib/api";
import { jobTitle } from "@/lib/jobLabels";

/** Deferred to DASHBOARD-API-2 — requires backend aggregates / activity feed. */
export const DASHBOARD_API_2_DEFERRED = [
  "Últimos productos modificados (sin updated_at en API)",
  "Importaciones pendientes de revisión (sin listImportBatches)",
  "Productos sin imagen/categoría/precio (agregados exactos)",
  "Preview PDF desactualizado por catálogo (N+1)",
  "Últimos exports globales",
  "Tendencias históricas de KPIs",
] as const;

export type DashboardKpiSnapshot = {
  products: number | null;
  catalogs: number | null;
  priceLists: number | null;
  categories: number | null;
};

export type DashboardAction = {
  label: string;
  to: string;
  variant: "primary" | "secondary";
};

export type DashboardEmptyState = {
  title: string;
  description: string;
  actionLabel: string;
  actionTo: string;
};

export type DashboardRecommendation = {
  id: string;
  tone: "default" | "warning";
  message: string;
  actionLabel?: string;
  actionTo?: string;
};

export type RecentMovement = {
  id: string;
  kind: "price_list" | "job" | "catalog";
  label: string;
  meta?: string;
  href?: string;
  status?: JobOut["status"];
};

export function formatDashboardGreeting(now = new Date()): string {
  const hour = now.getHours();
  if (hour < 12) return "Buenos días";
  if (hour < 20) return "Buenas tardes";
  return "Buenas noches";
}

export function buildKpiSnapshot(input: {
  productsTotal: number | null;
  catalogsCount: number | null;
  priceListsCount: number | null;
  categoriesCount: number | null;
}): DashboardKpiSnapshot {
  return {
    products: input.productsTotal,
    catalogs: input.catalogsCount,
    priceLists: input.priceListsCount,
    categories: input.categoriesCount,
  };
}

export function catalogsWithoutCover(catalogs: CatalogListItem[]): CatalogListItem[] {
  return catalogs.filter((catalog) => !catalog.cover_image_url?.trim());
}

export function recentPriceLists<T extends { imported_at: string }>(lists: T[], limit = 5): T[] {
  return [...lists]
    .sort((a, b) => new Date(b.imported_at).getTime() - new Date(a.imported_at).getTime())
    .slice(0, limit);
}

export function recentCatalogs(catalogs: CatalogListItem[], limit = 5): CatalogListItem[] {
  return catalogs.slice(0, limit);
}

export function formatDashboardTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function failedJobs(jobs: JobOut[]): JobOut[] {
  return jobs.filter((job) => job.status === "failed");
}

export function getPrimaryDashboardAction(input: { hasCatalogs: boolean }): {
  primary: DashboardAction;
  secondary: DashboardAction;
} {
  if (!input.hasCatalogs) {
    return {
      primary: { label: "Crear catálogo", to: "/catalogs", variant: "primary" },
      secondary: { label: "Importar tarifa", to: "/import", variant: "secondary" },
    };
  }
  return {
    primary: { label: "Abrir catálogos", to: "/catalogs", variant: "primary" },
    secondary: { label: "Importar tarifa", to: "/import", variant: "secondary" },
  };
}

export function getDashboardEmptyState(input: {
  hasCatalogs: boolean;
  catalogsError?: boolean;
}): DashboardEmptyState | null {
  if (input.catalogsError || input.hasCatalogs) return null;
  return {
    title: "Cree su primer catálogo",
    description: "Organice productos, márgenes y exportaciones comerciales en un solo lugar.",
    actionLabel: "Crear catálogo",
    actionTo: "/catalogs",
  };
}

export function shouldShowSystemAlert(input: {
  connected: boolean | null;
  pdfEngine: string | null;
  pdfEngineError: string | null;
  jobsError: string | null;
}): boolean {
  if (input.connected === false) return true;
  if (input.jobsError) return true;
  if (input.connected === true && !input.pdfEngine) return true;
  if (input.pdfEngineError) return true;
  return false;
}

export function shouldShowProcessModule(input: {
  activeJobsCount: number;
  recentTerminalFailed: boolean;
}): boolean {
  return input.activeJobsCount > 0 || input.recentTerminalFailed;
}

export function shouldShowDashboardSidebar(input: {
  recommendations: DashboardRecommendation[];
  showSystemAlert: boolean;
  showProcessModule: boolean;
}): boolean {
  return input.showSystemAlert || input.showProcessModule || input.recommendations.length > 0;
}

export function getActionableRecommendations(input: {
  catalogs: CatalogListItem[];
  hasCatalogs: boolean;
  priceListsCount: number | null;
}): DashboardRecommendation[] {
  const items: DashboardRecommendation[] = [];

  if (!input.hasCatalogs) return items;

  const withoutCover = catalogsWithoutCover(input.catalogs);
  if (withoutCover.length > 0) {
    items.push({
      id: "catalogs-no-cover",
      tone: "warning",
      message:
        withoutCover.length === 1
          ? `«${withoutCover[0].name}» no tiene portada.`
          : `${withoutCover.length} catálogos sin portada.`,
      actionLabel: "Revisar catálogos",
      actionTo: "/catalogs",
    });
  }

  if (input.priceListsCount === 0) {
    items.push({
      id: "no-price-lists",
      tone: "default",
      message: "Importe la tarifa del proveedor para alimentar precios.",
      actionLabel: "Importar tarifa",
      actionTo: "/import",
    });
  }

  return items;
}

export function buildRecentMovements(input: {
  priceLists: Array<{ id: string; source_filename: string; imported_at: string }>;
  jobs: JobOut[];
  catalogs: CatalogListItem[];
  limit?: number;
}): RecentMovement[] {
  const movements: RecentMovement[] = [];

  const latestPrice = recentPriceLists(input.priceLists, 1)[0];
  if (latestPrice) {
    movements.push({
      id: `pl-${latestPrice.id}`,
      kind: "price_list",
      label: latestPrice.source_filename,
      meta: formatDashboardTimestamp(latestPrice.imported_at),
    });
  }

  const relevantJob =
    input.jobs.find((job) => job.status === "running" || job.status === "failed") ?? input.jobs[0];
  if (relevantJob) {
    movements.push({
      id: `job-${relevantJob.id}`,
      kind: "job",
      label: jobTitle(relevantJob),
      meta: relevantJob.progress_percent != null ? `${relevantJob.progress_percent}%` : undefined,
      status: relevantJob.status,
    });
  }

  const latestCatalog = input.catalogs[0];
  if (latestCatalog) {
    movements.push({
      id: `cat-${latestCatalog.id}`,
      kind: "catalog",
      label: latestCatalog.name,
      href: `/catalogs/${latestCatalog.id}`,
    });
  }

  return movements.slice(0, input.limit ?? 4);
}

export function generalStatusSummary(input: {
  connected: boolean | null;
  hasPriceLists: boolean;
  hasCatalogs: boolean;
}): string {
  if (input.connected === false) {
    return "Sin conexión con la aplicación. Compruebe que el servicio esté en ejecución.";
  }
  if (!input.hasCatalogs) {
    return "Empiece creando un catálogo con sus productos y márgenes.";
  }
  if (!input.hasPriceLists) {
    return "Importe la tarifa del proveedor para mantener precios actualizados.";
  }
  return "Resumen de su operación comercial.";
}

/** @deprecated Use getActionableRecommendations — kept for test migration reference */
export type DashboardAttentionItem = DashboardRecommendation;
