import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { BookOpen, Plus, Trash2 } from "lucide-react";
import { createCatalog, deleteCatalog, listCatalogs } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { PaginationBar } from "@/components/ui/pagination";
import { DataTableScroll } from "@/components/ui/data-table";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState } from "@/components/EmptyState";
import { TableSkeleton } from "@/components/LoadingPage";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import { paginate, clampPage, PAGE_SIZE_OPTIONS } from "@/lib/pagination";

export default function CatalogsPage() {
  const [items, setItems] = useState<
    { id: string; name: string; default_markup_percent: string }[]
  >([]);
  const [name, setName] = useState("Mayorista +20%");
  const [markup, setMarkup] = useState("20");
  const [showIvaColumn, setShowIvaColumn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const showSkeleton = useDelayedLoading(loading);
  const nav = useNavigate();

  function refresh(): void {
    void listCatalogs()
      .then((d) => setItems(d.items))
      .catch((error: unknown) => {
        toast.error(String(error));
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function onCreate() {
    const c = await createCatalog(name, parseFloat(markup) || 0, showIvaColumn);
    toast.success("Catálogo creado");
    refresh();
    nav(`/catalogs/${c.id}`);
  }

  async function onDelete(id: string, catalogName: string) {
    if (!confirm(`¿Eliminar el catálogo "${catalogName}"?`)) return;
    await deleteCatalog(id);
    toast.success("Catálogo eliminado");
    refresh();
  }

  const currentPage = clampPage(page, items.length, pageSize);
  const pageItems = useMemo(
    () => paginate(items, currentPage, pageSize),
    [currentPage, items, pageSize],
  );

  return (
    <div>
      <PageHeader title="Catálogos" icon={BookOpen} />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Nuevo catálogo
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 max-w-xl">
            <div className="space-y-2">
              <Label htmlFor="catalog-name">Nombre</Label>
              <Input id="catalog-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="catalog-markup">Aumento sobre precio base (%)</Label>
              <Input
                id="catalog-markup"
                type="number"
                value={markup}
                onChange={(e) => setMarkup(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 sm:col-span-2">
              <input
                id="catalog-show-iva"
                type="checkbox"
                className="rounded border-border"
                checked={showIvaColumn}
                onChange={(e) => setShowIvaColumn(e.target.checked)}
              />
              <Label htmlFor="catalog-show-iva" className="font-normal cursor-pointer">
                Mostrar columna PVP + IVA en el PDF
              </Label>
            </div>
          </div>
          <Button
            className="mt-4"
            onClick={() => {
              void onCreate();
            }}
          >
            Crear catálogo
          </Button>
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <CardContent className="p-0">
          {showSkeleton ? (
            <TableSkeleton rows={6} />
          ) : items.length === 0 ? (
            <>
              <EmptyState
                icon={BookOpen}
                title="Sin catálogos"
                description="Cree su primer catálogo arriba."
              />
              <PaginationBar page={1} pageSize={pageSize} totalItems={0} onPageChange={setPage} />
            </>
          ) : (
            <>
              <DataTableScroll maxHeight="max-h-[55vh]">
                <table className="w-full caption-bottom text-sm table-fixed">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nombre</TableHead>
                      <TableHead className="w-[100px]">Margen %</TableHead>
                      <TableHead className="w-[140px]" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pageItems.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell className="truncate font-medium">{c.name}</TableCell>
                        <TableCell className="tabular-nums">{c.default_markup_percent}%</TableCell>
                        <TableCell className="space-x-2">
                          <Button variant="link" size="sm" asChild className="h-auto p-0">
                            <Link to={`/catalogs/${c.id}`}>Editar</Link>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive"
                            onClick={() => {
                              void onDelete(c.id, c.name);
                            }}
                            aria-label={`Eliminar ${c.name}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </table>
              </DataTableScroll>
              <PaginationBar
                page={currentPage}
                pageSize={pageSize}
                totalItems={items.length}
                onPageChange={setPage}
                onPageSizeChange={(size) => {
                  setPageSize(size);
                  setPage(1);
                }}
                pageSizeOptions={[...PAGE_SIZE_OPTIONS]}
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
