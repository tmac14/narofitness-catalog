export type LayoutMode = "automatic" | "uniform" | "manual";

export type ProductLayoutDefinition = {
  id: string;
  name: string;
  description: string;
  compatible_with: "single" | "variants" | "both";
  recommended_variant_attributes: [number, number] | null;
  recommended_image_aspect: string[];
  use_cases: string[];
  limitations: string[];
  auto_priority: number;
  auto_enabled: boolean;
  manual_only: boolean;
};

export type LayoutProductRow = {
  master_id: string;
  master_name: string;
  section_name: string;
  layout_id: string;
  has_variants: boolean;
  variant_attribute_count: number;
  image_url?: string | null;
  manual_layout_id?: string | null;
  layout_selection?: {
    layout_id: string;
    selection_mode: LayoutMode;
    requested_layout_id?: string | null;
    fallback_used?: boolean;
    fallback_reason?: string | null;
  };
};

export type DiagnosticSeverity = "critical" | "warning" | "info";

export type LayoutDiagnostic = {
  type: "fallback" | "no_image" | "no_category" | "incomplete_variants";
  severity: DiagnosticSeverity;
  master_id: string;
  master_name: string;
  message: string;
};

export type LayoutStatusSummary = {
  total_products: number;
  manual_overrides: number;
  fallback_count: number;
  warning_count: number;
  diagnostics_count: number;
  diagnostics_by_severity?: { critical: number; warning: number; info: number };
  by_layout: Record<string, number>;
  by_section: Record<string, number>;
};

export const LAYOUT_MODE_OPTIONS: {
  value: LayoutMode;
  label: string;
  description: string;
}[] = [
  {
    value: "automatic",
    label: "Automático",
    description: "El sistema elige el layout más adecuado para cada producto.",
  },
  {
    value: "uniform",
    label: "Uniforme",
    description: "Todos los productos usan el mismo layout cuando es compatible.",
  },
  {
    value: "manual",
    label: "Manual",
    description: "Permite elegir un layout concreto para cada producto.",
  },
];

export const PAGE_SIZE = 50;

export type ProductFilterState = {
  search: string;
  sectionName: string | null;
  hasVariants: "all" | "yes" | "no";
  variantAttributes: "all" | "0" | "1" | "2+";
  status: "all" | "fallback" | "warning" | "no_image" | "manual";
};

export const DEFAULT_PRODUCT_FILTER: ProductFilterState = {
  search: "",
  sectionName: null,
  hasVariants: "all",
  variantAttributes: "all",
  status: "all",
};

export function compatibilityLabel(value: ProductLayoutDefinition["compatible_with"]): string {
  switch (value) {
    case "single":
      return "Solo sin variantes";
    case "variants":
      return "Solo con variantes";
    case "both":
      return "Con y sin variantes";
    default:
      return value;
  }
}

export type CatalogItemWithMaster = {
  id: string;
  master_id: string;
  name: string;
  sort_order: number;
};

export function layoutById(
  layouts: ProductLayoutDefinition[],
  layoutId: string | null | undefined,
): ProductLayoutDefinition | undefined {
  if (!layoutId) return undefined;
  return layouts.find((layout) => layout.id === layoutId);
}

export function filterLayoutProducts(
  products: LayoutProductRow[],
  filter: ProductFilterState,
  manualOverrides: Set<string>,
  warningMasterIds: Set<string>,
): LayoutProductRow[] {
  const query = filter.search.trim().toLowerCase();
  return products.filter((product) => {
    if (filter.sectionName && product.section_name !== filter.sectionName) return false;
    if (query) {
      const haystack = `${product.master_name} ${product.section_name}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }
    if (filter.hasVariants === "yes" && !product.has_variants) return false;
    if (filter.hasVariants === "no" && product.has_variants) return false;
    if (filter.variantAttributes === "0" && product.variant_attribute_count !== 0) return false;
    if (filter.variantAttributes === "1" && product.variant_attribute_count !== 1) return false;
    if (filter.variantAttributes === "2+" && product.variant_attribute_count < 2) return false;
    if (filter.status === "fallback" && !product.layout_selection?.fallback_used) return false;
    if (filter.status === "warning" && !warningMasterIds.has(product.master_id)) return false;
    if (filter.status === "no_image" && product.image_url) return false;
    if (filter.status === "manual" && !manualOverrides.has(product.master_id)) return false;
    return true;
  });
}

export function paginate<T>(items: T[], page: number, pageSize = PAGE_SIZE): T[] {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

export function totalPages(count: number, pageSize = PAGE_SIZE): number {
  return Math.max(1, Math.ceil(count / pageSize));
}

export type SectionNavItem = {
  name: string;
  count: number;
};

export function buildSectionNav(summary: LayoutStatusSummary | null): SectionNavItem[] {
  if (!summary) return [];
  return Object.entries(summary.by_section)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => a.name.localeCompare(b.name, "es"));
}

export function parseApiError(error: unknown): string {
  if (!(error instanceof Error)) return "Error desconocido";
  const raw = error.message;
  try {
    const parsed = JSON.parse(raw) as { detail?: string };
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // plain text
  }
  return raw || "Error desconocido";
}

export function layoutPreviewClass(layoutId: string): string {
  switch (layoutId) {
    case "variant_row_wide":
      return "layout-preview layout-preview--row-wide";
    case "variant_grid_50_50":
      return "layout-preview layout-preview--grid";
    case "family_variant_table":
      return "layout-preview layout-preview--supplier-table";
    case "single_standard":
    default:
      return "layout-preview layout-preview--single";
  }
}

function normalizeDiagnosticSeverity(severity: string): DiagnosticSeverity {
  if (severity === "critical" || severity === "error") return "critical";
  if (severity === "warning") return "warning";
  return "info";
}

export function groupDiagnosticsBySeverity(
  diagnostics: LayoutDiagnostic[],
): Record<DiagnosticSeverity, LayoutDiagnostic[]> {
  const grouped: Record<DiagnosticSeverity, LayoutDiagnostic[]> = {
    critical: [],
    warning: [],
    info: [],
  };
  for (const item of diagnostics) {
    grouped[normalizeDiagnosticSeverity(item.severity)].push(item);
  }
  return grouped;
}

export function diagnosticTypeLabel(type: LayoutDiagnostic["type"]): string {
  switch (type) {
    case "fallback":
      return "Fallback";
    case "no_image":
      return "Sin imagen";
    case "no_category":
      return "Sin categoría";
    case "incomplete_variants":
      return "Variantes incompletas";
    default:
      return type;
  }
}

/** Spanish labels for layout ids (display only; API values unchanged). */
const LAYOUT_ID_DISPLAY: Record<string, string> = {
  single_standard: "Estándar sin variantes",
  variant_grid_50_50: "Grid 50/50 con variantes",
  variant_row_wide: "Fila completa con tabla de variantes",
  family_variant_table: "Tabla familia-variante (PDF)",
  incomplete_variants: "Variantes incompletas",
};

/** Exact backend skip/diagnostic strings → Spanish UI copy. */
const REASON_EXACT_ES: Record<string, string> = {
  "Layout single_standard is not compatible with variant products":
    "Este diseño no es compatible con productos con variantes.",
  "No manual layout override for this product": "Este producto no tiene un diseño manual asignado.",
  "Product not in catalog": "El producto no está en el catálogo.",
};

const LAYOUT_INCOMPAT_VARIANTS_RE =
  /^Layout ([a-z0-9_]+) is not compatible with variant products$/i;

export function layoutIdDisplayLabel(layoutId: string): string {
  return LAYOUT_ID_DISPLAY[layoutId] ?? layoutId;
}

/** Map API skip/diagnostic free-text to Spanish for user-facing UI. */
export function formatSkipOrDiagnosticReason(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return trimmed;

  const exact = REASON_EXACT_ES[trimmed];
  if (exact) return exact;

  const layoutMatch = trimmed.match(LAYOUT_INCOMPAT_VARIANTS_RE);
  if (layoutMatch) {
    const label = layoutIdDisplayLabel(layoutMatch[1]);
    return `El diseño «${label}» no es compatible con productos con variantes.`;
  }

  let result = trimmed;
  for (const [id, label] of Object.entries(LAYOUT_ID_DISPLAY)) {
    if (result.includes(id)) {
      result = result.split(id).join(label);
    }
  }
  return result;
}

export function buildExportWarningMessage(summary: LayoutStatusSummary): string | null {
  const preflight = buildExportPreflight(
    { summary, diagnostics: [] },
    { previewStale: false, pendingPreview: false },
  );
  if (preflight.details.length === 0 && !preflight.previewStale && !preflight.pendingPreview) {
    return null;
  }
  return preflight.headline;
}

export type ExportPreflightInput = {
  summary: LayoutStatusSummary;
  diagnostics?: LayoutDiagnostic[];
};

export type ExportPreflightOptions = {
  previewStale: boolean;
  pendingPreview: boolean;
};

export type ExportPreflight = {
  safeToExport: boolean;
  requiresExplicitAck: boolean;
  showModal: boolean;
  previewStale: boolean;
  pendingPreview: boolean;
  bySeverity: Record<DiagnosticSeverity, number>;
  byType: Partial<Record<LayoutDiagnostic["type"], number>>;
  headline: string;
  details: string[];
};

const EMPTY_SEVERITY: Record<DiagnosticSeverity, number> = {
  critical: 0,
  warning: 0,
  info: 0,
};

export function buildExportPreflight(
  input: ExportPreflightInput,
  options: ExportPreflightOptions,
): ExportPreflight {
  const { summary, diagnostics = [] } = input;
  const { previewStale, pendingPreview } = options;

  const bySeverity = { ...EMPTY_SEVERITY };
  if (summary.diagnostics_by_severity) {
    bySeverity.critical = summary.diagnostics_by_severity.critical ?? 0;
    bySeverity.warning = summary.diagnostics_by_severity.warning ?? 0;
    bySeverity.info = summary.diagnostics_by_severity.info ?? 0;
  } else {
    const grouped = groupDiagnosticsBySeverity(diagnostics);
    bySeverity.critical = grouped.critical.length;
    bySeverity.warning = grouped.warning.length;
    bySeverity.info = grouped.info.length;
  }

  const byType: Partial<Record<LayoutDiagnostic["type"], number>> = {};
  for (const item of diagnostics) {
    byType[item.type] = (byType[item.type] ?? 0) + 1;
  }
  if (summary.fallback_count > 0 && !byType.fallback) {
    byType.fallback = summary.fallback_count;
  }

  const details: string[] = [];
  if (previewStale) {
    details.push("La vista previa PDF puede no reflejar los últimos cambios guardados.");
  }
  if (pendingPreview) {
    details.push("Hay cambios de presentación sin guardar.");
  }
  if (bySeverity.critical > 0) {
    details.push(`${bySeverity.critical} incidencia(s) crítica(s) de presentación`);
  }
  if (summary.fallback_count > 0) {
    details.push(`${summary.fallback_count} producto(s) con fallback de layout`);
  }
  if (summary.warning_count > 0) {
    details.push(`${summary.warning_count} aviso(s) de compatibilidad de layout`);
  } else if (bySeverity.warning > 0) {
    details.push(`${bySeverity.warning} aviso(s) de presentación`);
  }
  if (byType.no_image) {
    details.push(`${byType.no_image} producto(s) sin imagen`);
  }
  if (byType.no_category) {
    details.push(`${byType.no_category} producto(s) sin categoría asignada`);
  }
  if (byType.incomplete_variants) {
    details.push(`${byType.incomplete_variants} producto(s) con variantes incompletas`);
  }

  const hasCriticalOrWarning =
    bySeverity.critical > 0 ||
    bySeverity.warning > 0 ||
    summary.fallback_count > 0 ||
    summary.warning_count > 0;

  // Info-level issues (missing images, categories) do not block auto-export.
  // Warnings, fallbacks and critical issues still open the preflight modal.
  const safeToExport = !hasCriticalOrWarning;

  const headline = safeToExport
    ? "No se detectaron incidencias relevantes. Puedes exportar el PDF con seguridad."
    : details.length > 0
      ? `${details.join(". ")}. El PDF se generará con la configuración guardada.`
      : "Revisa la presentación antes de exportar.";

  return {
    safeToExport,
    requiresExplicitAck: bySeverity.critical > 0,
    showModal: !safeToExport,
    previewStale,
    pendingPreview,
    bySeverity,
    byType,
    headline,
    details,
  };
}

/** Skip redundant layout-status reload right after initial mount load. */
export function shouldReloadLayoutStatusOnPropSync(
  initialSyncDone: boolean,
  loading: boolean,
): boolean {
  if (loading) return false;
  if (!initialSyncDone) return false;
  return true;
}

/** Whether export must be blocked until user explicitly acknowledges critical issues. */
export function exportPreflightBlocksExport(
  preflight: ExportPreflight,
  acknowledged: boolean,
): boolean {
  return preflight.requiresExplicitAck && !acknowledged;
}

export type BulkLayoutSkippedDetail = {
  masterId: string;
  masterName: string;
  reason: string;
  rawReason: string;
};

export type BulkLayoutFeedback = {
  summary: string;
  applied: number;
  cleared: number;
  skippedCount: number;
  skippedDetails: BulkLayoutSkippedDetail[];
  skippedAll: BulkLayoutSkippedDetail[];
  skippedOverflow: number;
};

export const BULK_SKIP_DISPLAY_LIMIT = 10;

function resolveMasterName(masterId: string, masterNameById: Map<string, string>): string {
  const name = masterNameById.get(masterId);
  if (name) return name;
  return masterId.length > 8 ? `${masterId.slice(0, 8)}…` : masterId;
}

function mapSkippedDetail(
  s: { master_id: string; reason: string },
  masterNameById: Map<string, string>,
): BulkLayoutSkippedDetail {
  return {
    masterId: s.master_id,
    masterName: resolveMasterName(s.master_id, masterNameById),
    reason: formatSkipOrDiagnosticReason(s.reason),
    rawReason: s.reason,
  };
}

/** Format bulk layout API result for presentation builder feedback. */
export function buildBulkLayoutFeedback(
  result: { applied: number; cleared: number; skipped: { master_id: string; reason: string }[] },
  masterNameById: Map<string, string>,
): BulkLayoutFeedback {
  const parts: string[] = [];
  if (result.applied > 0) parts.push(`${result.applied} aplicados`);
  if (result.cleared > 0) parts.push(`${result.cleared} overrides eliminados`);
  if (result.skipped.length > 0) parts.push(`${result.skipped.length} omitidos`);

  const skippedAll = result.skipped.map((s) => mapSkippedDetail(s, masterNameById));
  const skippedDetails = skippedAll.slice(0, BULK_SKIP_DISPLAY_LIMIT);
  const skippedOverflow = Math.max(0, skippedAll.length - BULK_SKIP_DISPLAY_LIMIT);

  return {
    summary: parts.join(" · ") || "Sin cambios",
    applied: result.applied,
    cleared: result.cleared,
    skippedCount: result.skipped.length,
    skippedDetails,
    skippedAll,
    skippedOverflow,
  };
}

/** Generate synthetic products for stress-testing filters (tests only). */
export function generateStressProducts(count: number): LayoutProductRow[] {
  const sections = Array.from({ length: 18 }, (_, i) => (i === 0 ? "General" : `Categoría ${i}`));
  return Array.from({ length: count }, (_, i) => ({
    master_id: `m-${i}`,
    master_name: `Producto ${i}`,
    section_name: sections[i % sections.length],
    layout_id:
      i % 3 === 0 ? "single_standard" : i % 3 === 1 ? "variant_grid_50_50" : "variant_row_wide",
    has_variants: i % 4 !== 0,
    variant_attribute_count: i % 4 === 0 ? 0 : i % 2 === 0 ? 2 : 1,
    image_url: i % 7 === 0 ? null : "/img.jpg",
    layout_selection:
      i % 11 === 0
        ? {
            layout_id: "single_standard",
            selection_mode: "automatic" as const,
            fallback_used: true,
          }
        : { layout_id: "variant_row_wide", selection_mode: "automatic" as const },
  }));
}
