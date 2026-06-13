import type { ProductMasterDetail } from "@/lib/api";
import { hasAnyDisplayedSpecs } from "@/lib/productSpecs";

export function variantCountLabel(count: number): string {
  if (count === 1) return "1 variante";
  return `${count} variantes`;
}

export function categoryBreadcrumb(master: ProductMasterDetail): string | null {
  const parent = master.category_parent_name?.trim();
  const sub = master.category_sub_name?.trim();
  const name = master.category_name?.trim();

  if (parent && sub && parent.toLowerCase() !== sub.toLowerCase()) {
    return `${parent} › ${sub}`;
  }
  return sub || parent || name || null;
}

export function primaryReference(master: ProductMasterDetail): string | null {
  if (master.references.length > 0) return master.references[0];
  if (master.variants.length > 0) return master.variants[0].sku;
  return null;
}

export function formatReferencesSummary(master: ProductMasterDetail): string {
  const refs =
    master.references.length > 0
      ? master.references
      : master.variants.map((variant) => variant.sku);
  if (refs.length === 0) return "—";
  if (refs.length === 1) return refs[0];
  if (refs.length <= 2) return refs.join(", ");
  return `${refs.slice(0, 2).join(", ")} +${refs.length - 2}`;
}

export function masterThumbnailUrl(master: ProductMasterDetail, apiBase: string): string | null {
  if (master.image_url) return `${apiBase}${master.image_url}`;
  const primary = master.images.find((img) => img.is_primary) ?? master.images[0];
  return primary ? `${apiBase}${primary.url}` : null;
}

export type ProductDetailBadge = {
  id: string;
  label: string;
  variant: "secondary" | "outline";
};

export function productDetailBadges(master: ProductMasterDetail): ProductDetailBadge[] {
  const badges: ProductDetailBadge[] = [];

  if (master.images.length === 0 && !master.image_url) {
    badges.push({ id: "no-images", label: "Sin imágenes", variant: "outline" });
  }
  if (!hasAnyDisplayedSpecs(master)) {
    badges.push({ id: "no-specs", label: "Sin características", variant: "outline" });
  }

  return badges;
}
