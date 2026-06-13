import { Fragment, useCallback, useEffect, useRef, useState } from "react";

import { Link } from "react-router-dom";

import {
  ChevronDown,
  ChevronRight,
  Eye,
  ImageIcon,
  MoreVertical,
  Package,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  API_BASE,
  listMasters,
  type MasterSortKey,
  type ProductMaster,
  type SortDirection,
  type VariantAttributeColumn,
} from "@/lib/api";

import { PageHeader } from "@/components/PageHeader";

import { Card, CardContent } from "@/components/ui/card";

import { Input } from "@/components/ui/input";

import { Label } from "@/components/ui/label";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { PaginationBar } from "@/components/ui/pagination";

import { DataTableScroll } from "@/components/ui/data-table";

import { SortableTableHead } from "@/components/ui/sortable-table-head";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { EmptyState } from "@/components/EmptyState";

import { ErrorState } from "@/components/ErrorState";

import { TableSkeleton } from "@/components/LoadingPage";

import { useDelayedLoading } from "@/hooks/useDelayedLoading";

import { useDebouncedValue } from "@/hooks/useDebouncedValue";

import { PRODUCTS_LIST_VIEW_POLICY, useDataViewMode } from "@/hooks/useDataViewMode";

import { ProductMasterCardList } from "@/components/products/ProductMasterCardList";
import {
  hasMultipleVariants,
  parentPrice,
  parentReference,
  variantCount,
} from "@/components/products/productMasterCardMeta";

import { PAGE_SIZE_OPTIONS, totalPages } from "@/lib/pagination";
import { listVariantsInApiOrder } from "@/lib/productSpecs";
import {
  getListVariantAttributeValue,
  isMixedBrandMaster,
  layoutListVariantColumns,
  masterBrandDisplay,
  masterBrandTitle,
} from "@/lib/variantRepresentation";
import { ProductSourcePageTrigger } from "@/components/products/ProductSourcePageTrigger";
import { cn } from "@/lib/utils";

type VariantCellKind = "variant" | "brand" | "spec";

function VariantDynamicCell({
  variant,
  column,
  kind,
}: {
  variant: ProductMaster["variants"][number];
  column: VariantAttributeColumn;
  kind: VariantCellKind;
}) {
  const value = getListVariantAttributeValue(variant, column.key);
  const cellClass =
    kind === "variant"
      ? "product-variants-panel__cell-variant"
      : kind === "brand"
        ? "product-variants-panel__cell-brand"
        : "product-variants-panel__cell-spec";

  return (
    <td className={cellClass} title={value === "—" ? undefined : value}>
      {value}
    </td>
  );
}

export function VariantsExpandedPanel({ master }: { master: ProductMaster }) {
  const variants = listVariantsInApiOrder(master.variants);
  const { leadingColumns, identityColumns, specColumns } = layoutListVariantColumns(master);

  return (
    <div className="product-variants-panel">
      <div className="product-variants-panel__header">
        <span className="product-variants-panel__title">Variantes del producto</span>
        <span className="product-variants-panel__count">{variants.length}</span>
      </div>
      {variants.length === 0 ? (
        <p className="px-4 py-3 text-sm text-muted-foreground">Este producto no tiene variantes.</p>
      ) : (
        <table className="product-variants-panel__table" aria-label={`Variantes de ${master.name}`}>
          <colgroup>
            <col className="product-variants-panel__col-photo" />
            {leadingColumns.map((column) => (
              <col key={column.key} className="product-variants-panel__col-variant" />
            ))}
            <col className="product-variants-panel__col-ref" />
            {identityColumns.map((column) => (
              <col key={column.key} className="product-variants-panel__col-brand" />
            ))}
            {specColumns.map((column) => (
              <col key={column.key} className="product-variants-panel__col-spec" />
            ))}
            <col className="product-variants-panel__col-price" />
          </colgroup>
          <thead>
            <tr>
              <th>
                <span className="sr-only">Foto</span>
              </th>
              {leadingColumns.map((column) => (
                <th key={column.key} scope="col">
                  {column.label}
                </th>
              ))}
              <th>Referencia</th>
              {identityColumns.map((column) => (
                <th key={column.key} scope="col">
                  {column.label}
                </th>
              ))}
              {specColumns.map((column) => (
                <th key={column.key} scope="col">
                  {column.label}
                </th>
              ))}
              <th>PVP</th>
            </tr>
          </thead>
          <tbody>
            {variants.map((variant, index) => {
              const stripe =
                index % 2 === 0
                  ? "product-variants-panel__row--even"
                  : "product-variants-panel__row--odd";

              return (
                <tr key={variant.id} className={stripe}>
                  <td>
                    <VariantImageThumb imageUrl={variant.image_url} />
                  </td>
                  {leadingColumns.map((column) => (
                    <VariantDynamicCell
                      key={column.key}
                      variant={variant}
                      column={column}
                      kind="variant"
                    />
                  ))}
                  <td className="product-variants-panel__cell-ref">{variant.sku}</td>
                  {identityColumns.map((column) => (
                    <VariantDynamicCell
                      key={column.key}
                      variant={variant}
                      column={column}
                      kind="brand"
                    />
                  ))}
                  {specColumns.map((column) => (
                    <VariantDynamicCell
                      key={column.key}
                      variant={variant}
                      column={column}
                      kind="spec"
                    />
                  ))}
                  <td className="whitespace-nowrap tabular-nums">
                    {variant.price ? (
                      <Badge
                        variant="secondary"
                        className="whitespace-nowrap px-2.5 font-semibold tabular-nums shadow-none"
                        title={variant.price}
                      >
                        {variant.price}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

function CategoryStack({
  parent,
  sub,
}: {
  parent: string | null | undefined;
  sub: string | null | undefined;
}) {
  const parentLabel = parent?.trim() || null;
  const subLabel = sub?.trim() || null;

  if (!parentLabel && !subLabel) {
    return <span className="text-muted-foreground">—</span>;
  }

  if (parentLabel && subLabel && parentLabel.toLowerCase() !== subLabel.toLowerCase()) {
    return (
      <div className="flex min-h-8 w-full flex-col items-center justify-center gap-0.5 text-center leading-tight">
        <span className="max-w-full truncate text-[0.65rem] uppercase tracking-wide text-muted-foreground">
          {parentLabel}
        </span>
        <span className="max-w-full truncate text-[0.7rem] font-medium text-foreground">
          {subLabel}
        </span>
      </div>
    );
  }

  return (
    <div className="flex min-h-8 w-full items-center justify-center text-center">
      <span className="line-clamp-2 max-w-full text-[0.7rem] font-medium leading-tight text-foreground">
        {subLabel || parentLabel}
      </span>
    </div>
  );
}

function ProductNameCell({ master }: { master: ProductMaster }) {
  const imageSrc = master.image_url ? `${API_BASE}${master.image_url}` : null;

  return (
    <div className="flex min-w-0 items-center gap-2.5 py-1">
      {imageSrc ? (
        <img
          src={imageSrc}
          alt=""
          className="h-10 w-10 shrink-0 rounded border border-border bg-muted/30 object-contain"
        />
      ) : (
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded border border-dashed border-border bg-muted/20 text-muted-foreground"
          aria-hidden="true"
        >
          <ImageIcon className="h-4 w-4" />
        </div>
      )}
      <span className="min-w-0 flex-1 truncate text-xs font-medium" title={master.name}>
        {master.name}
      </span>
    </div>
  );
}

function VariantImageThumb({ imageUrl }: { imageUrl: string | null | undefined }) {
  if (imageUrl) {
    return (
      <img
        src={`${API_BASE}${imageUrl}`}
        alt=""
        className="h-8 w-8 shrink-0 border border-border bg-muted/30 object-contain"
      />
    );
  }

  return (
    <div
      className="h-8 w-8 shrink-0 border border-dashed border-border/60 bg-muted/15"
      aria-hidden="true"
    />
  );
}

export function MasterListPriceCell({ master }: { master: ProductMaster }) {
  const priceLabel = parentPrice(master);

  return (
    <TableCell className="col-centered col-price overflow-visible">
      <div className="flex justify-center overflow-visible">
        {priceLabel !== "—" ? (
          <Badge
            variant="success"
            className="shrink-0 whitespace-nowrap border-success/50 bg-success/10 px-2.5 tabular-nums font-semibold shadow-none"
            title={priceLabel}
          >
            {priceLabel}
          </Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </div>
    </TableCell>
  );
}

export function ProductRowActions({
  master,
  expanded,
  onToggleExpand,
}: {
  master: ProductMaster;
  expanded: boolean;
  onToggleExpand: () => void;
}) {
  const count = variantCount(master);
  const showVariantsToggle = hasMultipleVariants(master);

  return (
    <div className="flex items-center justify-center gap-0.5">
      {showVariantsToggle ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
          onClick={onToggleExpand}
          aria-expanded={expanded}
          aria-label={
            expanded
              ? `Ocultar variantes de ${master.name}`
              : `Mostrar ${count} variantes de ${master.name}`
          }
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>
      ) : null}

      <ProductSourcePageTrigger
        source_page={master.source_page}
        source_pages={master.source_pages}
      />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
            aria-label={`Más acciones para ${master.name}`}
          >
            <MoreVertical className="h-4 w-4" aria-hidden="true" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem asChild>
            <Link to={`/products/${master.id}`} className="cursor-pointer">
              <Eye className="h-4 w-4" aria-hidden="true" />
              Ver ficha
            </Link>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

export default function ProductsPage() {
  const [items, setItems] = useState<ProductMaster[]>([]);

  const [q, setQ] = useState("");

  const debouncedQ = useDebouncedValue(q, 300);

  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(true);

  const [fetchError, setFetchError] = useState(false);

  const [page, setPage] = useState(1);

  const [pageSize, setPageSize] = useState(50);

  const [sortBy, setSortBy] = useState<MasterSortKey>("name");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");

  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { showTable } = useDataViewMode(PRODUCTS_LIST_VIEW_POLICY);

  const showSkeleton = useDelayedLoading(loading);
  const prevDebouncedQ = useRef(debouncedQ);

  const handleSort = useCallback(
    (column: MasterSortKey) => {
      if (sortBy === column) {
        setSortDir((dir) => (dir === "asc" ? "desc" : "asc"));
      } else {
        setSortBy(column);
        setSortDir("asc");
      }
      setPage(1);
    },
    [sortBy],
  );

  const toggleExpanded = useCallback((master: ProductMaster) => {
    if (!hasMultipleVariants(master)) return;
    setExpandedId((prev) => (prev === master.id ? null : master.id));
  }, []);

  const openVariantSheet = useCallback((master: ProductMaster) => {
    setExpandedId(master.id);
  }, []);

  const handleVariantSheetOpenChange = useCallback((open: boolean) => {
    if (!open) setExpandedId(null);
  }, []);

  const loadProducts = useCallback(() => {
    const searchChanged = prevDebouncedQ.current !== debouncedQ;
    if (searchChanged) {
      prevDebouncedQ.current = debouncedQ;
      if (page !== 1) {
        setPage(1);
        return;
      }
    }
    setLoading(true);
    setFetchError(false);
    listMasters({
      q: debouncedQ || undefined,
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_dir: sortDir,
    })
      .then((d) => {
        setItems(d.items);
        setTotal(d.total);
        const maxPage = totalPages(d.total, pageSize);
        if (page > maxPage && maxPage >= 1) {
          setPage(maxPage);
        }
      })
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, [debouncedQ, page, pageSize, sortBy, sortDir]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadProducts();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadProducts]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setExpandedId(null);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [page, debouncedQ, sortBy, sortDir, pageSize]);

  return (
    <div>
      <PageHeader
        title="Productos"
        description="Familias de producto de su catálogo. Cada familia puede tener varias variantes (peso, color, etc.)."
        icon={Package}
      />

      <Card className="mb-6 toolbar-card">
        <CardContent className="flex items-center gap-3 p-4">
          <div className="relative max-w-md flex-1 space-y-2">
            <Label htmlFor="product-search">Buscar productos</Label>
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />
              <Input
                id="product-search"
                className="pl-9"
                placeholder="Nombre, referencia o código de barras…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <CardContent className="p-0">
          {showSkeleton ? (
            <TableSkeleton rows={8} />
          ) : fetchError ? (
            <ErrorState
              title="No se pudieron cargar los productos"
              description="Compruebe la conexión con la aplicación e inténtelo de nuevo."
              action={
                <Button type="button" size="sm" variant="secondary" onClick={loadProducts}>
                  Reintentar
                </Button>
              }
            />
          ) : items.length === 0 ? (
            <EmptyState
              icon={Package}
              title="Sin productos"
              description={
                q
                  ? "No hay resultados para su búsqueda."
                  : "Importe una tarifa para crear productos."
              }
              action={
                !q ? (
                  <Button asChild size="sm">
                    <Link to="/import">Importar tarifa</Link>
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <>
              <div className="flex justify-end border-b border-border px-4 py-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={loadProducts}
                  disabled={loading}
                >
                  <RefreshCw
                    className={cn("h-4 w-4", loading && "animate-spin")}
                    aria-hidden="true"
                  />
                  Actualizar
                </Button>
              </div>

              {showTable ? (
                <DataTableScroll maxHeight="max-h-[55vh]">
                  <table className="product-list-table w-full caption-bottom text-sm">
                    <colgroup>
                      <col className="product-col-name" style={{ width: "40%" }} />
                      <col style={{ width: "14%" }} />
                      <col style={{ width: "9%" }} />
                      <col style={{ width: "13.5%" }} />
                      <col style={{ width: "11%" }} />
                      <col style={{ width: "5rem" }} />
                    </colgroup>
                    <TableHeader>
                      <TableRow>
                        <SortableTableHead
                          label="Producto"
                          column="name"
                          activeColumn={sortBy}
                          direction={sortDir}
                          onSort={handleSort}
                          className="col-product"
                        />

                        <SortableTableHead
                          label="Referencia"
                          column="reference"
                          activeColumn={sortBy}
                          direction={sortDir}
                          onSort={handleSort}
                          align="center"
                          className="col-centered"
                        />

                        <SortableTableHead
                          label="Marca"
                          column="brand"
                          activeColumn={sortBy}
                          direction={sortDir}
                          onSort={handleSort}
                          align="center"
                          className="col-centered"
                        />

                        <SortableTableHead
                          label="Categoría"
                          column="category"
                          activeColumn={sortBy}
                          direction={sortDir}
                          onSort={handleSort}
                          align="center"
                          className="col-centered"
                        />

                        <SortableTableHead
                          label="PVP"
                          column="price"
                          activeColumn={sortBy}
                          direction={sortDir}
                          onSort={handleSort}
                          align="center"
                          className="col-centered col-price"
                        />

                        <TableHead className="col-centered">
                          <span className="sr-only">Acciones</span>
                        </TableHead>
                      </TableRow>
                    </TableHeader>

                    <TableBody>
                      {items.map((m, index) => {
                        const expanded = expandedId === m.id && hasMultipleVariants(m);
                        const stripe =
                          index % 2 === 0 ? "product-list-row--even" : "product-list-row--odd";
                        return (
                          <Fragment key={m.id}>
                            <TableRow
                              className={cn("product-list-row", stripe, expanded && "is-expanded")}
                            >
                              <TableCell className="col-product overflow-hidden">
                                <ProductNameCell master={m} />
                              </TableCell>

                              <TableCell
                                className="col-centered truncate font-mono text-xs font-bold text-primary"
                                title={(m.references ?? []).join(", ") || undefined}
                              >
                                {parentReference(m)}
                              </TableCell>

                              <TableCell className="col-centered">
                                {(() => {
                                  const brandLabel = masterBrandDisplay(m);
                                  if (!brandLabel) {
                                    return <span className="text-muted-foreground">—</span>;
                                  }
                                  return (
                                    <Badge
                                      variant={isMixedBrandMaster(m) ? "outline" : "secondary"}
                                      className="max-w-full truncate font-normal"
                                      title={masterBrandTitle(m)}
                                    >
                                      {brandLabel}
                                    </Badge>
                                  );
                                })()}
                              </TableCell>

                              <TableCell className="col-centered">
                                <CategoryStack
                                  parent={m.category_parent_name}
                                  sub={m.category_sub_name}
                                />
                              </TableCell>

                              <MasterListPriceCell master={m} />

                              <TableCell className="col-centered !px-2">
                                <ProductRowActions
                                  master={m}
                                  expanded={expanded}
                                  onToggleExpand={() => toggleExpanded(m)}
                                />
                              </TableCell>
                            </TableRow>

                            {expanded ? (
                              <TableRow className="product-variants-detail-row hover:bg-transparent">
                                <TableCell colSpan={6} className="p-0">
                                  <VariantsExpandedPanel master={m} />
                                </TableCell>
                              </TableRow>
                            ) : null}
                          </Fragment>
                        );
                      })}
                    </TableBody>
                  </table>
                </DataTableScroll>
              ) : (
                <ProductMasterCardList
                  items={items}
                  sortBy={sortBy}
                  sortDir={sortDir}
                  onSort={handleSort}
                  variantSheetMasterId={expandedId}
                  onOpenVariants={openVariantSheet}
                  onVariantSheetOpenChange={handleVariantSheetOpenChange}
                />
              )}

              <PaginationBar
                page={page}
                pageSize={pageSize}
                totalItems={total}
                onPageChange={setPage}
                onPageSizeChange={(size) => {
                  setPageSize(size);
                  setPage(1);
                }}
                pageSizeOptions={[...PAGE_SIZE_OPTIONS]}
              />

              <p className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
                Total en el sistema: {total}
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
