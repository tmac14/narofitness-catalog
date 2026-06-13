/** Spanish display labels for category mapping UI (import subcomponents). */

import type { SourceCategoryDiscovery } from "@/lib/api";

export const MAPPING_STATUS_LABELS: Record<SourceCategoryDiscovery["mapping_status"], string> = {
  mapped: "Asignada",
  unmapped: "Sin asignar",
  ambiguous: "Necesita revisión",
  ignored: "Ignorada",
};

const PROPOSAL_SOURCE_LABELS: Record<string, string> = {
  rule: "Regla automática",
  manual: "Asignación manual",
  history: "Historial previo",
  fuzzy: "Coincidencia aproximada",
  default: "Por defecto",
};

export function labelMappingStatus(status: SourceCategoryDiscovery["mapping_status"]): string {
  return MAPPING_STATUS_LABELS[status] ?? status;
}

export function labelProposalSource(source: string | null | undefined): string {
  if (!source) return "";
  return PROPOSAL_SOURCE_LABELS[source] ?? source.replace(/_/g, " ");
}

/** Turn internal category path/slug into readable breadcrumb text. */
export function formatCategoryPath(path: string): string {
  return path
    .split(/[/\\>›]/)
    .map((s) => s.trim())
    .filter(Boolean)
    .join(" › ");
}
