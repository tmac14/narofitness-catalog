import type { ProductMasterDetail, ProductVariant, VariantAttributeColumn } from "@/lib/api";
import type { VariantPriceHistoryState } from "@/lib/priceHistory";
import { formatPriceDisplay } from "@/lib/priceHistory";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { getDetailVariantCellValue, layoutDetailVariantColumns } from "@/lib/variantRepresentation";
import { ProductSourcePageTrigger } from "./ProductSourcePageTrigger";
import { ProductVariantDetailPanel } from "./ProductVariantDetailPanel";

type ProductVariantsPanelProps = {
  master: ProductMasterDetail;
  apiBase: string;
  expandedVariantId: string | null;
  historyState: VariantPriceHistoryState;
  onToggleExpand: (variantId: string) => void;
  onUploadVariantImage: (variantId: string, file: File) => Promise<void>;
  onAddVariantImageFromUrl: (variantId: string, url: string) => Promise<void>;
  onDeleteVariantImage: (imageId: string) => Promise<void>;
  onSetVariantImagePrimary?: (imageId: string) => Promise<void>;
  onRetryHistory?: () => void;
};

type VariantCellKind = "variant" | "brand" | "spec";

function VariantDynamicCell({
  variant,
  column,
  kind,
}: {
  variant: ProductVariant;
  column: VariantAttributeColumn;
  kind: VariantCellKind;
}) {
  const value = getDetailVariantCellValue(variant, column.key);
  const cellClass =
    kind === "variant"
      ? "product-variants-panel__cell-variant"
      : kind === "brand"
        ? "product-variants-panel__cell-brand"
        : "product-variants-panel__cell-spec";

  return (
    <TableCell className={cn("py-2.5", cellClass)} title={value === "—" ? undefined : value}>
      {value}
    </TableCell>
  );
}

export function VariantListPriceCell({ variant }: { variant: ProductVariant }) {
  const priceLabel = formatPriceDisplay(variant.latest_price);

  return (
    <TableCell className="py-2.5 text-center">
      {priceLabel ? (
        <Badge
          variant="secondary"
          className="whitespace-nowrap px-2.5 font-semibold tabular-nums shadow-none"
          title={priceLabel}
        >
          {priceLabel}
        </Badge>
      ) : (
        <span className="text-muted-foreground">—</span>
      )}
    </TableCell>
  );
}

export function VariantRowDetailControls({
  variant,
  expanded,
  onToggleExpand,
}: {
  variant: ProductVariant;
  expanded: boolean;
  onToggleExpand: () => void;
}) {
  return (
    <TableCell className="py-2.5 text-center">
      <div className="flex items-center justify-center gap-0.5">
        <ProductSourcePageTrigger
          source_page={variant.source_page}
          source_pages={variant.source_pages}
          openOnHover
        />
        <Button
          type="button"
          variant={expanded ? "secondary" : "ghost"}
          size="sm"
          className={cn(
            "h-8 gap-1 px-2 text-muted-foreground hover:text-foreground",
            expanded && "bg-muted text-foreground shadow-none",
          )}
          aria-expanded={expanded}
          aria-controls={expanded ? `variant-detail-${variant.id}` : undefined}
          aria-label={
            expanded ? `Ocultar detalle de ${variant.sku}` : `Ver detalle de ${variant.sku}`
          }
          onClick={onToggleExpand}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4 shrink-0" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0" aria-hidden="true" />
          )}
          <span className="hidden text-xs font-medium sm:inline">
            {expanded ? "Ocultar" : "Detalle"}
          </span>
        </Button>
      </div>
    </TableCell>
  );
}

export function ProductVariantsPanel({
  master,
  apiBase,
  expandedVariantId,
  historyState,
  onToggleExpand,
  onUploadVariantImage,
  onAddVariantImageFromUrl,
  onDeleteVariantImage,
  onSetVariantImagePrimary,
  onRetryHistory,
}: ProductVariantsPanelProps) {
  const { leadingColumns, identityColumns, specColumns } = layoutDetailVariantColumns(master);
  const expandedVariant = expandedVariantId
    ? master.variants.find((variant) => variant.id === expandedVariantId)
    : null;

  if (master.variants.length === 0) {
    return (
      <Card className="builder-panel">
        <CardContent className="py-12 text-center text-sm text-muted-foreground">
          Este producto no tiene variantes.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="builder-panel overflow-hidden">
      <CardHeader className="border-b border-border/60 bg-muted/10">
        <CardTitle>Variantes</CardTitle>
        <CardDescription>
          Referencias, precios y detalle por variante ({master.variants.length}). Pulse una fila o
          el control de detalle para ver el contenido completo.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <div className="product-variants-detail-table-wrap overflow-x-auto">
          <table
            className="product-variants-detail-table w-full caption-bottom text-sm"
            aria-label={`Variantes de ${master.name}`}
          >
            <colgroup>
              {leadingColumns.map((column) => (
                <col key={column.key} className="product-variants-panel__col-variant" />
              ))}
              <col className="product-variants-panel__col-ref" />
              <col className="product-variants-panel__col-supplier" />
              {identityColumns.map((column) => (
                <col key={column.key} className="product-variants-panel__col-brand" />
              ))}
              {specColumns.map((column) => (
                <col key={column.key} className="product-variants-panel__col-spec" />
              ))}
              <col className="product-variants-panel__col-price" />
              <col className="product-variants-panel__col-expand" />
            </colgroup>
            <TableHeader>
              <TableRow className="bg-muted/30 hover:bg-muted/30">
                {leadingColumns.map((column) => (
                  <TableHead key={column.key} className="text-xs uppercase tracking-wide">
                    {column.label}
                  </TableHead>
                ))}
                <TableHead className="text-xs uppercase tracking-wide">Referencia</TableHead>
                <TableHead className="text-xs uppercase tracking-wide">Proveedor</TableHead>
                {identityColumns.map((column) => (
                  <TableHead key={column.key} className="text-xs uppercase tracking-wide">
                    {column.label}
                  </TableHead>
                ))}
                {specColumns.map((column) => (
                  <TableHead key={column.key} className="text-xs uppercase tracking-wide">
                    {column.label}
                  </TableHead>
                ))}
                <TableHead className="text-center text-xs uppercase tracking-wide">
                  Precio
                </TableHead>
                <TableHead className="product-variants-panel__col-expand">
                  <span className="sr-only">Detalle</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {master.variants.map((variant, index) => {
                const expanded = expandedVariantId === variant.id;
                const stripe = index % 2 === 0 ? "bg-background" : "bg-muted/10";

                return (
                  <TableRow
                    key={variant.id}
                    data-expanded={expanded ? "true" : "false"}
                    className={cn(
                      "product-variants-table-row",
                      stripe,
                      "transition-colors hover:bg-row-hover",
                      expanded && "is-expanded",
                    )}
                  >
                    {leadingColumns.map((column) => (
                      <VariantDynamicCell
                        key={column.key}
                        variant={variant}
                        column={column}
                        kind="variant"
                      />
                    ))}
                    <TableCell className="product-variants-panel__cell-ref py-2.5">
                      {variant.sku}
                    </TableCell>
                    <TableCell
                      className="product-variants-panel__cell-supplier py-2.5 text-muted-foreground"
                      title={variant.supplier_code ?? undefined}
                    >
                      {variant.supplier_code ?? "—"}
                    </TableCell>
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
                    <VariantListPriceCell variant={variant} />
                    <VariantRowDetailControls
                      variant={variant}
                      expanded={expanded}
                      onToggleExpand={() => onToggleExpand(variant.id)}
                    />
                  </TableRow>
                );
              })}
            </TableBody>
          </table>
        </div>

        {expandedVariant ? (
          <div
            id={`variant-detail-${expandedVariant.id}`}
            className="product-variants-detail-panel"
            role="region"
            aria-label={`Detalle de variante ${expandedVariant.sku}`}
          >
            <ProductVariantDetailPanel
              variant={expandedVariant}
              apiBase={apiBase}
              historyState={historyState}
              onRetryHistory={onRetryHistory}
              onUploadImage={(file) => onUploadVariantImage(expandedVariant.id, file)}
              onAddImageFromUrl={(url) => onAddVariantImageFromUrl(expandedVariant.id, url)}
              onDeleteImage={onDeleteVariantImage}
              onSetPrimaryImage={onSetVariantImagePrimary}
            />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
