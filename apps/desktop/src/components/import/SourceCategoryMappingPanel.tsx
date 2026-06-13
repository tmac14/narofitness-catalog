import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ErrorState";
import {
  confirmTaxonomyMapping,
  getBatchSourceCategories,
  getCanonicalCategoryTree,
  ignoreSourceCategory,
  remapBatchTaxonomy,
  type CanonicalCategoryNode,
  type ImportRow,
  type SourceCategoryDiscovery,
} from "@/lib/api";
import { CanonicalCategoryTree } from "./CanonicalCategoryTree";
import { MappingConfirmActions } from "./MappingConfirmActions";
import { SourceCategoryList } from "./SourceCategoryList";

type PanelError = { title: string; description: string; retry?: () => void };

type Props = {
  batchId: string;
  supplierId: string;
  importProfileId: string;
  onRowsUpdated: (rows: ImportRow[]) => void;
};

export function SourceCategoryMappingPanel({
  batchId,
  supplierId,
  importProfileId,
  onRowsUpdated,
}: Props) {
  const [sourceCategories, setSourceCategories] = useState<SourceCategoryDiscovery[]>([]);
  const [canonicalTree, setCanonicalTree] = useState<CanonicalCategoryNode[]>([]);
  const [selectedSource, setSelectedSource] = useState<SourceCategoryDiscovery | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<CanonicalCategoryNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [panelError, setPanelError] = useState<PanelError | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setPanelError(null);
    try {
      const [discovery, tree] = await Promise.all([
        getBatchSourceCategories(batchId),
        getCanonicalCategoryTree(),
      ]);
      setSourceCategories(discovery.source_categories);
      setCanonicalTree(tree);
    } catch (e) {
      const msg = String(e);
      setPanelError({
        title: "No se pudieron cargar las categorías",
        description: msg,
        retry: () => {
          void refresh();
        },
      });
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function findNodeBySlug(
    nodes: CanonicalCategoryNode[],
    slug: string | null,
  ): CanonicalCategoryNode | null {
    if (!slug) return null;
    for (const node of nodes) {
      if (node.slug === slug) return node;
      const child = findNodeBySlug(node.children, slug);
      if (child) return child;
    }
    return null;
  }

  function handleSelectSource(item: SourceCategoryDiscovery) {
    setSelectedSource(item);
    const slug = item.currently_mapped_category_slug || item.proposed_category_slug;
    setSelectedTarget(findNodeBySlug(canonicalTree, slug));
  }

  async function handleConfirm(notes: string) {
    if (!selectedSource || !selectedTarget) return;
    setLoading(true);
    setPanelError(null);
    try {
      await confirmTaxonomyMapping({
        supplier_id: supplierId,
        import_profile_id: importProfileId,
        source_category_path_raw: selectedSource.source_category_path_raw,
        target_category_id: selectedTarget.id,
        notes: notes || undefined,
      });
      toast.success(
        "Asignación guardada. Pulse «Aplicar cambios de categorías» para actualizar las filas.",
      );
      await refresh();
    } catch (e) {
      const msg = String(e);
      setPanelError({
        title: "No se pudo guardar la asignación",
        description: `${msg} Compruebe la categoría seleccionada e inténtelo de nuevo.`,
        retry: () => {
          void handleConfirm(notes);
        },
      });
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleIgnore(notes: string) {
    if (!selectedSource) return;
    setLoading(true);
    setPanelError(null);
    try {
      await ignoreSourceCategory({
        supplier_id: supplierId,
        import_profile_id: importProfileId,
        source_category_path_raw: selectedSource.source_category_path_raw,
        notes: notes || undefined,
      });
      toast.success("Categoría del PDF marcada como ignorada.");
      await refresh();
    } catch (e) {
      const msg = String(e);
      setPanelError({
        title: "No se pudo ignorar la categoría",
        description: msg,
      });
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemap() {
    setLoading(true);
    setPanelError(null);
    try {
      const result = await remapBatchTaxonomy(batchId, true);
      toast.success(
        `Cambios aplicados: ${result.mapped_count} categorías asignadas, ${result.unmapped_count} sin asignar.`,
      );
      if (result.rows.length > 0) {
        onRowsUpdated(result.rows.map((r) => ({ ...r, row_index: r.source_row_index })));
      }
      await refresh();
    } catch (e) {
      const msg = String(e);
      setPanelError({
        title: "No se pudieron aplicar los cambios de categorías",
        description: `${msg} Revise las asignaciones e inténtelo de nuevo.`,
        retry: () => {
          void handleRemap();
        },
      });
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {panelError && (
        <ErrorState
          title={panelError.title}
          description={panelError.description}
          action={
            <div className="flex gap-2">
              {panelError.retry && (
                <Button type="button" size="sm" variant="secondary" onClick={panelError.retry}>
                  Reintentar
                </Button>
              )}
              <Button type="button" size="sm" variant="ghost" onClick={() => setPanelError(null)}>
                Cerrar
              </Button>
            </div>
          }
          className="py-6 rounded-lg border border-destructive/30 bg-destructive/5"
        />
      )}

      <div className="relative grid gap-4 xl:grid-cols-[1fr_1fr]" aria-busy={loading}>
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-background/60">
            <Loader2 className="h-6 w-6 animate-spin text-primary" aria-hidden="true" />
            <span className="sr-only">Cargando categorías…</span>
          </div>
        )}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Categorías encontradas en el PDF</CardTitle>
          </CardHeader>
          <CardContent>
            <SourceCategoryList
              items={sourceCategories}
              selectedPath={selectedSource?.source_category_path_raw ?? null}
              onSelect={handleSelectSource}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Categorías de destino en la app</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <CanonicalCategoryTree
              nodes={canonicalTree}
              selectedId={selectedTarget?.id ?? null}
              onSelect={setSelectedTarget}
            />
            <MappingConfirmActions
              selectedSource={selectedSource}
              selectedTarget={selectedTarget}
              loading={loading}
              onConfirm={(notes) => {
                void handleConfirm(notes);
              }}
              onIgnore={(notes) => {
                void handleIgnore(notes);
              }}
              onRemap={() => {
                void handleRemap();
              }}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
