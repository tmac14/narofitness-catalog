import { describe, expect, it } from "vitest";
import {
  buildBulkLayoutFeedback,
  formatSkipOrDiagnosticReason,
  layoutIdDisplayLabel,
  layoutPreviewClass,
  exportPreflightBlocksExport,
  buildExportPreflight,
  buildExportWarningMessage,
  buildSectionNav,
  DEFAULT_PRODUCT_FILTER,
  filterLayoutProducts,
  generateStressProducts,
  groupDiagnosticsBySeverity,
  LAYOUT_MODE_OPTIONS,
  layoutById,
  paginate,
  shouldReloadLayoutStatusOnPropSync,
  totalPages,
  type LayoutDiagnostic,
  type LayoutProductRow,
} from "./catalogLayout";

const sampleProducts: LayoutProductRow[] = [
  {
    master_id: "m1",
    master_name: "Kettlebell",
    section_name: "Pesas",
    layout_id: "variant_row_wide",
    has_variants: true,
    variant_attribute_count: 2,
    image_url: "/img.jpg",
    layout_selection: { layout_id: "variant_row_wide", selection_mode: "automatic" },
  },
  {
    master_id: "m2",
    master_name: "Disco",
    section_name: "Pesas",
    layout_id: "variant_grid_50_50",
    has_variants: true,
    variant_attribute_count: 1,
    image_url: null,
    layout_selection: {
      layout_id: "variant_grid_50_50",
      selection_mode: "automatic",
      fallback_used: true,
    },
  },
  {
    master_id: "m3",
    master_name: "Mat",
    section_name: "General",
    layout_id: "single_standard",
    has_variants: false,
    variant_attribute_count: 0,
    image_url: "/mat.jpg",
    layout_selection: { layout_id: "single_standard", selection_mode: "automatic" },
  },
];

describe("catalogLayout helpers", () => {
  it("filters by section and search", () => {
    const filtered = filterLayoutProducts(
      sampleProducts,
      { ...DEFAULT_PRODUCT_FILTER, sectionName: "Pesas", search: "disco" },
      new Set(),
      new Set(),
    );
    expect(filtered).toHaveLength(1);
    expect(filtered[0].master_id).toBe("m2");
  });

  it("filters fallback and manual status", () => {
    const fallback = filterLayoutProducts(
      sampleProducts,
      { ...DEFAULT_PRODUCT_FILTER, status: "fallback" },
      new Set(),
      new Set(),
    );
    expect(fallback).toHaveLength(1);

    const manual = filterLayoutProducts(
      sampleProducts,
      { ...DEFAULT_PRODUCT_FILTER, status: "manual" },
      new Set(["m1"]),
      new Set(),
    );
    expect(manual).toHaveLength(1);
  });

  it("paginates large lists", () => {
    const many = Array.from({ length: 120 }, (_, i) => ({
      ...sampleProducts[0],
      master_id: `m-${i}`,
      master_name: `Product ${i}`,
    }));
    expect(totalPages(many.length)).toBe(3);
    expect(paginate(many, 2)).toHaveLength(50);
  });

  it("builds section navigation", () => {
    const nav = buildSectionNav({
      total_products: 3,
      manual_overrides: 0,
      fallback_count: 1,
      warning_count: 0,
      diagnostics_count: 0,
      by_layout: {},
      by_section: { Pesas: 2, General: 1 },
    });
    expect(nav).toHaveLength(2);
    expect(nav[0].name).toBe("General");
  });

  it("finds layout by id", () => {
    const layout = layoutById(
      [
        {
          id: "single_standard",
          name: "Single",
          description: "",
          compatible_with: "single",
          recommended_variant_attributes: null,
          recommended_image_aspect: ["any"],
          use_cases: [],
          limitations: [],
          auto_priority: 1,
          auto_enabled: true,
          manual_only: false,
        },
      ],
      "single_standard",
    );
    expect(layout?.name).toBe("Single");
  });

  it("defines three layout modes", () => {
    expect(LAYOUT_MODE_OPTIONS.map((option) => option.value)).toEqual([
      "automatic",
      "uniform",
      "manual",
    ]);
  });

  it("handles 400-product stress dataset with pagination", () => {
    const products = generateStressProducts(400);
    expect(products).toHaveLength(400);
    expect(totalPages(products.length)).toBe(8);
    expect(paginate(products, 1)).toHaveLength(50);
    expect(paginate(products, 8)).toHaveLength(50);
  });

  it("applies combined filters on large dataset", () => {
    const products = generateStressProducts(400);
    const manual = new Set(["m-0", "m-5"]);
    const warnings = new Set(["m-10"]);
    const filtered = filterLayoutProducts(
      products,
      {
        ...DEFAULT_PRODUCT_FILTER,
        sectionName: "Categoría 1",
        hasVariants: "yes",
        variantAttributes: "2+",
        status: "fallback",
      },
      manual,
      warnings,
    );
    for (const product of filtered) {
      expect(product.section_name).toBe("Categoría 1");
      expect(product.has_variants).toBe(true);
      expect(product.variant_attribute_count).toBeGreaterThanOrEqual(2);
      expect(product.layout_selection?.fallback_used).toBe(true);
    }
  });

  it("groups diagnostics by severity", () => {
    const diagnostics: LayoutDiagnostic[] = [
      { type: "fallback", severity: "warning", master_id: "a", master_name: "A", message: "fb" },
      { type: "no_image", severity: "info", master_id: "b", master_name: "B", message: "img" },
      {
        type: "incomplete_variants",
        severity: "critical",
        master_id: "c",
        master_name: "C",
        message: "var",
      },
    ];
    const grouped = groupDiagnosticsBySeverity(diagnostics);
    expect(grouped.warning).toHaveLength(1);
    expect(grouped.info).toHaveLength(1);
    expect(grouped.critical).toHaveLength(1);
  });

  it("builds export warning message for relevant issues only", () => {
    expect(
      buildExportWarningMessage({
        total_products: 10,
        manual_overrides: 0,
        fallback_count: 2,
        warning_count: 1,
        diagnostics_count: 3,
        by_layout: {},
        by_section: {},
      }),
    ).toContain("fallback");

    expect(
      buildExportWarningMessage({
        total_products: 10,
        manual_overrides: 0,
        fallback_count: 0,
        warning_count: 0,
        diagnostics_count: 0,
        by_layout: {},
        by_section: {},
      }),
    ).toBeNull();
  });

  it("filters bulk-apply candidates by section", () => {
    const products = generateStressProducts(120);
    const sectionFiltered = filterLayoutProducts(
      products,
      { ...DEFAULT_PRODUCT_FILTER, sectionName: "Categoría 5" },
      new Set(),
      new Set(),
    );
    expect(sectionFiltered.length).toBeGreaterThan(0);
    expect(sectionFiltered.every((p) => p.section_name === "Categoría 5")).toBe(true);
  });

  it("buildExportPreflight marks safe export when no issues", () => {
    const preflight = buildExportPreflight(
      {
        summary: {
          total_products: 10,
          manual_overrides: 0,
          fallback_count: 0,
          warning_count: 0,
          diagnostics_count: 0,
          diagnostics_by_severity: { critical: 0, warning: 0, info: 0 },
          by_layout: {},
          by_section: {},
        },
        diagnostics: [],
      },
      { previewStale: false, pendingPreview: false },
    );
    expect(preflight.safeToExport).toBe(true);
    expect(preflight.showModal).toBe(false);
    expect(preflight.requiresExplicitAck).toBe(false);
  });

  it("buildExportPreflight requires ack for critical and shows modal for fallbacks", () => {
    const withFallback = buildExportPreflight(
      {
        summary: {
          total_products: 10,
          manual_overrides: 0,
          fallback_count: 3,
          warning_count: 0,
          diagnostics_count: 3,
          diagnostics_by_severity: { critical: 0, warning: 3, info: 0 },
          by_layout: {},
          by_section: {},
        },
        diagnostics: [
          {
            type: "fallback",
            severity: "warning",
            master_id: "a",
            master_name: "A",
            message: "fb",
          },
        ],
      },
      { previewStale: false, pendingPreview: false },
    );
    expect(withFallback.showModal).toBe(true);
    expect(withFallback.safeToExport).toBe(false);
    expect(withFallback.details.some((d) => d.includes("fallback"))).toBe(true);

    const withCritical = buildExportPreflight(
      {
        summary: {
          total_products: 1,
          manual_overrides: 0,
          fallback_count: 0,
          warning_count: 0,
          diagnostics_count: 1,
          diagnostics_by_severity: { critical: 1, warning: 0, info: 0 },
          by_layout: {},
          by_section: {},
        },
        diagnostics: [],
      },
      { previewStale: false, pendingPreview: false },
    );
    expect(withCritical.requiresExplicitAck).toBe(true);
  });

  it("buildExportPreflight auto-exports for info-only issues", () => {
    const preflight = buildExportPreflight(
      {
        summary: {
          total_products: 5,
          manual_overrides: 0,
          fallback_count: 0,
          warning_count: 0,
          diagnostics_count: 2,
          diagnostics_by_severity: { critical: 0, warning: 0, info: 2 },
          by_layout: {},
          by_section: {},
        },
        diagnostics: [
          {
            type: "no_image",
            severity: "info",
            master_id: "a",
            master_name: "A",
            message: "sin img",
          },
        ],
      },
      { previewStale: false, pendingPreview: false },
    );
    expect(preflight.safeToExport).toBe(true);
    expect(preflight.showModal).toBe(false);
    expect(preflight.requiresExplicitAck).toBe(false);
    expect(preflight.byType.no_image).toBe(1);
    expect(preflight.details.some((d) => d.includes("sin imagen"))).toBe(true);
  });

  it("buildExportPreflight includes preview stale in details without blocking export", () => {
    const preflight = buildExportPreflight(
      {
        summary: {
          total_products: 1,
          manual_overrides: 0,
          fallback_count: 0,
          warning_count: 0,
          diagnostics_count: 0,
          by_layout: {},
          by_section: {},
        },
        diagnostics: [],
      },
      { previewStale: true, pendingPreview: false },
    );
    expect(preflight.previewStale).toBe(true);
    expect(preflight.safeToExport).toBe(true);
    expect(preflight.showModal).toBe(false);
    expect(preflight.details[0]).toContain("vista previa PDF");
  });

  it("shouldReloadLayoutStatusOnPropSync skips initial mount", () => {
    expect(shouldReloadLayoutStatusOnPropSync(false, true)).toBe(false);
    expect(shouldReloadLayoutStatusOnPropSync(false, false)).toBe(false);
    expect(shouldReloadLayoutStatusOnPropSync(true, false)).toBe(true);
    expect(shouldReloadLayoutStatusOnPropSync(true, true)).toBe(false);
  });

  it("exportPreflightBlocksExport requires ack for critical issues", () => {
    const preflight = buildExportPreflight(
      {
        summary: {
          total_products: 1,
          manual_overrides: 0,
          fallback_count: 0,
          warning_count: 0,
          diagnostics_count: 1,
          diagnostics_by_severity: { critical: 1, warning: 0, info: 0 },
          by_layout: {},
          by_section: {},
        },
        diagnostics: [],
      },
      { previewStale: false, pendingPreview: false },
    );
    expect(preflight.requiresExplicitAck).toBe(true);
    expect(exportPreflightBlocksExport(preflight, false)).toBe(true);
    expect(exportPreflightBlocksExport(preflight, true)).toBe(false);
  });

  it("layoutIdDisplayLabel maps known layout ids to Spanish", () => {
    expect(layoutIdDisplayLabel("single_standard")).toBe("Estándar sin variantes");
    expect(layoutIdDisplayLabel("variant_grid_50_50")).toBe("Grid 50/50 con variantes");
    expect(layoutIdDisplayLabel("variant_row_wide")).toBe("Fila completa con tabla de variantes");
    expect(layoutIdDisplayLabel("family_variant_table")).toBe("Tabla familia-variante (PDF)");
    expect(layoutIdDisplayLabel("unknown_layout")).toBe("unknown_layout");
  });

  it("layoutPreviewClass maps family_variant_table wireframe class", () => {
    expect(layoutPreviewClass("family_variant_table")).toBe(
      "layout-preview layout-preview--supplier-table",
    );
  });

  it("formatSkipOrDiagnosticReason maps backend strings to Spanish", () => {
    expect(
      formatSkipOrDiagnosticReason(
        "Layout single_standard is not compatible with variant products",
      ),
    ).toBe("Este diseño no es compatible con productos con variantes.");
    expect(formatSkipOrDiagnosticReason("No manual layout override for this product")).toBe(
      "Este producto no tiene un diseño manual asignado.",
    );
    expect(formatSkipOrDiagnosticReason("Product not in catalog")).toBe(
      "El producto no está en el catálogo.",
    );
    expect(
      formatSkipOrDiagnosticReason(
        "Layout variant_row_wide is not compatible with variant products",
      ),
    ).toBe(
      "El diseño «Fila completa con tabla de variantes» no es compatible con productos con variantes.",
    );
  });

  it("buildBulkLayoutFeedback formats summary and skip details", () => {
    const names = new Map([
      ["m1", "Kettlebell"],
      ["m2", "Disco"],
    ]);
    const feedback = buildBulkLayoutFeedback(
      {
        applied: 3,
        cleared: 0,
        skipped: [
          { master_id: "m1", reason: "Product not in catalog" },
          {
            master_id: "m2",
            reason: "Layout single_standard is not compatible with variant products",
          },
        ],
      },
      names,
    );
    expect(feedback.summary).toBe("3 aplicados · 2 omitidos");
    expect(feedback.applied).toBe(3);
    expect(feedback.skippedCount).toBe(2);
    expect(feedback.skippedDetails).toHaveLength(2);
    expect(feedback.skippedAll).toHaveLength(2);
    expect(feedback.skippedDetails[0].masterName).toBe("Kettlebell");
    expect(feedback.skippedDetails[0].reason).toBe("El producto no está en el catálogo.");
    expect(feedback.skippedDetails[0].rawReason).toBe("Product not in catalog");
    expect(feedback.skippedDetails[1].reason).toBe(
      "Este diseño no es compatible con productos con variantes.",
    );
    expect(feedback.skippedOverflow).toBe(0);
  });

  it("buildBulkLayoutFeedback falls back for unknown master", () => {
    const feedback = buildBulkLayoutFeedback(
      {
        applied: 0,
        cleared: 0,
        skipped: [{ master_id: "abcdefgh-1234", reason: "Product not in catalog" }],
      },
      new Map(),
    );
    expect(feedback.skippedDetails[0].masterName).toBe("abcdefgh…");
  });

  it("buildBulkLayoutFeedback caps displayed skips", () => {
    const skipped = Array.from({ length: 12 }, (_, i) => ({
      master_id: `m-${i}`,
      reason: "skipped",
    }));
    const feedback = buildBulkLayoutFeedback({ applied: 0, cleared: 0, skipped }, new Map());
    expect(feedback.skippedDetails).toHaveLength(10);
    expect(feedback.skippedAll).toHaveLength(12);
    expect(feedback.skippedOverflow).toBe(2);
  });

  it("buildBulkLayoutFeedback returns Sin cambios when empty", () => {
    const feedback = buildBulkLayoutFeedback({ applied: 0, cleared: 0, skipped: [] }, new Map());
    expect(feedback.summary).toBe("Sin cambios");
    expect(feedback.skippedDetails).toHaveLength(0);
  });

  it("exportPreflightBlocksExport allows export for warnings without ack", () => {
    const preflight = buildExportPreflight(
      {
        summary: {
          total_products: 10,
          manual_overrides: 0,
          fallback_count: 2,
          warning_count: 0,
          diagnostics_count: 2,
          diagnostics_by_severity: { critical: 0, warning: 2, info: 0 },
          by_layout: {},
          by_section: {},
        },
        diagnostics: [],
      },
      { previewStale: false, pendingPreview: false },
    );
    expect(exportPreflightBlocksExport(preflight, false)).toBe(false);
  });
});
