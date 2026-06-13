import type {
  ProductMaster,
  ProductMasterListVariant,
  ProductVariant,
  SpecValue,
  VariantAttributeColumn,
} from "@/lib/api";

const PESO_COLUMN_KEYS = new Set(["peso", "peso_kg", "peso_lb"]);

const FALLBACK_SPEC_LABELS: Record<string, string> = {
  peso: "Peso",
  peso_kg: "Peso",
  peso_lb: "Peso",
  color: "Color",
  capacidad_balones: "Capacidad (balones)",
};

export function humanizeSpecKey(key: string): string {
  return FALLBACK_SPEC_LABELS[key] ?? key.replace(/_/g, " ");
}

export function formatSpecLabel(spec: Pick<SpecValue, "key" | "label">): string {
  const label = spec.label?.trim();
  if (label) return label;
  return humanizeSpecKey(spec.key);
}

export function formatSpecValue(spec: Pick<SpecValue, "value">): string {
  const value = spec.value?.trim();
  return value ? value : "—";
}

export function specHasValue(spec: Pick<SpecValue, "value">): boolean {
  return spec.value != null && spec.value.trim() !== "";
}

export function hasMasterSpecs(specs?: SpecValue[]): boolean {
  return (specs ?? []).some(specHasValue);
}

export function hasVariantSpecs(variants: { specs?: SpecValue[] }[]): boolean {
  return variants.some((variant) => (variant.specs ?? []).some(specHasValue));
}

export function hasAnyDisplayedSpecs(master: {
  specs?: SpecValue[];
  variants: { specs?: SpecValue[] }[];
}): boolean {
  return hasMasterSpecs(master.specs) || hasVariantSpecs(master.variants);
}

/** Use API column definitions as-is — no client-side hiding or reordering. */
export function resolveListVariantColumns(master: ProductMaster): VariantAttributeColumn[] {
  return master.variant_columns ?? [];
}

/** Preserve variant order from API response. */
export function listVariantsInApiOrder(
  variants: ProductMasterListVariant[] | undefined,
): ProductMasterListVariant[] {
  return variants ?? [];
}

export { getListVariantAttributeValue } from "@/lib/variantRepresentation";

export function masterSpecsForDisplay(specs?: SpecValue[]): SpecValue[] {
  return (specs ?? []).filter(specHasValue);
}

export type VariantSpecColumn = {
  key: string;
  label: string;
  sortOrder: number;
};

function specColumnSortRank(key: string): number {
  return PESO_COLUMN_KEYS.has(key) ? 0 : 1;
}

/** Collect union of variant spec columns for detail tables (peso-family first, then sort_order). */
export function collectVariantSpecColumns(variants: ProductVariant[]): VariantSpecColumn[] {
  const byKey = new Map<string, VariantSpecColumn>();

  for (const variant of variants) {
    for (const spec of variant.specs ?? []) {
      if (!byKey.has(spec.key)) {
        byKey.set(spec.key, {
          key: spec.key,
          label: formatSpecLabel(spec),
          sortOrder: spec.sort_order ?? 999,
        });
      }
    }
  }

  return [...byKey.values()].sort((a, b) => {
    const rankA = specColumnSortRank(a.key);
    const rankB = specColumnSortRank(b.key);
    if (rankA !== rankB) return rankA - rankB;
    if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
    return a.label.localeCompare(b.label, "es");
  });
}

export function variantSpecValue(variant: ProductVariant, columnKey: string): string {
  const spec = (variant.specs ?? []).find((item) => item.key === columnKey);
  if (!spec) return "—";
  return formatSpecValue(spec);
}

/** Synthetic list/detail column `peso` maps to native weight specs on detail payloads. */
export const SYNTHETIC_PESO_COLUMN_KEY = "peso";

export function variantSpecValueForColumnKey(variant: ProductVariant, columnKey: string): string {
  if (columnKey === SYNTHETIC_PESO_COLUMN_KEY) {
    for (const key of PESO_COLUMN_KEYS) {
      const value = variantSpecValue(variant, key);
      if (value !== "—") return value;
    }
    return "—";
  }
  return variantSpecValue(variant, columnKey);
}

export function variantsWithDisplayableSpecs(variants: ProductVariant[]): ProductVariant[] {
  return variants.filter((variant) => (variant.specs ?? []).some(specHasValue));
}
