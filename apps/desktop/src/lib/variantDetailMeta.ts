import type { ProductVariant, SpecValue } from "@/lib/api";
import { specHasValue } from "@/lib/productSpecs";

export function variantDisplayTitle(variant: Pick<ProductVariant, "display_name" | "sku">): string {
  const name = variant.display_name?.trim();
  return name || variant.sku;
}

export function formatVariantField(value: string | null | undefined): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : "—";
}

export function variantSpecsWithValue(specs: SpecValue[] | undefined): SpecValue[] {
  return (specs ?? []).filter(specHasValue);
}

export function topVariantSpecs(variant: Pick<ProductVariant, "specs">, limit = 3): SpecValue[] {
  return variantSpecsWithValue(variant.specs).slice(0, Math.max(0, limit));
}
