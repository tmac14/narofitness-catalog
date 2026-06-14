import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { GitCompare } from "lucide-react";
import { diffPriceLists, listPriceLists } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TableSkeleton } from "@/components/LoadingPage";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import {
  PRICE_LIST_DIFF_VIEW_POLICY,
  useDataViewMode,
} from "@/hooks/useDataViewMode";
import { PriceListsToolbar } from "@/components/price-lists/PriceListsToolbar";
import { PriceDiffCardList } from "@/components/price-lists/PriceDiffCardList";
import { PriceDiffTable } from "@/components/price-lists/PriceDiffTable";
import type { PriceDiffRow } from "@/components/price-lists/priceDiffLabels";

export default function PriceListsPage() {
  const [lists, setLists] = useState<
    { id: string; source_filename: string; imported_at: string }[]
  >([]);
  const [listA, setListA] = useState("");
  const [listB, setListB] = useState("");
  const [diff, setDiff] = useState<PriceDiffRow[]>([]);
  const [onlyChanges, setOnlyChanges] = useState(true);
  const [minPct, setMinPct] = useState("5");
  const [direction, setDirection] = useState("up");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [hasCompared, setHasCompared] = useState(false);
  const showSkeleton = useDelayedLoading(loading);
  const { showTable, platform } = useDataViewMode(PRICE_LIST_DIFF_VIEW_POLICY);
  const collapseFilters = platform === "mobile";

  const loadLists = useCallback(() => {
    setLoading(true);
    setFetchError(false);
    listPriceLists()
      .then((data) => {
        setLists(data);
        if (data.length >= 2) {
          setListA(data[1].id);
          setListB(data[0].id);
        } else if (data.length === 1) {
          setListA(data[0].id);
        }
      })
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadLists();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadLists]);

  async function runDiff() {
    if (!listA || !listB) {
      toast.error("Seleccione dos tarifas.");
      return;
    }
    setComparing(true);
    try {
      const res = await diffPriceLists(listA, listB, {
        only_changes: onlyChanges,
        min_delta_pct: onlyChanges && direction === "up" ? parseFloat(minPct) : undefined,
        direction,
      });
      setDiff(res.items);
      setHasCompared(true);
      toast.success(`${res.items.length} filas en la comparación`);
    } catch (err) {
      toast.error(String(err));
    } finally {
      setComparing(false);
    }
  }

  if (loading && showSkeleton) {
    return (
      <div>
        <PageHeader
          title="Comparar tarifas"
          description="Analice diferencias de precio entre dos importaciones."
          icon={GitCompare}
        />
        <Card className="mb-6">
          <CardContent className="p-4">
            <TableSkeleton rows={2} />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Comparar tarifas"
        description="Elija dos tarifas importadas y vea qué precios han subido, bajado o desaparecido."
        icon={GitCompare}
      />

      {fetchError ? (
        <ErrorState
          title="No se pudieron cargar las tarifas"
          description="Compruebe la conexión con la aplicación e inténtelo de nuevo."
          action={
            <Button type="button" variant="secondary" className="min-h-11" onClick={loadLists}>
              Reintentar
            </Button>
          }
        />
      ) : (
        <>
          <PriceListsToolbar
            lists={lists}
            listA={listA}
            listB={listB}
            onlyChanges={onlyChanges}
            minPct={minPct}
            direction={direction}
            comparing={comparing}
            collapseFilters={collapseFilters}
            defaultFiltersExpanded={!collapseFilters}
            onListAChange={setListA}
            onListBChange={setListB}
            onOnlyChangesChange={setOnlyChanges}
            onMinPctChange={setMinPct}
            onDirectionChange={setDirection}
            onCompare={() => {
              void runDiff();
            }}
          />

          {diff.length > 0 ? (
            <Card>
              <CardContent className="max-h-[55vh] overflow-auto p-0">
                {showTable ? <PriceDiffTable items={diff} /> : <PriceDiffCardList items={diff} />}
              </CardContent>
            </Card>
          ) : hasCompared ? (
            <EmptyState
              icon={GitCompare}
              title="Sin cambios con estos filtros"
              description="La comparación no devolvió filas. Pruebe a ampliar los filtros o desmarcar «Solo mostrar cambios»."
            />
          ) : (
            <EmptyState
              icon={GitCompare}
              title="Sin comparación"
              description="Seleccione dos tarifas y pulse Comparar para ver las diferencias."
            />
          )}
        </>
      )}
    </div>
  );
}
