import { API_BASE } from "@/lib/api";

export type PriceDiffRow = {
  sku: string;
  name: string;
  price_a: string | null;
  price_b: string | null;
  delta_abs: string | null;
  delta_pct: string | null;
  change_type: string;
};

const CHANGE_TYPE_LABELS: Record<string, string> = {
  only_a: "Solo en A",
  only_b: "Solo en B",
  changed: "Cambiado",
  both: "Sin cambio",
};

export function changeTypeLabel(changeType: string): string {
  return CHANGE_TYPE_LABELS[changeType] ?? changeType.replace(/_/g, " ");
}

export function priceDiffCardModifier(changeType: string): string | null {
  if (changeType === "only_a") return "responsive-data-card--only_a";
  if (changeType === "only_b") return "responsive-data-card--only_b";
  return null;
}

export function priceDiffTableRowClass(changeType: string): string {
  if (changeType === "only_a") return "diff-only-a";
  if (changeType === "only_b") return "diff-only-b";
  return "";
}

export function buildPriceDiffExportUrl(
  listA: string,
  listB: string,
  direction: string,
  minPct: string,
): string {
  const params = new URLSearchParams();
  params.set("direction", direction);
  params.set("min_delta_pct", minPct);
  return `${API_BASE}/api/v1/price-lists/${listA}/diff/${listB}/export.csv?${params.toString()}`;
}

export function formatPriceListOptionLabel(sourceFilename: string, importedAt: string): string {
  return `${sourceFilename} (${new Date(importedAt).toLocaleDateString("es-ES")})`;
}
