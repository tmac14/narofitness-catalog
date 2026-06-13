import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { FileUp, Upload, Loader2 } from "lucide-react";
import {
  labelAction,
  labelReason,
  labelStatus,
  STATUS_LABELS,
  ACTION_LABELS,
} from "@/lib/importLabels";
import { ErrorState } from "@/components/ErrorState";
import {
  confirmImport,
  diffPriceLists,
  listImportProfiles,
  listPriceLists,
  listSuppliers,
  previewImport,
  type ImportProfile,
  type ImportRow,
  type Supplier,
} from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SourceCategoryMappingPanel } from "@/components/import/SourceCategoryMappingPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";

function updateRow(rows: ImportRow[], index: number, patch: Partial<ImportRow>): ImportRow[] {
  return rows.map((r) => (rowKey(r) === index ? { ...r, ...patch } : r));
}

function updateRows(rows: ImportRow[], indices: number[], patch: Partial<ImportRow>): ImportRow[] {
  const set = new Set(indices);
  return rows.map((r) => (set.has(rowKey(r)) ? { ...r, ...patch } : r));
}

function rowKey(r: ImportRow): number {
  return r.source_row_index ?? r.row_index ?? 0;
}

const BLOCKING_REASONS = new Set([
  "false_family_pattern",
  "low_grouping_confidence",
  "regex_fallback_1_1",
  "unmapped_category",
  "spec_validation_failed",
  "duplicate_sku",
  "missing_sku",
  "missing_price",
  "missing_name",
  "unknown_spec_key",
]);

function hasBlockingReasons(r: ImportRow): boolean {
  return (r.review_reasons || []).some((code) => BLOCKING_REASONS.has(code));
}

function isConfirmableRow(r: ImportRow, allowNeedsReview: boolean): boolean {
  if (!r.sku || !r.price_amount || r.review_status === "imported") return false;
  if (hasBlockingReasons(r)) return false;
  if (r.review_status === "needs_review") return allowNeedsReview;
  return r.review_status === "pending" || r.review_status === "confirmed";
}

export default function ImportPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [profiles, setProfiles] = useState<ImportProfile[]>([]);
  const [supplierId, setSupplierId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [rows, setRows] = useState<ImportRow[]>([]);
  const [batchId, setBatchId] = useState("");
  const [filename, setFilename] = useState("");
  const [stats, setStats] = useState<Record<string, number>>({});
  const [actionStats, setActionStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [actionFilter, setActionFilter] = useState("all");
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [effectiveDate, setEffectiveDate] = useState(new Date().toISOString().slice(0, 10));
  const [bulkMasterKey, setBulkMasterKey] = useState("");
  const [bulkMasterName, setBulkMasterName] = useState("");
  const [allowNeedsReview, setAllowNeedsReview] = useState(false);
  const [importStep, setImportStep] = useState<"mapping" | "rows">("mapping");
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<{ title: string; description: string } | null>(
    null,
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void listSuppliers()
        .then((s) => {
          setSuppliers(s);
          const fdl = s.find((x) => x.code === "FDL") || s[0];
          if (fdl) setSupplierId(fdl.id);
        })
        .catch((error: unknown) => {
          toast.error(String(error));
          setSuppliers([]);
        });
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!supplierId) return;
    const timer = window.setTimeout(() => {
      void listImportProfiles(supplierId)
        .then((p) => {
          setProfiles(p);
          const def = p.find((x) => x.is_default) || p[0];
          if (def) setProfileId(def.id);
        })
        .catch((error: unknown) => {
          toast.error(String(error));
          setProfiles([]);
        });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [supplierId]);

  async function onFile(file: File) {
    if (!supplierId || !profileId) {
      toast.error("Seleccione proveedor y perfil de importación.");
      return;
    }
    setLoading(true);
    setInlineError(null);
    setActionError(null);
    setSelected(new Set());
    try {
      const data = await previewImport(file, supplierId, profileId);
      setBatchId(data.batch_id);
      setRows(data.rows.map((r) => ({ ...r, row_index: r.source_row_index })));
      setFilename(data.filename);
      setStats(data.stats);
      setActionStats(data.action_stats || {});
      setImportStep("mapping");
      toast.success(`Vista previa: ${data.rows.length} filas`);
    } catch (e) {
      const msg = String(e);
      setInlineError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function onConfirm() {
    if (!batchId) {
      toast.error("No hay lote de importación. Suba un PDF primero.");
      return;
    }
    const selectedExplicit = selected.size > 0;
    const confirmRows = selectedExplicit
      ? rows.filter((r) => selected.has(rowKey(r)) && isConfirmableRow(r, allowNeedsReview))
      : rows.filter((r) => isConfirmableRow(r, false));
    if (confirmRows.length === 0) {
      const msg =
        "No hay filas listas para importar. Revise el estado o seleccione filas pendientes.";
      setActionError({
        title: "No se puede confirmar todavía",
        description: `${msg} Si acaba de cambiar categorías, vuelva al paso 1 y pulse «Aplicar cambios de categorías».`,
      });
      toast.error(msg);
      return;
    }
    const rowIds = confirmRows.map((r) => r.id);
    setLoading(true);
    setActionError(null);
    try {
      const res = await confirmImport({
        batch_id: batchId,
        supplier_id: supplierId,
        import_profile_id: profileId,
        row_ids: rowIds.length ? rowIds : undefined,
        effective_date: effectiveDate,
        allow_needs_review: selectedExplicit && allowNeedsReview,
      });
      let summary = `Importado: ${res.entries_created} precios · ${res.variants_created} variantes nuevas · ${res.variants_updated} actualizaciones · ${res.masters_created} familias nuevas`;
      const blockedRows = res.rows_blocked ?? 0;
      if (blockedRows > 0) {
        summary += ` · ${blockedRows} filas bloqueadas`;
      }
      try {
        const lists = await listPriceLists();
        if (lists.length >= 2) {
          const diff = await diffPriceLists(lists[1].id, lists[0].id, {
            direction: "up",
            min_delta_pct: 5,
          });
          summary += ` · ${diff.items.length} SKUs con subida ≥5% vs lista anterior`;
        }
      } catch {
        /* optional */
      }
      toast.success(summary, { duration: 8000 });
    } catch (e) {
      const msg = String(e);
      setActionError({
        title: "No se pudo completar la importación",
        description: `${msg} Revise las filas marcadas para revisar e inténtelo de nuevo.`,
      });
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      if (statusFilter !== "all" && (r.status ?? r.review_status) !== statusFilter) return false;
      if (actionFilter !== "all" && r.import_action !== actionFilter) return false;
      return true;
    });
  }, [rows, statusFilter, actionFilter]);

  const displayRows = filtered.slice(0, 500);
  const truncated = filtered.length > 500;
  const editingRow = editingIndex != null ? rows.find((r) => rowKey(r) === editingIndex) : null;

  function toggleSelect(idx: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }

  function selectFiltered() {
    setSelected(new Set(displayRows.map((r) => rowKey(r))));
  }

  function bulkMergeMaster() {
    if (!bulkMasterKey.trim()) {
      toast.error("Indique la clave de familia para agrupar las filas seleccionadas.");
      return;
    }
    const ids = [...selected];
    setRows(
      updateRows(rows, ids, {
        master_key: bulkMasterKey.trim(),
        master_name: bulkMasterName.trim() || bulkMasterKey.trim(),
        grouping_locked: true,
      }),
    );
    toast.success(`Agrupadas ${ids.length} filas en la familia «${bulkMasterKey}».`);
  }

  function bulkForceOneToOne() {
    const ids = new Set(selected);
    setRows(
      rows.map((r) =>
        ids.has(rowKey(r))
          ? { ...r, master_key: r.sku || r.master_key, master_name: r.name, grouping_locked: true }
          : r,
      ),
    );
    toast.success(`Forzado 1:1 en ${ids.size} filas.`);
  }

  return (
    <div>
      <PageHeader
        title="Importar tarifa PDF"
        description="Suba el PDF del proveedor, asigne categorías y revise las filas antes de confirmar. Si el producto ya existe, solo se guarda el nuevo precio."
        icon={FileUp}
      />

      {inlineError && (
        <div className="mb-4">
          <ErrorState
            title="No se pudo procesar el archivo"
            description={inlineError}
            action={
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => setInlineError(null)}
              >
                Cerrar
              </Button>
            }
            className="py-6 rounded-lg border border-destructive/30 bg-destructive/5"
          />
        </div>
      )}

      {batchId && (
        <p className="text-sm text-muted-foreground mb-2">
          Lote: {batchId.slice(0, 8)}… · {filename}
        </p>
      )}

      <Card className="mb-4 toolbar-card">
        <CardContent className="p-4 flex flex-wrap items-end gap-4">
          <div className="space-y-2">
            <Label htmlFor="supplier">Proveedor</Label>
            <Select
              id="supplier"
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
            >
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.code})
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="profile">Perfil</Label>
            <Select id="profile" value={profileId} onChange={(e) => setProfileId(e.target.value)}>
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="effective-date">Fecha efectiva</Label>
            <Input
              id="effective-date"
              type="date"
              value={effectiveDate}
              onChange={(e) => setEffectiveDate(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card
        className="dropzone mb-4 cursor-pointer relative"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (loading) return;
          const f = e.dataTransfer.files[0];
          if (f) {
            void onFile(f);
          }
        }}
        aria-busy={loading}
      >
        {loading && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 rounded-lg bg-background/80">
            <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
            <p className="text-sm font-medium">Procesando PDF…</p>
          </div>
        )}
        <CardContent className="p-8 flex flex-col items-center gap-3">
          <Upload className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
          <p className="font-medium">Arrastre el PDF aquí o seleccione un archivo</p>
          <p className="text-sm text-muted-foreground">
            Formato admitido: PDF con texto (no escaneado)
          </p>
          <Label htmlFor="import-file" className="sr-only">
            Seleccionar archivo PDF
          </Label>
          <Input
            id="import-file"
            type="file"
            accept=".pdf"
            className="max-w-xs"
            disabled={loading}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) {
                void onFile(f);
              }
            }}
          />
        </CardContent>
      </Card>

      {(Object.keys(stats).length > 0 || Object.keys(actionStats).length > 0) && (
        <Card className="mb-4">
          <CardContent className="p-4 flex flex-wrap gap-2">
            {Object.entries(stats).map(([k, v]) => (
              <button
                key={k}
                type="button"
                className={`stat-pill status-${k} ${statusFilter === k ? "active" : ""}`}
                onClick={() => setStatusFilter(statusFilter === k ? "all" : k)}
                aria-pressed={statusFilter === k}
                aria-label={`Filtrar por ${labelStatus(k)}: ${v}`}
              >
                {labelStatus(k)}: {v}
              </button>
            ))}
            {Object.entries(actionStats).map(([k, v]) => (
              <button
                key={`a-${k}`}
                type="button"
                className={`stat-pill ${actionFilter === k ? "active" : ""}`}
                onClick={() => setActionFilter(actionFilter === k ? "all" : k)}
                aria-pressed={actionFilter === k}
                aria-label={`Filtrar por ${labelAction(k)}: ${v}`}
              >
                {labelAction(k)}: {v}
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {editingRow && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Editar fila #{editingRow.row_index}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="form-grid">
              <div className="space-y-2">
                <Label>Referencia (SKU)</Label>
                <Input
                  value={editingRow.sku ?? ""}
                  onChange={(e) => setRows(updateRow(rows, editingIndex!, { sku: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Precio</Label>
                <Input
                  value={editingRow.price_amount ?? ""}
                  onChange={(e) =>
                    setRows(updateRow(rows, editingIndex!, { price_amount: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>EAN</Label>
                <Input
                  value={editingRow.ean ?? ""}
                  onChange={(e) => setRows(updateRow(rows, editingIndex!, { ean: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Marca</Label>
                <Input
                  value={editingRow.brand ?? ""}
                  onChange={(e) =>
                    setRows(updateRow(rows, editingIndex!, { brand: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-2 span-2">
                <Label>Nombre</Label>
                <Input
                  value={editingRow.name ?? ""}
                  onChange={(e) =>
                    setRows(updateRow(rows, editingIndex!, { name: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-2 span-2">
                <Label>Categoría</Label>
                <Input
                  value={editingRow.category_path ?? ""}
                  onChange={(e) =>
                    setRows(updateRow(rows, editingIndex!, { category_path: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Clave de familia</Label>
                <Input
                  value={editingRow.master_key ?? ""}
                  onChange={(e) =>
                    setRows(
                      updateRow(rows, editingIndex!, {
                        master_key: e.target.value,
                        grouping_locked: true,
                      }),
                    )
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Nombre de familia</Label>
                <Input
                  value={editingRow.master_name ?? ""}
                  onChange={(e) =>
                    setRows(
                      updateRow(rows, editingIndex!, {
                        master_name: e.target.value,
                        grouping_locked: true,
                      }),
                    )
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Nombre de variante</Label>
                <Input
                  value={editingRow.display_name ?? ""}
                  onChange={(e) =>
                    setRows(updateRow(rows, editingIndex!, { display_name: e.target.value }))
                  }
                />
              </div>
            </div>
            <Button type="button" onClick={() => setEditingIndex(null)}>
              Cerrar
            </Button>
          </CardContent>
        </Card>
      )}

      {rows.length > 0 && (
        <>
          <Card className="mb-4 border-border bg-card">
            <CardContent className="p-4 space-y-3">
              <p className="text-sm font-medium">Pasos de la importación</p>
              <ol className="text-sm text-muted-foreground list-decimal list-inside space-y-1">
                <li>Suba el PDF del proveedor (arriba).</li>
                <li>Asigne cada categoría del PDF a una categoría suya (paso 1).</li>
                <li>
                  Pulse <strong>Aplicar cambios de categorías</strong> para actualizar las filas.
                </li>
                <li>Revise las filas en el paso 2.</li>
                <li>Confirme la importación cuando todo esté correcto.</li>
              </ol>
              <div
                role="tablist"
                aria-label="Pasos de importación"
                className="flex flex-wrap gap-2"
              >
                <Button
                  type="button"
                  role="tab"
                  id="import-tab-mapping"
                  aria-selected={importStep === "mapping"}
                  aria-controls="import-panel-mapping"
                  variant={importStep === "mapping" ? "default" : "secondary"}
                  onClick={() => setImportStep("mapping")}
                >
                  1. Asignar categorías
                </Button>
                <Button
                  type="button"
                  role="tab"
                  id="import-tab-rows"
                  aria-selected={importStep === "rows"}
                  aria-controls="import-panel-rows"
                  variant={importStep === "rows" ? "default" : "secondary"}
                  onClick={() => setImportStep("rows")}
                >
                  2. Revisar filas
                </Button>
              </div>
            </CardContent>
          </Card>

          {importStep === "mapping" && batchId && (
            <div role="tabpanel" id="import-panel-mapping" aria-labelledby="import-tab-mapping">
              <SourceCategoryMappingPanel
                batchId={batchId}
                supplierId={supplierId}
                importProfileId={profileId}
                onRowsUpdated={(updated) => setRows(updated)}
              />
            </div>
          )}

          {importStep === "rows" && (
            <div role="tabpanel" id="import-panel-rows" aria-labelledby="import-tab-rows">
              {actionError && (
                <div className="mb-4">
                  <ErrorState
                    title={actionError.title}
                    description={actionError.description}
                    action={
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setActionError(null)}
                      >
                        Cerrar
                      </Button>
                    }
                    className="py-6 rounded-lg border border-destructive/30 bg-destructive/5"
                  />
                </div>
              )}
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <div className="space-y-1">
                  <Label htmlFor="status-filter" className="text-xs">
                    Estado
                  </Label>
                  <Select
                    id="status-filter"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-auto min-w-[160px]"
                  >
                    <option value="all">Todos</option>
                    {Object.entries(STATUS_LABELS).map(([code, label]) => (
                      <option key={code} value={code}>
                        {label}
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="action-filter" className="text-xs">
                    Acción
                  </Label>
                  <Select
                    id="action-filter"
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                    className="w-auto min-w-[160px]"
                  >
                    <option value="all">Todas</option>
                    {Object.entries(ACTION_LABELS).map(([code, label]) => (
                      <option key={code} value={code}>
                        {label}
                      </option>
                    ))}
                  </Select>
                </div>
                <Button type="button" variant="secondary" onClick={selectFiltered}>
                  Seleccionar visibles
                </Button>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={allowNeedsReview}
                    onChange={(e) => setAllowNeedsReview(e.target.checked)}
                    aria-label="Permitir filas que requieren revisión al confirmar"
                  />
                  Incluir filas «Revisar» al confirmar
                </label>
                <Button
                  disabled={loading}
                  onClick={() => {
                    void onConfirm();
                  }}
                >
                  Confirmar importación
                </Button>
              </div>

              {selected.size > 0 && (
                <Card className="mb-4">
                  <CardContent className="p-4 flex flex-wrap items-center gap-3">
                    <Badge variant="secondary">{selected.size} seleccionadas</Badge>
                    <Input
                      placeholder="Clave familia"
                      aria-label="Clave de familia"
                      value={bulkMasterKey}
                      onChange={(e) => setBulkMasterKey(e.target.value)}
                      className="max-w-[160px]"
                    />
                    <Input
                      placeholder="Nombre familia"
                      aria-label="Nombre de familia"
                      value={bulkMasterName}
                      onChange={(e) => setBulkMasterName(e.target.value)}
                      className="max-w-[160px]"
                    />
                    <Button type="button" variant="secondary" onClick={bulkMergeMaster}>
                      Agrupar en familia
                    </Button>
                    <Button type="button" variant="secondary" onClick={bulkForceOneToOne}>
                      Un producto por fila
                    </Button>
                  </CardContent>
                </Card>
              )}

              {truncated && (
                <div className="warning-panel mb-3" role="status">
                  <strong>Atención:</strong> solo se muestran 500 de {filtered.length} filas. Use
                  los filtros de estado o acción para ver un subconjunto más pequeño.
                </div>
              )}

              <Card>
                <CardContent className="p-0 max-h-[55vh] overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead></TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Acción</TableHead>
                        <TableHead>Motivos</TableHead>
                        <TableHead>Referencia</TableHead>
                        <TableHead>Familia</TableHead>
                        <TableHead>Variante</TableHead>
                        <TableHead>Precio</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {displayRows.map((r) => (
                        <TableRow
                          key={r.id}
                          className={`row-status-${r.status ?? r.review_status}`}
                        >
                          <TableCell>
                            <input
                              type="checkbox"
                              checked={selected.has(rowKey(r))}
                              onChange={() => toggleSelect(rowKey(r))}
                              className="mr-2"
                              aria-label={`Seleccionar fila ${r.sku || r.name}`}
                            />
                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              onClick={() => setEditingIndex(rowKey(r))}
                            >
                              Editar
                            </Button>
                          </TableCell>
                          <TableCell>{labelStatus(r.review_status || r.status)}</TableCell>
                          <TableCell>{labelAction(r.import_action)}</TableCell>
                          <TableCell className="muted-cell">
                            {(r.review_reasons || []).map((c) => labelReason(c)).join(", ")}
                          </TableCell>
                          <TableCell>{r.sku}</TableCell>
                          <TableCell className="muted-cell">
                            {r.master_name || r.master_key}
                          </TableCell>
                          <TableCell>{r.display_name || "—"}</TableCell>
                          <TableCell>{r.price_amount}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}

      {rows.length === 0 && !loading && (
        <EmptyState
          icon={FileUp}
          title="Sin vista previa"
          description="Suba un PDF para ver las filas a importar."
        />
      )}
    </div>
  );
}
