import type { ProductImage, ProductVariant } from "@/lib/api";
import type { VariantPriceHistoryState } from "@/lib/priceHistory";
import { variantDisplayTitle, variantSpecsWithValue } from "@/lib/variantDetailMeta";
import { PriceEvolutionCard } from "./PriceEvolutionCard";
import { ProductSpecChip } from "./ProductSpecChip";
import { VariantDetailCard } from "./VariantDetailCard";
import { VariantDetailHeader } from "./VariantDetailHeader";
import { VariantImageGallery } from "./VariantImageGallery";

type ProductVariantDetailPanelProps = {
  variant: ProductVariant & { images?: ProductImage[] };
  apiBase: string;
  historyState: VariantPriceHistoryState;
  onRetryHistory?: () => void;
  onUploadImage: (file: File) => Promise<void>;
  onAddImageFromUrl: (url: string) => Promise<void>;
  onDeleteImage: (imageId: string) => Promise<void>;
  onSetPrimaryImage?: (imageId: string) => Promise<void>;
  presentation?: "full" | "sidebar";
};

export function ProductVariantDetailPanel({
  variant,
  apiBase,
  historyState,
  onRetryHistory,
  onUploadImage,
  onAddImageFromUrl,
  onDeleteImage,
  onSetPrimaryImage,
  presentation = "full",
}: ProductVariantDetailPanelProps) {
  const specs = variantSpecsWithValue(variant.specs);
  const images = variant.images ?? [];
  const altLabel = variantDisplayTitle(variant);

  const mediaAndPrice = (
    <div className="variant-detail-aside-stack">
      <div className="variant-detail-media-card">
        <VariantImageGallery
          images={images}
          apiBase={apiBase}
          altLabel={altLabel}
          sku={variant.sku}
          onUpload={onUploadImage}
          onAddFromUrl={onAddImageFromUrl}
          onDelete={onDeleteImage}
          onSetPrimary={onSetPrimaryImage}
        />
      </div>
      <div className="variant-detail-price-card">
        <PriceEvolutionCard
          latestPrice={variant.latest_price}
          historyState={historyState}
          onRetry={onRetryHistory}
        />
      </div>
    </div>
  );

  if (presentation === "sidebar") {
    return (
      <div
        className="single-variant-sidebar-panel space-y-4"
        role="region"
        aria-label="Imagen y precio"
      >
        {mediaAndPrice}
      </div>
    );
  }

  return (
    <VariantDetailCard className="border-0 shadow-none">
      <VariantDetailHeader variant={variant} />

      <div className="variant-detail-grid p-4 sm:p-5">
        <div className="variant-detail-grid__main">
          <section aria-labelledby="variant-specs-full-heading">
            <h4
              id="variant-specs-full-heading"
              className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Especificaciones de variante
            </h4>
            {specs.length > 0 ? (
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {specs.map((spec) => (
                  <ProductSpecChip key={spec.key} spec={spec} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Sin especificaciones registradas.</p>
            )}
          </section>
        </div>

        <aside className="variant-detail-grid__aside">{mediaAndPrice}</aside>
      </div>
    </VariantDetailCard>
  );
}
