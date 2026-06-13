import type { ProductMasterDetail } from "@/lib/api";

export function isSingleVariantProduct(master: Pick<ProductMasterDetail, "variants">): boolean {
  return master.variants.length === 1;
}

export function shouldShowVariantsTab(variantCount: number): boolean {
  return variantCount > 1;
}

export function getSingleVariant(master: ProductMasterDetail) {
  return master.variants.length === 1 ? master.variants[0] : null;
}
