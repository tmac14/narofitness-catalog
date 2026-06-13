import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { GitCompare, Download } from "lucide-react";
import { API_BASE, diffPriceLists, listPriceLists } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
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
import { TableSkeleton } from "@/components/LoadingPage";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";

export default function PriceListsPage() {
  const [lists, setLists] = useState<
    { id: string; source_filename: string; imported_at: string }[]
  >([]);
  const [listA, setListA] = useState("");
  const [listB, setListB] = useState("");
  const [diff, setDiff] = useState<
    {
      sku: string;
      name: string;
      price_a: string | null;
      price_b: string | null;
      delta_abs: string | null;
      delta_pct: string | null;
      change_type: string;
    }[]
  >([]);
  const [onlyChanges, setOnlyChanges] = useState(true);
  const [minPct, setMinPct] = useState("5");
  const [direction, setDirection] = useState("up");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [hasCompared, setHasCompared] = useState(false);
  const showSkeleton = useDelayedLoading(loading);

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
            <Button type="button" size="sm" variant="secondary" onClick={loadLists}>
              Reintentar
            </Button>
          }
        />
      ) : (
        <>
          <Card className="mb-6 toolbar-card">
            <CardContent className="p-4 space-y-4">
              <div className="flex flex-wrap items-end gap-4">
                <div className="space-y-2">
                  <Label htmlFor="list-a">Tarifa anterior (A)</Label>
                  <Select
                    id="list-a"
                    value={listA}
                    onChange={(e) => setListA(e.target.value)}
                    className="min-w-[220px]"
                  >
                    <option value="">—</option>
                    {lists.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.source_filename} ({new Date(l.imported_at).toLocaleDateString("es-ES")})
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="list-b">Tarifa nueva (B)</Label>
                  <Select
                    id="list-b"
                    value={listB}
                    onChange={(e) => setListB(e.target.value)}
                    className="min-w-[220px]"
                  >
                    <option value="">—</option>
                    {lists.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.source_filename} ({new Date(l.imported_at).toLocaleDateString("es-ES")})
                      </option>
                    ))}
                  </Select>
                </div>
                <Button
                  type="button"
                  onClick={() => {
                    void runDiff();
                  }}
                  disabled={comparing}
                >
                  {comparing ? "Comparando…" : "Comparar"}
                </Button>
              </div>
              <div className="flex flex-wrap items-end gap-4 border-t border-border pt-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    id="only-changes"
                    type="checkbox"
                    checked={onlyChanges}
                    onChange={(e) => setOnlyChanges(e.target.checked)}
                  />
                  <Label htmlFor="only-changes" className="font-normal cursor-pointer">
                    Solo mostrar cambios
                  </Label>
                </label>
                <div className="space-y-2">
                  <Label htmlFor="direction">Dirección del cambio</Label>
                  <Select
                    id="direction"
                    value={direction}
                    onChange={(e) => setDirection(e.target.value)}
                    className="w-auto min-w-[160px]"
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
                    onChange={(e) => setMinPct(e.target.value)}
                    className="w-20"
                  />
                </div>
                {listA && listB && (
                  <Button variant="secondary" asChild>
                    <a
                      href={`${API_BASE}/api/v1/price-lists/${listA}/diff/${listB}/export.csv?direction=${direction}&min_delta_pct=${minPct}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Download className="h-4 w-4" aria-hidden="true" />
                      Exportar CSV
                    </a>
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {diff.length > 0 ? (
            <Card>
              <CardContent className="p-0 max-h-[55vh] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Referencia</TableHead>
                      <TableHead>Nombre</TableHead>
                      <TableHead>Precio A</TableHead>
                      <TableHead>Precio B</TableHead>
                      <TableHead>Diferencia</TableHead>
                      <TableHead>Diferencia %</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {diff.map((r) => (
                      <TableRow
                        key={r.sku}
                        className={
                          r.change_type === "only_a"
                            ? "diff-only-a"
                            : r.change_type === "only_b"
                              ? "diff-only-b"
                              : ""
                        }
                      >
                        <TableCell>{r.sku}</TableCell>
                        <TableCell>{r.name}</TableCell>
                        <TableCell>{r.price_a ?? "—"}</TableCell>
                        <TableCell>{r.price_b ?? "—"}</TableCell>
                        <TableCell>{r.delta_abs ?? "—"}</TableCell>
                        <TableCell>{r.delta_pct != null ? `${r.delta_pct}%` : "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
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
