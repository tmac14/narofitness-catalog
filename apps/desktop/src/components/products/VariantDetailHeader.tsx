import type { ProductVariant } from "@/lib/api";
import { formatVariantField, topVariantSpecs, variantDisplayTitle } from "@/lib/variantDetailMeta";
import { ProductSpecChip } from "./ProductSpecChip";

type VariantDetailHeaderProps = {
  variant: ProductVariant;
};

export function VariantDetailHeader({ variant }: VariantDetailHeaderProps) {
  const title = variantDisplayTitle(variant);
  const highlightSpecs = topVariantSpecs(variant, 3);

  return (
    <header className="variant-detail-header">
      <div className="min-w-0 flex-1 space-y-1.5">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Variante seleccionada
        </p>
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <p className="font-mono text-lg font-bold tracking-tight text-primary sm:text-xl">
            {variant.sku}
          </p>
          <p className="min-w-0 text-sm font-medium text-foreground sm:text-base" title={title}>
            {title}
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          <span>
            Proveedor{" "}
            <span className="font-medium text-foreground">
              {formatVariantField(variant.supplier_code)}
            </span>
          </span>
          <span className="mx-2 text-border" aria-hidden="true">
            ·
          </span>
          <span>
            EAN{" "}
            <span className="font-mono font-medium text-foreground">
              {formatVariantField(variant.ean)}
            </span>
          </span>
        </p>
      </div>

      {highlightSpecs.length > 0 ? (
        <div className="flex flex-wrap gap-2 lg:max-w-[42%] lg:justify-end">
          {highlightSpecs.map((spec) => (
            <ProductSpecChip key={spec.key} spec={spec} size="compact" className="min-w-[5.5rem]" />
          ))}
        </div>
      ) : null}
    </header>
  );
}
