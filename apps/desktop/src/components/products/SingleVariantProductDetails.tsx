import type { ProductImage, ProductVariant } from "@/lib/api";
import type { VariantPriceHistoryState } from "@/lib/priceHistory";
import { formatPriceDisplay } from "@/lib/priceHistory";
import { formatVariantField } from "@/lib/variantDetailMeta";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductSourcePageTrigger } from "./ProductSourcePageTrigger";
import { ProductVariantDetailPanel } from "./ProductVariantDetailPanel";

type SingleVariantCommercialCardProps = {
  variant: ProductVariant;
};

export function SingleVariantCommercialCard({ variant }: SingleVariantCommercialCardProps) {
  const priceLabel = formatPriceDisplay(variant.latest_price);

  return (
    <Card className="builder-panel" aria-labelledby="single-variant-commercial-heading">
      <CardHeader className="pb-3">
        <CardTitle id="single-variant-commercial-heading" className="text-base">
          Referencia comercial
        </CardTitle>
        <CardDescription>Datos de la referencia única de este producto.</CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="min-w-0 space-y-1">
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Referencia
            </dt>
            <dd
              className="truncate font-mono text-sm font-semibold text-primary"
              title={variant.sku}
            >
              {variant.sku}
            </dd>
          </div>
          <div className="min-w-0 space-y-1">
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Proveedor
            </dt>
            <dd className="truncate text-sm font-medium text-foreground">
              {formatVariantField(variant.supplier_code)}
            </dd>
          </div>
          <div className="min-w-0 space-y-1">
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              EAN
            </dt>
            <dd className="truncate font-mono text-sm font-medium text-foreground">
              {formatVariantField(variant.ean)}
            </dd>
          </div>
          <div className="min-w-0 space-y-1">
            <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Precio actual
            </dt>
            <dd className="flex flex-wrap items-center gap-2">
              {priceLabel ? (
                <Badge
                  variant="secondary"
                  className="whitespace-nowrap px-2.5 font-semibold tabular-nums shadow-none"
                >
                  {priceLabel}
                </Badge>
              ) : (
                <span className="text-sm text-muted-foreground">—</span>
              )}
              <ProductSourcePageTrigger
                source_page={variant.source_page}
                source_pages={variant.source_pages}
                openOnHover
              />
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

type SingleVariantSidebarPanelProps = {
  variant: ProductVariant & { images?: ProductImage[] };
  apiBase: string;
  historyState: VariantPriceHistoryState;
  onRetryHistory?: () => void;
  onUploadImage: (file: File) => Promise<void>;
  onAddImageFromUrl: (url: string) => Promise<void>;
  onDeleteImage: (imageId: string) => Promise<void>;
  onSetPrimaryImage?: (imageId: string) => Promise<void>;
};

export function SingleVariantSidebarPanel({
  variant,
  apiBase,
  historyState,
  onRetryHistory,
  onUploadImage,
  onAddImageFromUrl,
  onDeleteImage,
  onSetPrimaryImage,
}: SingleVariantSidebarPanelProps) {
  return (
    <ProductVariantDetailPanel
      variant={variant}
      apiBase={apiBase}
      historyState={historyState}
      onRetryHistory={onRetryHistory}
      onUploadImage={onUploadImage}
      onAddImageFromUrl={onAddImageFromUrl}
      onDeleteImage={onDeleteImage}
      onSetPrimaryImage={onSetPrimaryImage}
      presentation="sidebar"
    />
  );
}
