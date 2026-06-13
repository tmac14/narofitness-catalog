import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  FolderTree,
  LayoutGrid,
  Loader2,
  Search,
} from "lucide-react";
import { toast } from "sonner";
import {
  bulkProductLayouts,
  deleteProductLayout,
  getCatalogLayoutStatus,
  listCatalogLayouts,
  type CatalogProductLayout,
  type CatalogSectionCover,
  type Category,
  type LayoutMode,
  type ProductLayoutDefinition,
  updateCatalog,
  upsertProductLayout,
} from "@/lib/api";
import {
  buildBulkLayoutFeedback,
  buildSectionNav,
  compatibilityLabel,
  DEFAULT_PRODUCT_FILTER,
  filterLayoutProducts,
  LAYOUT_MODE_OPTIONS,
  layoutPreviewClass,
  PAGE_SIZE,
  paginate,
  parseApiError,
  shouldReloadLayoutStatusOnPropSync,
  type BulkLayoutFeedback,
  type LayoutDiagnostic,
  type ProductFilterState,
} from "@/lib/catalogLayout";
import { PaginationBar } from "@/components/ui/pagination";
import { DataTableScroll } from "@/components/ui/data-table";
import {
  isPageFullySelected,
  selectAllFiltered,
  toggleItemSelection,
  togglePageSelection,
  filteredSelectionLabel,
} from "@/lib/selection";
import { applyDiagnosticsFilter } from "@/lib/editorPreview";
import { clampPage } from "@/lib/pagination";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { BuilderStatsCards } from "@/components/catalog-builder/BuilderStatsCards";
import { BulkLayoutFeedbackPanel } from "@/components/catalog-builder/BulkLayoutFeedbackPanel";
import { CatalogSectionCoversPanel } from "@/components/catalog-builder/CatalogSectionCoversPanel";
import { DiagnosticsPanel } from "@/components/catalog-builder/DiagnosticsPanel";
import { PresentationLoadingState } from "@/components/catalog-builder/PresentationLoadingState";
import { ProductLayoutRow } from "@/components/catalog-builder/ProductLayoutRow";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

type Props = {
  catalogId: string;
  layoutMode: LayoutMode;
  uniformLayoutId: string | null;
  productLayouts: CatalogProductLayout[];
  sectionCovers: CatalogSectionCover[];
  categoryTree: Category[];
  onSectionCoversUpdated: () => void;
  onCoverMediaChanged: () => void;
  onConfigSaved: () => void;
  onPreviewStale: () => void;
  onPendingPreviewChange: (pending: boolean) => void;
};

function LayoutMiniPreview({ layoutId }: { layoutId: string }) {
  const cls = layoutPreviewClass(layoutId);
  if (layoutId === "variant_grid_50_50") {
    return (
      <div className={cls} aria-hidden="true">
        <div className="layout-preview__block h-full" />
        <div className="flex flex-col gap-0.5">
          <div className="layout-preview__block h-2" />
          <div className="layout-preview__block layout-preview__block--muted h-6 flex-1" />
        </div>
      </div>
    );
  }
  if (layoutId === "variant_row_wide") {
    return (
      <div className={cls} aria-hidden="true">
        <div className="flex flex-col gap-0.5">
          <div className="layout-preview__block h-2" />
          <div className="layout-preview__block layout-preview__block--muted h-8" />
        </div>
        <div className="layout-preview__block layout-preview__block--muted h-full" />
      </div>
    );
  }
  if (layoutId === "family_variant_table") {
    return (
      <div className={cls} aria-hidden="true">
        <div className="layout-preview__block layout-preview__block--section h-2 w-full" />
        <div className="layout-preview__block layout-preview__block--family h-2 w-full" />
        <div className="layout-preview__block layout-preview__block--muted h-1.5 w-full" />
        <div className="layout-preview__block layout-preview__block--muted h-1.5 w-full" />
      </div>
    );
  }
  return (
    <div className={cls} aria-hidden="true">
      <div className="flex flex-col gap-0.5">
        <div className="layout-preview__block h-2" />
        <div className="layout-preview__block layout-preview__block--muted h-8" />
      </div>
      <div className="layout-preview__block layout-preview__block--muted h-6 self-start mt-auto" />
    </div>
  );
}

export function CatalogPresentationBuilder({
  catalogId,
  layoutMode: initialLayoutMode,
  uniformLayoutId: initialUniformLayoutId,
  productLayouts,
  sectionCovers,
  categoryTree,
  onSectionCoversUpdated,
  onCoverMediaChanged,
  onConfigSaved,
  onPreviewStale,
  onPendingPreviewChange,
}: Props) {
  const [layouts, setLayouts] = useState<ProductLayoutDefinition[]>([]);
  const [layoutStatus, setLayoutStatus] = useState<Awaited<
    ReturnType<typeof getCatalogLayoutStatus>
  > | null>(null);
  const [layoutMode, setLayoutMode] = useState<LayoutMode>(initialLayoutMode);
  const [uniformLayoutId, setUniformLayoutId] = useState(initialUniformLayoutId ?? "");
  const [filter, setFilter] = useState<ProductFilterState>(DEFAULT_PRODUCT_FILTER);
  const [searchInput, setSearchInput] = useState("");
  const [masterHighlightId, setMasterHighlightId] = useState<string | null>(null);
  const debouncedSearch = useDebouncedValue(searchInput, 300);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZE);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expandedMasterId, setExpandedMasterId] = useState<string | null>(null);
  const [bulkLayoutId, setBulkLayoutId] = useState("");
  const [loading, setLoading] = useState(true);
  const [statusLoading, setStatusLoading] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [bulkWorking, setBulkWorking] = useState(false);
  const [rowSaving, setRowSaving] = useState<string | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [bulkFeedback, setBulkFeedback] = useState<BulkLayoutFeedback | null>(null);
  const initialSyncDone = useRef(false);

  useEffect(() => {
    initialSyncDone.current = false;
  }, [catalogId]);

  const manualOverrideMap = useMemo(
    () => new Map(productLayouts.map((row) => [row.master_id, row.layout_id])),
    [productLayouts],
  );
  const manualOverrideIds = useMemo(() => new Set(manualOverrideMap.keys()), [manualOverrideMap]);
  const warningMasterIds = useMemo(
    () => new Set((layoutStatus?.layout_warnings ?? []).map((w) => w.master_id)),
    [layoutStatus],
  );

  const configDirty =
    layoutMode !== initialLayoutMode ||
    (layoutMode === "uniform" && (uniformLayoutId || null) !== (initialUniformLayoutId || null));

  useEffect(() => {
    onPendingPreviewChange(configDirty);
  }, [configDirty, onPendingPreviewChange]);

  const loadStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await getCatalogLayoutStatus(catalogId);
      setLayoutStatus(status);
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setStatusLoading(false);
    }
  }, [catalogId]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      setLoading(true);
      try {
        const [registry, status] = await Promise.all([
          listCatalogLayouts(),
          getCatalogLayoutStatus(catalogId),
        ]);
        if (!cancelled) {
          setLayouts(registry.items);
          setLayoutStatus(status);
        }
      } catch (error) {
        if (!cancelled) toast.error(parseApiError(error));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [catalogId]);

  useEffect(() => {
    if (!shouldReloadLayoutStatusOnPropSync(initialSyncDone.current, loading)) {
      if (!loading && !initialSyncDone.current) initialSyncDone.current = true;
      return;
    }
    void loadStatus();
  }, [productLayouts, initialLayoutMode, initialUniformLayoutId, loading, loadStatus]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLayoutMode(initialLayoutMode);
      setUniformLayoutId(initialUniformLayoutId ?? "");
    }, 0);
    return () => window.clearTimeout(timer);
  }, [initialLayoutMode, initialUniformLayoutId]);

  const effectiveFilter = useMemo(
    () => ({ ...filter, search: debouncedSearch }),
    [filter, debouncedSearch],
  );

  const filteredProducts = useMemo(() => {
    if (!layoutStatus) return [];
    let rows = filterLayoutProducts(
      layoutStatus.products,
      effectiveFilter,
      manualOverrideIds,
      warningMasterIds,
    );
    if (masterHighlightId) {
      rows = rows.filter((p) => p.master_id === masterHighlightId);
    }
    return rows;
  }, [layoutStatus, effectiveFilter, manualOverrideIds, warningMasterIds, masterHighlightId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPage(1);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [effectiveFilter, masterHighlightId, pageSize]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPage((p) => clampPage(p, filteredProducts.length, pageSize));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [filteredProducts.length, pageSize]);

  const pageItems = useMemo(
    () => paginate(filteredProducts, page, pageSize),
    [filteredProducts, page, pageSize],
  );
  const sections = buildSectionNav(layoutStatus?.summary ?? null);
  const showManualControls = initialLayoutMode === "manual";
  const pageAllSelected = isPageFullySelected(pageItems, selected);

  const markPreviewStale = useCallback(() => {
    onPreviewStale();
  }, [onPreviewStale]);

  async function saveLayoutConfig() {
    setSavingConfig(true);
    setConfigError(null);
    try {
      if (layoutMode === "uniform" && !uniformLayoutId) {
        setConfigError("Selecciona un layout uniforme.");
        return;
      }
      await updateCatalog(catalogId, {
        layout_mode: layoutMode,
        uniform_layout_id: layoutMode === "uniform" ? uniformLayoutId : null,
      });
      toast.success("Configuración guardada");
      onConfigSaved();
      await loadStatus();
      markPreviewStale();
    } catch (error) {
      setConfigError(parseApiError(error));
    } finally {
      setSavingConfig(false);
    }
  }

  async function runBulkApply(masterIds: string[], clear = false) {
    if (masterIds.length === 0) {
      toast.error("No hay productos seleccionados");
      return;
    }
    if (!clear && !bulkLayoutId) {
      toast.error("Selecciona un layout para aplicar");
      return;
    }

    setBulkWorking(true);
    setBulkFeedback(null);
    try {
      if (!clear && initialLayoutMode !== "manual") {
        await updateCatalog(catalogId, { layout_mode: "manual" });
        onConfigSaved();
      }
      const result = await bulkProductLayouts(catalogId, {
        layout_id: clear ? null : bulkLayoutId,
        master_ids: masterIds,
      });
      const nameById = new Map(
        (layoutStatus?.products ?? []).map((p) => [p.master_id, p.master_name]),
      );
      const feedback = buildBulkLayoutFeedback(result, nameById);
      setBulkFeedback(feedback);
      if (result.applied > 0 || result.cleared > 0) {
        toast.success(
          clear
            ? `Overrides eliminados: ${result.cleared}`
            : `Layout aplicado a ${result.applied} producto(s)`,
        );
      }
      if (result.skipped.length > 0) {
        const first = feedback.skippedDetails[0];
        toast.warning(
          first
            ? `${result.skipped.length} omitidos: ${first.masterName} — ${first.reason}`
            : `${result.skipped.length} omitidos`,
        );
      }
      setSelected(new Set());
      onConfigSaved();
      await loadStatus();
      markPreviewStale();
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setBulkWorking(false);
    }
  }

  async function saveManualLayout(masterId: string, layoutId: string) {
    setRowSaving(masterId);
    try {
      await upsertProductLayout(catalogId, masterId, layoutId);
      onConfigSaved();
      await loadStatus();
      markPreviewStale();
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setRowSaving(null);
    }
  }

  async function clearManualLayout(masterId: string) {
    setRowSaving(masterId);
    try {
      await deleteProductLayout(catalogId, masterId);
      onConfigSaved();
      await loadStatus();
      markPreviewStale();
    } catch (error) {
      toast.error(parseApiError(error));
    } finally {
      setRowSaving(null);
    }
  }

  if (loading) {
    return <PresentationLoadingState />;
  }

  if (!layoutStatus || layoutStatus.products.length === 0) {
    return (
      <Card className="builder-panel min-h-[var(--table-min-height,480px)]">
        <CardContent className="py-16 text-center space-y-2">
          <p className="font-medium">Sin productos en el catálogo</p>
          <p className="text-sm text-muted-foreground">
            Añade productos en la pestaña Productos para configurar la presentación.
          </p>
        </CardContent>
      </Card>
    );
  }

  const summary = layoutStatus.summary;
  const diagnostics = layoutStatus.diagnostics as LayoutDiagnostic[];

  return (
    <div className="space-y-6">
      <BuilderStatsCards summary={summary} statusLoading={statusLoading} />

      <CatalogSectionCoversPanel
        catalogId={catalogId}
        sectionCovers={sectionCovers}
        bySection={summary.by_section}
        categories={categoryTree}
        onSectionCoversUpdated={onSectionCoversUpdated}
        onCoverMediaChanged={onCoverMediaChanged}
      />

      <div className="grid gap-6 xl:grid-cols-[var(--builder-sidebar-width,260px)_minmax(0,1fr)]">
        <Card className="builder-panel h-fit xl:sticky xl:top-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <FolderTree className="h-4 w-4" />
              Categorías
            </CardTitle>
            <CardDescription>Filtra por sección del catálogo</CardDescription>
          </CardHeader>
          <CardContent className="space-y-0.5 max-h-[480px] overflow-auto">
            <button
              type="button"
              className={`category-nav-item ${filter.sectionName === null ? "category-nav-item--active" : ""}`}
              onClick={() => setFilter((f) => ({ ...f, sectionName: null }))}
            >
              <span>Todas</span>
              <Badge variant="secondary">{summary.total_products}</Badge>
            </button>
            {sections.map((section) => (
              <button
                key={section.name}
                type="button"
                className={`category-nav-item ${filter.sectionName === section.name ? "category-nav-item--active" : ""}`}
                onClick={() => setFilter((f) => ({ ...f, sectionName: section.name }))}
              >
                <span className="truncate pr-2">{section.name}</span>
                <Badge variant="secondary">{section.count}</Badge>
              </button>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6 min-w-0">
          <Card className="builder-panel">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <LayoutGrid className="h-4 w-4" />
                Modo de presentación
              </CardTitle>
              <div className="text-sm text-muted-foreground flex flex-wrap items-center gap-x-1 gap-y-1">
                <span>
                  Modo guardado:{" "}
                  <strong>
                    {LAYOUT_MODE_OPTIONS.find((o) => o.value === initialLayoutMode)?.label}
                  </strong>
                  · {summary.total_products} productos
                </span>
                {configDirty && <Badge variant="warning">Cambios sin guardar</Badge>}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                {LAYOUT_MODE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    aria-pressed={layoutMode === option.value}
                    className={cn(
                      "rounded-lg border p-3 text-left transition-colors hover:bg-muted/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      layoutMode === option.value &&
                        "border-primary bg-primary/5 ring-1 ring-primary/20",
                    )}
                    onClick={() => setLayoutMode(option.value)}
                  >
                    <p className="text-sm font-medium">{option.label}</p>
                    <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                      {option.description}
                    </p>
                  </button>
                ))}
              </div>
              {layoutMode === "uniform" && (
                <div className="space-y-2 max-w-md">
                  <Label htmlFor="uniform-layout">Layout uniforme</Label>
                  <Select
                    id="uniform-layout"
                    value={uniformLayoutId}
                    onChange={(e) => setUniformLayoutId(e.target.value)}
                  >
                    <option value="">— Seleccionar —</option>
                    {layouts.map((layout) => (
                      <option key={layout.id} value={layout.id}>
                        {layout.name}
                      </option>
                    ))}
                  </Select>
                </div>
              )}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  disabled={savingConfig || !configDirty}
                  onClick={() => {
                    void saveLayoutConfig();
                  }}
                >
                  {savingConfig ? "Guardando…" : "Guardar configuración"}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={statusLoading}
                  onClick={() => {
                    void loadStatus();
                  }}
                >
                  {statusLoading ? "Actualizando…" : "Actualizar asignaciones"}
                </Button>
              </div>
              {configError && (
                <p className="text-sm text-destructive flex items-center gap-1">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {configError}
                </p>
              )}
            </CardContent>
          </Card>

          <div className="builder-sticky-bar">
            <span className="text-sm font-medium text-muted-foreground whitespace-nowrap tabular-nums">
              {filteredSelectionLabel(selected.size, filteredProducts.length, pageItems.length)}
            </span>
            <Label htmlFor="presentation-bulk-layout" className="sr-only">
              Layout para aplicación masiva
            </Label>
            <Select
              id="presentation-bulk-layout"
              name="bulkLayout"
              className="w-44 h-8"
              value={bulkLayoutId}
              onChange={(e) => setBulkLayoutId(e.target.value)}
              aria-label="Layout para aplicación masiva"
            >
              <option value="">Layout para bulk…</option>
              {layouts.map((layout) => (
                <option key={layout.id} value={layout.id}>
                  {layout.name}
                </option>
              ))}
            </Select>
            <Button
              type="button"
              size="sm"
              disabled={bulkWorking || selected.size === 0}
              onClick={() => {
                void runBulkApply([...selected], false);
              }}
            >
              Aplicar selección
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={bulkWorking || filteredProducts.length === 0}
              onClick={() => {
                void runBulkApply(
                  filteredProducts.map((p) => p.master_id),
                  false,
                );
              }}
            >
              Aplicar filtrados ({filteredProducts.length})
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={bulkWorking || selected.size === 0}
              onClick={() => {
                void runBulkApply([...selected], true);
              }}
            >
              Quitar overrides
            </Button>
            {filteredProducts.length > pageItems.length && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={bulkWorking}
                onClick={() => setSelected(selectAllFiltered(filteredProducts))}
              >
                Sel. todos filtrados
              </Button>
            )}
            {bulkWorking && (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" aria-hidden="true" />
            )}
          </div>

          {bulkFeedback && <BulkLayoutFeedbackPanel feedback={bulkFeedback} />}

          {masterHighlightId && (
            <div className="flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-2 text-sm">
              <span>Filtro diagnóstico activo</span>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => setMasterHighlightId(null)}
              >
                Quitar filtro
              </Button>
            </div>
          )}

          <Card className="builder-panel overflow-hidden">
            <CardHeader className="pb-3 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CardTitle className="text-base">Productos</CardTitle>
                <p className="text-xs text-muted-foreground tabular-nums">
                  {filteredProducts.length} coincidencias · {summary.total_products} total
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <div className="relative flex-1 min-w-[200px]">
                  <Label htmlFor="presentation-product-search" className="sr-only">
                    Buscar producto
                  </Label>
                  <Search
                    className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground"
                    aria-hidden="true"
                  />
                  <Input
                    id="presentation-product-search"
                    name="productSearch"
                    className="pl-8"
                    placeholder="Buscar producto…"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                  />
                </div>
                <Label htmlFor="presentation-filter-has-variants" className="sr-only">
                  Filtrar por variantes
                </Label>
                <Select
                  id="presentation-filter-has-variants"
                  name="hasVariants"
                  className="w-36"
                  value={filter.hasVariants}
                  onChange={(e) =>
                    setFilter((f) => ({
                      ...f,
                      hasVariants: e.target.value as ProductFilterState["hasVariants"],
                    }))
                  }
                >
                  <option value="all">Variantes: todas</option>
                  <option value="yes">Con variantes</option>
                  <option value="no">Sin variantes</option>
                </Select>
                <Label htmlFor="presentation-filter-variant-attributes" className="sr-only">
                  Filtrar por atributos de variante
                </Label>
                <Select
                  id="presentation-filter-variant-attributes"
                  name="variantAttributes"
                  className="w-36"
                  value={filter.variantAttributes}
                  onChange={(e) =>
                    setFilter((f) => ({
                      ...f,
                      variantAttributes: e.target.value as ProductFilterState["variantAttributes"],
                    }))
                  }
                >
                  <option value="all">Atributos: todos</option>
                  <option value="0">0 atributos</option>
                  <option value="1">1 atributo</option>
                  <option value="2+">2+ atributos</option>
                </Select>
                <Label htmlFor="presentation-filter-status" className="sr-only">
                  Filtrar por estado de presentación
                </Label>
                <Select
                  id="presentation-filter-status"
                  name="status"
                  className="w-36"
                  value={filter.status}
                  onChange={(e) =>
                    setFilter((f) => ({
                      ...f,
                      status: e.target.value as ProductFilterState["status"],
                    }))
                  }
                >
                  <option value="all">Estado: todos</option>
                  <option value="fallback">Con fallback</option>
                  <option value="warning">Con aviso</option>
                  <option value="no_image">Sin imagen</option>
                  <option value="manual">Override manual</option>
                </Select>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <DataTableScroll>
                <table className="w-full caption-bottom text-sm table-fixed">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">
                        <input
                          id="presentation-select-page"
                          name="selectPage"
                          type="checkbox"
                          checked={pageAllSelected}
                          title="Selecciona filas de esta página"
                          onChange={() =>
                            setSelected((prev) => togglePageSelection(pageItems, prev))
                          }
                          aria-label="Seleccionar página actual"
                        />
                      </TableHead>
                      <TableHead className="w-8" />
                      <TableHead>Producto</TableHead>
                      <TableHead className="w-[120px]">Categoría</TableHead>
                      <TableHead className="w-[80px]">Var.</TableHead>
                      <TableHead className="w-[140px]">Layout</TableHead>
                      <TableHead className="w-[160px]">Estado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pageItems.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={7}
                          className="min-h-[8rem] h-32 text-center text-muted-foreground"
                        >
                          Ningún producto coincide con los filtros actuales. Prueba otro filtro o
                          quita el filtro diagnóstico.
                        </TableCell>
                      </TableRow>
                    ) : (
                      pageItems.map((product) => {
                        const expanded = expandedMasterId === product.master_id;
                        const manualId = manualOverrideMap.get(product.master_id);
                        return (
                          <Fragment key={product.master_id}>
                            <TableRow>
                              <TableCell>
                                <input
                                  id={`presentation-select-${product.master_id}`}
                                  name="selectedProduct"
                                  type="checkbox"
                                  checked={selected.has(product.master_id)}
                                  onChange={() =>
                                    setSelected((prev) =>
                                      toggleItemSelection(prev, product.master_id),
                                    )
                                  }
                                  aria-label={`Seleccionar ${product.master_name}`}
                                />
                              </TableCell>
                              <TableCell className="p-1">
                                {showManualControls && (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 w-7 p-0"
                                    aria-expanded={expanded}
                                    aria-label={expanded ? "Ocultar override" : "Editar override"}
                                    onClick={() =>
                                      setExpandedMasterId(expanded ? null : product.master_id)
                                    }
                                  >
                                    {expanded ? (
                                      <ChevronDown className="h-4 w-4" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4" />
                                    )}
                                  </Button>
                                )}
                              </TableCell>
                              <ProductLayoutRow
                                product={product}
                                layouts={layouts}
                                manualOverrideId={manualId}
                                highlighted={masterHighlightId === product.master_id}
                              />
                            </TableRow>
                            {showManualControls && expanded && (
                              <TableRow key={`${product.master_id}-detail`} className="bg-muted/20">
                                <TableCell colSpan={7} className="py-3">
                                  <div className="flex flex-wrap items-center gap-2 pl-8">
                                    <Label
                                      htmlFor={`presentation-override-${product.master_id}`}
                                      className="text-xs text-muted-foreground shrink-0"
                                    >
                                      Override manual
                                    </Label>
                                    <Select
                                      id={`presentation-override-${product.master_id}`}
                                      name={`override-${product.master_id}`}
                                      className="h-8 w-52 text-xs"
                                      value={manualId ?? ""}
                                      disabled={rowSaving === product.master_id}
                                      aria-label={`Override manual para ${product.master_name}`}
                                      onChange={(e) => {
                                        const value = e.target.value;
                                        if (value) {
                                          void saveManualLayout(product.master_id, value);
                                        } else {
                                          void clearManualLayout(product.master_id);
                                        }
                                      }}
                                    >
                                      <option value="">Automático</option>
                                      {layouts.map((layout) => (
                                        <option key={layout.id} value={layout.id}>
                                          {layout.name}
                                        </option>
                                      ))}
                                    </Select>
                                    {rowSaving === product.master_id && (
                                      <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            )}
                          </Fragment>
                        );
                      })
                    )}
                  </TableBody>
                </table>
              </DataTableScroll>
              <PaginationBar
                page={page}
                pageSize={pageSize}
                totalItems={filteredProducts.length}
                onPageChange={setPage}
                onPageSizeChange={(size) => {
                  setPageSize(size);
                  setPage(1);
                }}
              />
            </CardContent>
          </Card>

          <details className="builder-panel rounded-lg border border-border bg-card">
            <summary className="cursor-pointer px-5 py-4 text-base font-semibold">
              Layouts registrados ({layouts.length})
            </summary>
            <p className="px-5 pb-3 text-xs text-muted-foreground">
              Referencia de layouts disponibles. No es necesario abrirlo para el flujo habitual.
            </p>
            <div className="px-5 pb-5 grid gap-3 lg:grid-cols-3">
              {layouts.map((layout) => (
                <div
                  key={layout.id}
                  className="rounded-lg border border-border p-3 space-y-2 bg-muted/10"
                >
                  <LayoutMiniPreview layoutId={layout.id} />
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-sm">{layout.name}</p>
                    <Badge variant="outline" className="text-[10px]">
                      {layout.id}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">{layout.description}</p>
                  <p className="text-xs">{compatibilityLabel(layout.compatible_with)}</p>
                  <Badge variant="outline">{summary.by_layout[layout.id] ?? 0} productos</Badge>
                </div>
              ))}
            </div>
          </details>

          {!statusLoading && (
            <DiagnosticsPanel
              diagnostics={diagnostics}
              onSelectMaster={(masterId) => {
                const filterState = applyDiagnosticsFilter(masterId);
                setMasterHighlightId(filterState.masterHighlightId);
                setSearchInput(filterState.searchInput);
                setPage(filterState.page);
              }}
            />
          )}
          {statusLoading && (
            <p className="text-sm text-muted-foreground flex items-center gap-2 px-1">
              <Loader2 className="h-4 w-4 animate-spin shrink-0" aria-hidden="true" />
              Actualizando diagnósticos…
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
