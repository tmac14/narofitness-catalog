import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { AlertCircle, AlertTriangle, Eye, FileDown, Loader2, Trash2 } from "lucide-react";
import {
  addCatalogItem,
  bulkAddCatalogItems,
  deleteCatalog,
  createCatalogPdfExportJob,
  flattenCategories,
  getCatalog,
  getCatalogLayoutStatus,
  listCatalogExports,
  listCategories,
  type Category,
  patchCatalogItem,
  reorderCatalogItems,
  removeCatalogItem,
  searchVariants,
  updateCatalog,
} from "@/lib/api";
import { CatalogEditorSkeleton } from "@/components/LoadingPage";
import { CatalogCoverPanel } from "@/components/catalog-builder/CatalogCoverPanel";
import { CatalogEditorHeader } from "@/components/catalog-builder/CatalogEditorHeader";
import { CatalogPresentationBuilder } from "@/components/catalog-builder/CatalogPresentationBuilder";
import { ExportPdfDialog } from "@/components/catalog-builder/ExportPdfDialog";
import { PreviewWorkspace } from "@/components/catalog-builder/PreviewWorkspace";
import {
  SortableCatalogLines,
  type CatalogLineItem,
} from "@/components/catalog-builder/SortableCatalogLines";
import { buildExportPreflight, type ExportPreflight } from "@/lib/catalogLayout";
import {
  afterCatalogOptionsSavedForExport,
  afterCatalogOptionsSavedNormally,
  getUnsavedExportBlockFromFreshness,
  shouldAutoRefreshPreviewBeforeExport,
} from "@/lib/catalogPreviewFreshness";
import {
  CATALOG_PDF_EXPORT_QUEUED_DESCRIPTION,
  CATALOG_PDF_EXPORT_QUEUED_TOAST,
  queueCatalogPdfExportJob,
} from "@/lib/catalogExportJob";
import {
  isGeneralOptionsDirty,
  unsavedExportMessage,
  unsavedExportTab,
  type SaveCatalogOptionsConfig,
} from "@/lib/exportPdf";
import { useStatusBar } from "@/context/useStatusBar";
import { useRegisterTopBarRouteActions } from "@/context/useRegisterTopBarRouteActions";
import {
  applySortOrderUpdates,
  buildSortOrderUpdates,
  hasOrderChanged,
  mapReorderError,
  ORDER_SAVE_COPY,
  ORDER_SAVE_TOAST_ID,
  orderSaveButtonLabel,
} from "@/lib/catalogLines";
import { exportWarningsNavigationIntent } from "@/lib/editorPreview";
import { paginate, clampPage, PAGE_SIZE_OPTIONS } from "@/lib/pagination";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PaginationBar } from "@/components/ui/pagination";
import { DataTableScroll } from "@/components/ui/data-table";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  shouldAbortExportAfterPreviewError,
  shouldClearStaleOnPreviewError,
  shouldClearStaleOnPreviewReady,
  shouldClearStaleOnPreviewRefreshStart,
} from "@/lib/catalogPreviewLifecycle";
import type { PreviewPdfErrorDetail } from "@/lib/paginatedPreviewLoader";
import type { PreviewState } from "@/lib/previewState";

const DEFAULT_LINES_PAGE_SIZE = 50;

export default function CatalogEditorPage() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [catalog, setCatalog] = useState<Awaited<ReturnType<typeof getCatalog>> | null>(null);
  const [name, setName] = useState("");
  const [markup, setMarkup] = useState("");
  const [showIvaColumn, setShowIvaColumn] = useState(false);
  const [showDescriptionColumn, setShowDescriptionColumn] = useState(true);
  const [coverSubtitle, setCoverSubtitle] = useState("");
  const [search, setSearch] = useState("");
  const [supplierFilter, setSupplierFilter] = useState("");
  const [variants, setVariants] = useState<Awaited<ReturnType<typeof searchVariants>>["items"]>([]);
  const [variantPage, setVariantPage] = useState(1);
  const [variantPageSize, setVariantPageSize] = useState(DEFAULT_LINES_PAGE_SIZE);
  const [showPreview, setShowPreview] = useState(false);
  const [previewKey, setPreviewKey] = useState(0);
  const [previewState, setPreviewState] = useState<PreviewState>("idle");
  const [previewErrorDetail, setPreviewErrorDetail] = useState<PreviewPdfErrorDetail | null>(null);
  const [previewStale, setPreviewStale] = useState(false);
  const [pendingPreview, setPendingPreview] = useState(false);
  const [exportWarnings, setExportWarnings] = useState(0);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportPreflight, setExportPreflight] = useState<ExportPreflight | null>(null);
  const [categories, setCategories] = useState<{ id: string; label: string }[]>([]);
  const [categoryTree, setCategoryTree] = useState<Category[]>([]);
  const [bulkCategory, setBulkCategory] = useState("");
  const [exports, setExports] = useState<{ id: string; filename: string; exported_at: string }[]>(
    [],
  );
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [linesPage, setLinesPage] = useState(1);
  const [linesPageSize, setLinesPageSize] = useState(DEFAULT_LINES_PAGE_SIZE);
  const [activeTab, setActiveTab] = useState("general");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [localLines, setLocalLines] = useState<CatalogLineItem[]>([]);
  const [orderDirty, setOrderDirty] = useState(false);
  const [savingOrder, setSavingOrder] = useState(false);
  const [orderSaveError, setOrderSaveError] = useState<string | null>(null);
  const showSkeleton = useDelayedLoading(loading);
  const { setPanelOpen, refreshJobs } = useStatusBar();
  const exportAfterPreviewRef = useRef(false);
  const previewStaleRef = useRef(previewStale);
  const pendingPreviewRef = useRef(pendingPreview);

  useEffect(() => {
    previewStaleRef.current = previewStale;
  }, [previewStale]);

  useEffect(() => {
    pendingPreviewRef.current = pendingPreview;
  }, [pendingPreview]);

  function clearPreviewStaleState() {
    previewStaleRef.current = false;
    setPreviewStale(false);
  }

  function refreshPreview() {
    setPreviewKey((k) => k + 1);
    setPreviewState("loading");
    setPreviewErrorDetail(null);
    if (shouldClearStaleOnPreviewRefreshStart()) {
      clearPreviewStaleState();
    }
  }

  function handlePreviewReady() {
    setPreviewState("ready");
    setPreviewErrorDetail(null);
    if (shouldClearStaleOnPreviewReady()) {
      clearPreviewStaleState();
    }
    if (exportAfterPreviewRef.current) {
      exportAfterPreviewRef.current = false;
      void runExportAfterPreviewRefresh();
    }
  }

  function handlePreviewError(detail: PreviewPdfErrorDetail) {
    setPreviewState("error");
    setPreviewErrorDetail(detail);
    if (shouldAbortExportAfterPreviewError(exportAfterPreviewRef.current)) {
      exportAfterPreviewRef.current = false;
      toast.error(
        "No se pudo regenerar la vista previa PDF. Inténtalo de nuevo antes de exportar.",
      );
    } else {
      toast.error("No se pudo generar la vista previa PDF.");
    }
    if (shouldClearStaleOnPreviewError()) {
      clearPreviewStaleState();
    }
  }

  const markPreviewStale = useCallback(() => {
    previewStaleRef.current = true;
    setPreviewStale(true);
    if (showPreview && previewState === "ready") {
      setPreviewState("stale");
    }
  }, [showPreview, previewState]);

  const syncLocalLines = useCallback((c: Awaited<ReturnType<typeof getCatalog>>) => {
    const sorted = [...c.items].sort((a, b) => a.sort_order - b.sort_order);
    setLocalLines(
      sorted.map((item) => ({
        id: item.id,
        sku: item.sku,
        name: item.name,
        markup_percent: item.markup_percent,
        final_price_override: item.final_price_override,
        final_price: item.final_price,
        sort_order: item.sort_order,
      })),
    );
    setOrderDirty(false);
  }, []);

  const reload = useCallback((): void => {
    if (!id) return;
    setLoadError(null);
    void getCatalog(id)
      .then((c) => {
        setCatalog(c);
        setName(c.name);
        setMarkup(String(c.default_markup_percent));
        setShowIvaColumn(c.show_iva_column);
        setShowDescriptionColumn(c.show_description_column ?? true);
        setCoverSubtitle(c.cover_subtitle ?? "");
        syncLocalLines(c);
      })
      .catch((e) => {
        setLoadError(e instanceof Error ? e.message : "No se pudo cargar el catálogo");
        setCatalog(null);
      })
      .finally(() => setLoading(false));
    void listCatalogExports(id)
      .then((e) => setExports(e.items))
      .catch(() => {});
  }, [id, syncLocalLines]);

  const reloadCatalogAndPreview = useCallback(() => {
    reload();
    markPreviewStale();
  }, [markPreviewStale, reload]);

  const refreshExportWarnings = useCallback(async () => {
    if (!id) return;
    try {
      const status = await getCatalogLayoutStatus(id);
      const sev = status.summary.diagnostics_by_severity;
      setExportWarnings((sev?.critical ?? 0) + (sev?.warning ?? 0) + status.summary.fallback_count);
    } catch {
      // non-blocking
    }
  }, [id]);

  async function saveCatalogOptions(config?: SaveCatalogOptionsConfig): Promise<boolean> {
    if (!id || !catalog) return false;
    const pct = parseFloat(markup);
    if (Number.isNaN(pct)) {
      toast.error("Indica un aumento % válido");
      return false;
    }
    const dirty = isGeneralOptionsDirty(catalog, {
      name,
      markup,
      showIvaColumn,
      showDescriptionColumn,
      coverSubtitle,
    });
    if (!dirty) return true;

    setSaving(true);
    try {
      await updateCatalog(id, {
        name,
        default_markup_percent: pct,
        show_iva_column: showIvaColumn,
        show_description_column: showDescriptionColumn,
        cover_subtitle: coverSubtitle.trim() || null,
      });
      reload();
      const postSave = config?.skipPreviewRefresh
        ? afterCatalogOptionsSavedForExport(showPreview)
        : afterCatalogOptionsSavedNormally(showPreview);
      if (postSave === "refresh") {
        refreshPreview();
      } else if (postSave === "markStale") {
        markPreviewStale();
      }
      return true;
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error al guardar");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function runExportPdf() {
    if (!id) return;
    setExportingPdf(true);
    try {
      const result = await queueCatalogPdfExportJob(id, {
        createJob: createCatalogPdfExportJob,
      });
      if (!result.ok) {
        toast.error(result.message);
        return;
      }
      toast.success(CATALOG_PDF_EXPORT_QUEUED_TOAST, {
        description: CATALOG_PDF_EXPORT_QUEUED_DESCRIPTION,
      });
      setExportDialogOpen(false);
      setPanelOpen(true);
      void refreshJobs();
    } finally {
      setExportingPdf(false);
    }
  }

  async function runExportAfterPreviewRefresh() {
    if (!id) return;
    if (!(await saveCatalogOptions({ skipPreviewRefresh: true }))) return;
    await continueExportPreflight();
  }

  async function continueExportPreflight() {
    if (!id) return;
    try {
      const status = await getCatalogLayoutStatus(id);
      const preflight = buildExportPreflight(
        {
          summary: status.summary,
          diagnostics: status.diagnostics.map((d) => ({
            type: d.type as "fallback" | "no_image" | "no_category" | "incomplete_variants",
            severity: d.severity as "critical" | "warning" | "info",
            master_id: d.master_id,
            master_name: d.master_name,
            message: d.message,
          })),
        },
        {
          previewStale: previewStaleRef.current,
          pendingPreview: pendingPreviewRef.current,
        },
      );

      if (preflight.safeToExport) {
        await runExportPdf();
        return;
      }

      setExportPreflight(preflight);
      setExportDialogOpen(true);
    } catch {
      await runExportPdf();
    }
  }

  async function handleExportPdf() {
    if (!id) return;

    const unsavedBlock = getUnsavedExportBlockFromFreshness({
      previewStale,
      pendingPresentation: pendingPreview,
      orderDirty,
    });
    if (unsavedBlock) {
      toast.error(unsavedExportMessage(unsavedBlock));
      setActiveTab(unsavedExportTab(unsavedBlock));
      if (showPreview) setShowPreview(false);
      return;
    }

    if (
      shouldAutoRefreshPreviewBeforeExport({
        previewStale,
        pendingPresentation: pendingPreview,
        orderDirty,
      })
    ) {
      setShowPreview(true);
      exportAfterPreviewRef.current = true;
      refreshPreview();
      return;
    }

    if (previewStaleRef.current) {
      clearPreviewStaleState();
    }

    if (!(await saveCatalogOptions({ skipPreviewRefresh: true }))) return;

    await continueExportPreflight();
  }

  const handleTogglePreview = useCallback(() => {
    if (showPreview) setShowPreview(false);
    else {
      setShowPreview(true);
      if (previewState === "idle" || previewState === "error") {
        refreshPreview();
      } else if (previewStale || previewState === "stale") {
        setPreviewState("stale");
      }
    }
  }, [previewState, previewStale, showPreview]);

  useRegisterTopBarRouteActions(
    showPreview || !catalog
      ? []
      : [
          {
            id: "preview",
            label: "Vista previa",
            icon: Eye,
            onClick: handleTogglePreview,
          },
          {
            id: "export-pdf",
            label: "Exportar PDF",
            icon: FileDown,
            onClick: () => {
              void handleExportPdf();
            },
            disabled: exportingPdf,
          },
        ],
  );

  async function saveLineOrder() {
    if (!id || !catalog || savingOrder) return;
    const serverSorted = [...catalog.items].sort((a, b) => a.sort_order - b.sort_order);
    const updates = buildSortOrderUpdates(localLines);
    setOrderSaveError(null);
    setSavingOrder(true);
    try {
      const result = await applySortOrderUpdates(updates, serverSorted, (items) =>
        reorderCatalogItems(id, items),
      );
      if (result.skipped) {
        toast.info(ORDER_SAVE_COPY.toastNoop, { id: ORDER_SAVE_TOAST_ID });
        setOrderDirty(false);
        return;
      }
      toast.success(ORDER_SAVE_COPY.toastSuccess, { id: ORDER_SAVE_TOAST_ID });
      reloadCatalogAndPreview();
    } catch (e) {
      const message = mapReorderError(e);
      setOrderSaveError(message);
      toast.error(message, { id: ORDER_SAVE_TOAST_ID });
    } finally {
      setSavingOrder(false);
    }
  }

  function resetLineOrder() {
    setOrderSaveError(null);
    if (catalog) syncLocalLines(catalog);
  }

  function handleCoverMediaChanged() {
    if (showPreview) {
      refreshPreview();
    } else {
      markPreviewStale();
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      reload();
      void listCategories()
        .then((c) => {
          setCategoryTree(c);
          setCategories(flattenCategories(c));
        })
        .catch(() => {
          setCategoryTree([]);
          setCategories([]);
        });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [id, reload]);

  useEffect(() => {
    if (activeTab !== "presentation" || !id || !catalog) return;
    const timer = window.setTimeout(() => {
      void refreshExportWarnings();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [activeTab, catalog, id, refreshExportWarnings]);

  useEffect(() => {
    const t = setTimeout(() => {
      if (!id) return;
      void searchVariants({
        q: search || undefined,
        supplier_id: supplierFilter || undefined,
        exclude_catalog_id: id,
      })
        .then((d) => {
          setVariants(d.items);
          setVariantPage(1);
        })
        .catch(() => {
          setVariants([]);
        });
    }, 300);
    return () => clearTimeout(t);
  }, [search, supplierFilter, id]);

  useEffect(() => {
    if (!catalog) return;
    const serverSorted = [...catalog.items].sort((a, b) => a.sort_order - b.sort_order);
    const nextOrderDirty = hasOrderChanged(
      serverSorted.map((i) => ({ id: i.id, sort_order: i.sort_order })),
      localLines.map((i) => ({ id: i.id, sort_order: i.sort_order })),
    );
    const timer = window.setTimeout(() => {
      setOrderDirty(nextOrderDirty);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [localLines, catalog]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLinesPage((p) => clampPage(p, localLines.length, linesPageSize));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [localLines.length, linesPageSize]);

  const linesPageItems = useMemo(
    () => paginate(localLines, linesPage, linesPageSize),
    [localLines, linesPage, linesPageSize],
  );

  const variantPageItems = useMemo(
    () => paginate(variants, variantPage, variantPageSize),
    [variants, variantPage, variantPageSize],
  );

  function handlePageReorder(pageItems: CatalogLineItem[]) {
    setOrderSaveError(null);
    const start = (linesPage - 1) * linesPageSize;
    const next = [...localLines];
    next.splice(start, pageItems.length, ...pageItems);
    setLocalLines(next.map((item, index) => ({ ...item, sort_order: index })));
    markPreviewStale();
  }

  if (!id) return null;

  if (loadError && !catalog && !showSkeleton) {
    return (
      <Card className="max-w-lg mx-auto mt-12">
        <CardContent className="py-10 text-center space-y-4">
          <p className="font-medium text-destructive">Error al cargar el catálogo</p>
          <p className="text-sm text-muted-foreground">{loadError}</p>
          <Button
            type="button"
            onClick={() => {
              setLoading(true);
              reload();
            }}
          >
            Reintentar
          </Button>
        </CardContent>
      </Card>
    );
  }

  const mainContent =
    showSkeleton || !catalog ? (
      <CatalogEditorSkeleton />
    ) : (
      <>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full sm:w-auto">
            <TabsTrigger value="general" className="min-w-[5.5rem]">
              General
            </TabsTrigger>
            <TabsTrigger value="presentation" className="min-w-[6.5rem]">
              Presentación
            </TabsTrigger>
            <TabsTrigger value="products" className="min-w-[5.5rem] gap-1.5">
              Productos
              <Badge variant="secondary" className="h-5 px-1.5 text-[10px] tabular-nums">
                {catalog.items.length}
              </Badge>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="editor-tab-panel">
            {catalog &&
              isGeneralOptionsDirty(catalog, {
                name,
                markup,
                showIvaColumn,
                showDescriptionColumn,
                coverSubtitle,
              }) && (
                <div className="mb-4 rounded-lg border border-warning/40 bg-warning/10 px-3 py-3 text-sm text-warning">
                  Opciones del PDF modificadas sin guardar. Guarda los cambios para actualizar la
                  vista previa y el PDF exportado.
                </div>
              )}
            <Card className="mb-6 builder-panel">
              <CardHeader>
                <CardTitle className="text-base">Opciones del PDF</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap items-end gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="catalog-name">Nombre del catálogo</Label>
                    <Input
                      id="catalog-name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="max-w-[240px]"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="catalog-markup">Aumento sobre precio base (%)</Label>
                    <Input
                      id="catalog-markup"
                      type="number"
                      step="0.01"
                      value={markup}
                      onChange={(e) => setMarkup(e.target.value)}
                      className="w-28"
                    />
                  </div>
                </div>
                <div className="space-y-3 border-t border-border pt-4">
                  <div className="flex items-center gap-2">
                    <input
                      id="show-iva-column"
                      type="checkbox"
                      className="rounded border-border"
                      checked={showIvaColumn}
                      onChange={(e) => setShowIvaColumn(e.target.checked)}
                    />
                    <Label htmlFor="show-iva-column" className="cursor-pointer font-normal">
                      Mostrar columna PVP + IVA
                    </Label>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <input
                        id="show-description-column"
                        type="checkbox"
                        className="rounded border-border"
                        checked={showDescriptionColumn}
                        onChange={(e) => setShowDescriptionColumn(e.target.checked)}
                      />
                      <Label
                        htmlFor="show-description-column"
                        className="cursor-pointer font-normal"
                      >
                        Mostrar columna Descripción
                      </Label>
                    </div>
                    <p className="pl-6 text-xs text-muted-foreground">
                      Incluye descripciones y detalles destacados del producto en las tablas de
                      productos simples.
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    disabled={saving}
                    onClick={() => {
                      void (async () => {
                        if (await saveCatalogOptions()) {
                          toast.success("Opciones guardadas");
                        }
                      })();
                    }}
                  >
                    {saving ? "Guardando…" : "Guardar opciones"}
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={() => setDeleteDialogOpen(true)}
                  >
                    <Trash2 className="h-4 w-4" />
                    Eliminar
                  </Button>
                </div>
              </CardContent>
            </Card>

            {id && (
              <CatalogCoverPanel
                catalogId={id}
                coverImageUrl={catalog.cover_image_url}
                coverSubtitle={coverSubtitle}
                onCoverSubtitleChange={setCoverSubtitle}
                onCoverImageUpdated={(url) =>
                  setCatalog((current) =>
                    current ? { ...current, cover_image_url: url } : current,
                  )
                }
                onCoverMediaChanged={handleCoverMediaChanged}
              />
            )}

            {exports.length > 0 && (
              <Card className="mb-6 builder-panel">
                <CardHeader>
                  <CardTitle className="text-sm">Exportaciones recientes</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm space-y-1">
                    {exports.map((e) => (
                      <li key={e.id}>
                        {new Date(e.exported_at).toLocaleString("es-ES")} — {e.filename}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent
            value="presentation"
            className="editor-tab-panel editor-tab-panel--presentation"
          >
            <CatalogPresentationBuilder
              catalogId={id}
              layoutMode={catalog.layout_mode ?? "automatic"}
              uniformLayoutId={catalog.uniform_layout_id}
              productLayouts={catalog.product_layouts ?? []}
              sectionCovers={catalog.section_covers ?? []}
              categoryTree={categoryTree}
              onSectionCoversUpdated={reload}
              onCoverMediaChanged={handleCoverMediaChanged}
              onConfigSaved={() => {
                reload();
                void refreshExportWarnings();
              }}
              onPreviewStale={markPreviewStale}
              onPendingPreviewChange={setPendingPreview}
            />
          </TabsContent>

          <TabsContent value="products">
            {orderDirty && (
              <div
                className="mb-4 flex flex-wrap items-start gap-3 rounded-lg border border-warning/40 bg-warning/10 px-3 py-3 text-sm"
                role="status"
                aria-live="polite"
                aria-busy={savingOrder}
              >
                <AlertTriangle
                  className="h-4 w-4 shrink-0 text-warning mt-0.5"
                  aria-hidden="true"
                />
                <div className="flex-1 min-w-[12rem] space-y-1">
                  <p className="font-medium text-foreground">{ORDER_SAVE_COPY.bannerTitle}</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {savingOrder
                      ? ORDER_SAVE_COPY.bannerHintSaving
                      : ORDER_SAVE_COPY.bannerHintIdle}
                  </p>
                  {orderSaveError && (
                    <p className="text-xs text-destructive flex items-start gap-1.5 pt-0.5">
                      <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" aria-hidden="true" />
                      <span>{orderSaveError}</span>
                    </p>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  {savingOrder && (
                    <Loader2
                      className="h-4 w-4 animate-spin text-muted-foreground"
                      aria-hidden="true"
                    />
                  )}
                  <Button
                    type="button"
                    size="sm"
                    variant="default"
                    disabled={savingOrder}
                    onClick={() => {
                      void saveLineOrder();
                    }}
                  >
                    {orderSaveButtonLabel(savingOrder)}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    disabled={savingOrder}
                    title={savingOrder ? ORDER_SAVE_COPY.discardDisabledTitle : undefined}
                    onClick={resetLineOrder}
                  >
                    {ORDER_SAVE_COPY.discardLabel}
                  </Button>
                </div>
              </div>
            )}
            <div className="grid gap-4 lg:grid-cols-2">
              <Card className="builder-panel overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-base">Líneas ({catalog.items.length})</CardTitle>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    El orden manual aplica solo a las líneas del catálogo (pestaña Productos). No
                    reordena masters de Presentación ni categorías. El arrastre afecta solo a la
                    página visible.
                  </p>
                </CardHeader>
                <CardContent className="p-0">
                  <SortableCatalogLines
                    items={linesPageItems}
                    defaultMarkup={markup}
                    disabled={savingOrder}
                    disabledReason={ORDER_SAVE_COPY.dndDisabledReason}
                    onReorder={handlePageReorder}
                    onRemove={(itemId) => {
                      void (async () => {
                        await removeCatalogItem(id, itemId);
                        reloadCatalogAndPreview();
                      })();
                    }}
                    onMarkupBlur={(itemId, value) => {
                      void patchCatalogItem(id, itemId, {
                        markup_percent: value === "" ? null : parseFloat(value),
                      }).then(() => {
                        reloadCatalogAndPreview();
                      });
                    }}
                    onPriceBlur={(itemId, value) => {
                      void patchCatalogItem(id, itemId, {
                        final_price_override: value === "" ? null : parseFloat(value),
                      }).then(() => {
                        reloadCatalogAndPreview();
                      });
                    }}
                  />
                  <PaginationBar
                    page={linesPage}
                    pageSize={linesPageSize}
                    totalItems={localLines.length}
                    onPageChange={setLinesPage}
                    onPageSizeChange={(size) => {
                      setLinesPageSize(size);
                      setLinesPage(1);
                    }}
                    pageSizeOptions={[...PAGE_SIZE_OPTIONS]}
                  />
                </CardContent>
              </Card>

              <Card className="builder-panel overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-base">Añadir variante</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Buscar SKU o nombre"
                  />
                  <Input
                    value={supplierFilter}
                    onChange={(e) => setSupplierFilter(e.target.value)}
                    placeholder="ID proveedor (opcional)"
                  />
                  <DataTableScroll maxHeight="max-h-[280px]">
                    <table className="w-full caption-bottom text-sm table-fixed">
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[120px]">SKU</TableHead>
                          <TableHead>Nombre</TableHead>
                          <TableHead className="w-12" />
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {variantPageItems.map((v) => (
                          <TableRow key={v.id}>
                            <TableCell className="truncate font-mono text-xs">{v.sku}</TableCell>
                            <TableCell className="truncate">{v.master_name}</TableCell>
                            <TableCell>
                              <Button
                                type="button"
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                  void (async () => {
                                    await addCatalogItem(id, v.id, catalog.items.length);
                                    reloadCatalogAndPreview();
                                  })();
                                }}
                                aria-label={`Añadir ${v.sku}`}
                              >
                                +
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </table>
                  </DataTableScroll>
                  <PaginationBar
                    page={variantPage}
                    pageSize={variantPageSize}
                    totalItems={variants.length}
                    onPageChange={setVariantPage}
                    onPageSizeChange={(size) => {
                      setVariantPageSize(size);
                      setVariantPage(1);
                    }}
                    pageSizeOptions={[25, 50]}
                  />
                  <div className="space-y-2 pt-2 border-t border-border">
                    <Label htmlFor="bulk-cat">Añadir categoría completa</Label>
                    <Select
                      id="bulk-cat"
                      value={bulkCategory}
                      onChange={(e) => setBulkCategory(e.target.value)}
                    >
                      <option value="">— categoría —</option>
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.label}
                        </option>
                      ))}
                    </Select>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        void (async () => {
                          if (!bulkCategory) return;
                          const r = await bulkAddCatalogItems(id, bulkCategory);
                          toast.success(`Añadidas ${r.created} variantes.`);
                          reloadCatalogAndPreview();
                        })();
                      }}
                    >
                      Añadir categoría
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {exportPreflight && (
          <ExportPdfDialog
            open={exportDialogOpen}
            onOpenChange={setExportDialogOpen}
            catalogName={name}
            preflight={exportPreflight}
            isExporting={exportingPdf}
            onExport={() => {
              void runExportPdf();
            }}
            onRefreshPreview={() => {
              setShowPreview(true);
              exportAfterPreviewRef.current = false;
              refreshPreview();
            }}
          />
        )}

        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>¿Eliminar catálogo?</DialogTitle>
              <DialogDescription>
                Se eliminará <strong>{name}</strong> y sus líneas. Esta acción no se puede deshacer.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setDeleteDialogOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={deleting}
                onClick={() => {
                  void (async () => {
                    setDeleting(true);
                    try {
                      await deleteCatalog(id);
                      nav("/catalogs");
                    } catch (e) {
                      toast.error(e instanceof Error ? e.message : "Error al eliminar");
                    } finally {
                      setDeleting(false);
                    }
                  })();
                }}
              >
                {deleting ? "Eliminando…" : "Eliminar catálogo"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </>
    );

  return (
    <div className="catalog-editor-page">
      {!showSkeleton && catalog && (
        <CatalogEditorHeader
          catalogName={catalog.name}
          productCount={catalog.items.length}
          showPreview={showPreview}
          exportingPdf={exportingPdf}
          exportWarnings={exportWarnings}
          hideInlineRouteActions={!showPreview}
          onTogglePreview={handleTogglePreview}
          onExportPdf={() => {
            void handleExportPdf();
          }}
        />
      )}

      <div className="editor-workspace">
        {showPreview && catalog ? (
          <PreviewWorkspace
            catalogId={id}
            previewKey={previewKey}
            previewState={previewState}
            previewErrorDetail={previewErrorDetail}
            exportWarnings={exportWarnings}
            pendingPreview={pendingPreview}
            exportingPdf={exportingPdf}
            onRefresh={refreshPreview}
            onLoad={handlePreviewReady}
            onError={handlePreviewError}
            onClose={() => setShowPreview(false)}
            onExportPdf={() => {
              void handleExportPdf();
            }}
            onExportWarningsClick={() => {
              const nav = exportWarningsNavigationIntent();
              if (nav.closePreview) setShowPreview(false);
              setActiveTab(nav.targetTab);
            }}
          />
        ) : (
          mainContent
        )}
      </div>
    </div>
  );
}
