import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ResponsiveCollapsiblePanel } from "@/components/responsive/list";
import {
  buildPriceDiffExportUrl,
  formatPriceListOptionLabel,
} from "@/components/price-lists/priceDiffLabels";

export type PriceListOption = {
  id: string;
  source_filename: string;
  imported_at: string;
};

export function PriceListsToolbar({
  lists,
  listA,
  listB,
  onlyChanges,
  minPct,
  direction,
  comparing,
  collapseFilters,
  defaultFiltersExpanded = true,
  onListAChange,
  onListBChange,
  onOnlyChangesChange,
  onMinPctChange,
  onDirectionChange,
  onCompare,
}: {
  lists: PriceListOption[];
  listA: string;
  listB: string;
  onlyChanges: boolean;
  minPct: string;
  direction: string;
  comparing: boolean;
  collapseFilters: boolean;
  defaultFiltersExpanded?: boolean;
  onListAChange: (value: string) => void;
  onListBChange: (value: string) => void;
  onOnlyChangesChange: (value: boolean) => void;
  onMinPctChange: (value: string) => void;
  onDirectionChange: (value: string) => void;
  onCompare: () => void;
}) {
  const [filtersOpen, setFiltersOpen] = useState(defaultFiltersExpanded);

  useEffect(() => {
    setFiltersOpen(defaultFiltersExpanded);
  }, [defaultFiltersExpanded, collapseFilters]);

  const exportUrl =
    listA && listB ? buildPriceDiffExportUrl(listA, listB, direction, minPct) : null;

  return (
    <Card className="mb-6 toolbar-card">
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="min-w-0 flex-1 space-y-2 sm:max-w-none sm:flex-[1_1_14rem]">
            <Label htmlFor="list-a">Tarifa anterior (A)</Label>
            <Select
              id="list-a"
              value={listA}
              onChange={(e) => onListAChange(e.target.value)}
              className="min-h-11 w-full lg:min-w-[220px]"
            >
              <option value="">—</option>
              {lists.map((list) => (
                <option key={list.id} value={list.id}>
                  {formatPriceListOptionLabel(list.source_filename, list.imported_at)}
                </option>
              ))}
            </Select>
          </div>
          <div className="min-w-0 flex-1 space-y-2 sm:max-w-none sm:flex-[1_1_14rem]">
            <Label htmlFor="list-b">Tarifa nueva (B)</Label>
            <Select
              id="list-b"
              value={listB}
              onChange={(e) => onListBChange(e.target.value)}
              className="min-h-11 w-full lg:min-w-[220px]"
            >
              <option value="">—</option>
              {lists.map((list) => (
                <option key={list.id} value={list.id}>
                  {formatPriceListOptionLabel(list.source_filename, list.imported_at)}
                </option>
              ))}
            </Select>
          </div>
          <Button
            type="button"
            className="min-h-11 w-full sm:w-auto"
            disabled={comparing}
            onClick={onCompare}
          >
            {comparing ? "Comparando…" : "Comparar"}
          </Button>
        </div>

        <ResponsiveCollapsiblePanel
          panelId="price-lists-filters-panel"
          triggerLabel="Filtros y exportación"
          open={filtersOpen}
          onOpenChange={setFiltersOpen}
          collapseEnabled={collapseFilters}
          showPanelBorder={!collapseFilters}
          panelClassName="price-lists-toolbar__filters flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end"
        >
          <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm">
            <input
              id="only-changes"
              type="checkbox"
              className="h-5 w-5 shrink-0 accent-primary"
              checked={onlyChanges}
              onChange={(e) => onOnlyChangesChange(e.target.checked)}
            />
            <span className="font-normal">Solo mostrar cambios</span>
          </label>
          <div className="min-w-0 flex-1 space-y-2 sm:flex-[0_1_12rem]">
            <Label htmlFor="direction">Dirección del cambio</Label>
            <Select
              id="direction"
              value={direction}
              onChange={(e) => onDirectionChange(e.target.value)}
              className="min-h-11 w-full sm:min-w-[160px]"
            >
              <option value="any">Cualquier dirección</option>
              <option value="up">Solo subidas</option>
              <option value="down">Solo bajadas</option>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="min-pct">Cambio mínimo (%)</Label>
            <Input
              id="min-pct"
              type="number"
              value={minPct}
              onChange={(e) => onMinPctChange(e.target.value)}
              className="min-h-11 w-full sm:w-24"
            />
          </div>
          {exportUrl ? (
            <Button variant="secondary" asChild className="min-h-11 w-full sm:w-auto">
              <a href={exportUrl} target="_blank" rel="noreferrer">
                <Download className="h-4 w-4" aria-hidden="true" />
                Exportar CSV
              </a>
            </Button>
          ) : null}
        </ResponsiveCollapsiblePanel>
      </CardContent>
    </Card>
  );
}
