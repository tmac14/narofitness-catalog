import type { ProductMaster } from "@/lib/api";

export function variantCount(master: ProductMaster): number {
  return master.variants?.length ?? master.variant_count;
}

export function hasMultipleVariants(master: ProductMaster): boolean {
  return variantCount(master) > 1;
}

export function formatReferences(references: string[]): string {
  if (references.length === 0) return "—";
  if (references.length === 1) return references[0];
  if (references.length <= 2) return references.join(", ");
  return `${references.slice(0, 2).join(", ")} +${references.length - 2}`;
}

export function parentReference(master: ProductMaster): string {
  const refs =
    master.references.length > 0
      ? master.references
      : (master.variants ?? []).map((variant) => variant.sku);
  return formatReferences(refs);
}

export function parentPrice(master: ProductMaster): string {
  if (master.price) return master.price;
  const variants = master.variants ?? [];
  if (variants.length === 1) return variants[0].price ?? "—";
  return "—";
}
