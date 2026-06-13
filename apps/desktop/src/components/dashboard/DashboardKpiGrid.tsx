import { BookOpen, FileText, FolderTree, Package } from "lucide-react";
import type { DashboardKpiSnapshot } from "@/lib/dashboardData";
import type { DashboardLoadErrors } from "@/hooks/useDashboardData";
import { DashboardKpiCard } from "./DashboardKpiCard";

type DashboardKpiGridProps = {
  kpis: DashboardKpiSnapshot;
  errors: DashboardLoadErrors;
};

export function DashboardKpiGrid({ kpis, errors }: DashboardKpiGridProps) {
  const items = [
    {
      id: "products",
      label: "Productos",
      value: kpis.products,
      icon: Package,
      href: "/products",
      error: errors.products,
    },
    {
      id: "catalogs",
      label: "Catálogos",
      value: kpis.catalogs,
      icon: BookOpen,
      href: "/catalogs",
      error: errors.catalogs,
    },
    {
      id: "priceLists",
      label: "Tarifas",
      value: kpis.priceLists,
      icon: FileText,
      href: "/price-lists",
      error: errors.priceLists,
    },
    {
      id: "categories",
      label: "Categorías",
      value: kpis.categories,
      icon: FolderTree,
      href: "/categories",
      error: errors.categories,
    },
  ] as const;

  return (
    <div className="dashboard-kpi-grid mb-6" role="list" aria-label="Indicadores principales">
      {items.map((item) => (
        <div key={item.id} role="listitem">
          <DashboardKpiCard
            label={item.label}
            value={item.value}
            icon={item.icon}
            href={item.href}
            error={item.error}
          />
        </div>
      ))}
    </div>
  );
}
