import type {
  ProductMaster,
  ProductMasterDetail,
  ProductMasterListVariant,
  ProductVariant,
  VariantAttributeColumn,
} from "@/lib/api";
import { variantSpecValueForColumnKey } from "@/lib/productSpecs";

export const BRAND_COLUMN_KEY = "brand";
export const VARIANT_LABEL_COLUMN_KEY = "variant_label";
export const MIXED_BRAND_DISPLAY = "Varias marcas";

export type VariantColumnsLayout = {
  /** variant_label — rendered immediately after photo / row start */
  leadingColumns: VariantAttributeColumn[];
  /** brand — rendered after Referencia (and Proveedor in detail) */
  identityColumns: VariantAttributeColumn[];
  /** specs — rendered after Marca */
  specColumns: VariantAttributeColumn[];
};

/** Partition API columns for visual layout without inventing columns. */
export function orderVariantColumnsForDisplay(
  columns: VariantAttributeColumn[],
): VariantColumnsLayout {
  const leadingColumns: VariantAttributeColumn[] = [];
  const identityColumns: VariantAttributeColumn[] = [];
  const specColumns: VariantAttributeColumn[] = [];

  for (const column of columns) {
    if (column.key === VARIANT_LABEL_COLUMN_KEY) {
      leadingColumns.push(column);
    } else if (column.key === BRAND_COLUMN_KEY) {
      identityColumns.push(column);
    } else {
      specColumns.push(column);
    }
  }

  return { leadingColumns, identityColumns, specColumns };
}

/** Dynamic column keys in visual order after fixed Referencia (list) or Ref+Proveedor (detail). */
export function presentationDynamicKeysAfterReference(layout: VariantColumnsLayout): string[] {
  return [
    ...layout.identityColumns.map((column) => column.key),
    ...layout.specColumns.map((column) => column.key),
  ];
}

export function layoutListVariantColumns(master: ProductMaster): VariantColumnsLayout {
  return orderVariantColumnsForDisplay(master.variant_columns ?? []);
}

export function layoutDetailVariantColumns(
  master: Pick<ProductMasterDetail, "variant_columns">,
): VariantColumnsLayout {
  return orderVariantColumnsForDisplay(master.variant_columns ?? []);
}

/** Recommended source for master brand in UI — never infer from a variant row. */
export function masterBrandDisplay(
  master: Pick<ProductMaster, "brand_display" | "brand">,
): string | null {
  const display = master.brand_display?.trim();
  if (display) return display;
  const brand = master.brand?.trim();
  return brand || null;
}

export function isMixedBrandMaster(master: Pick<ProductMaster, "brand_mode">): boolean {
  return master.brand_mode === "mixed";
}

export function masterBrandTitle(
  master: Pick<ProductMaster, "brand_mode" | "brand_display" | "brand">,
): string | undefined {
  if (isMixedBrandMaster(master)) return "Marcas distintas por variante";
  const label = masterBrandDisplay(master);
  return label ?? undefined;
}

function normalizeCellValue(value: string | null | undefined): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : "—";
}

export function getListVariantAttributeValue(
  variant: ProductMasterListVariant,
  columnKey: string,
): string {
  const fromAttributes = variant.attributes?.[columnKey];
  if (fromAttributes != null && fromAttributes.trim() !== "") return fromAttributes;

  if (columnKey === BRAND_COLUMN_KEY) {
    return normalizeCellValue(variant.brand_display ?? variant.brand);
  }
  if (columnKey === VARIANT_LABEL_COLUMN_KEY) {
    return normalizeCellValue(variant.variant_label);
  }

  return "—";
}

export function getDetailVariantCellValue(variant: ProductVariant, columnKey: string): string {
  if (columnKey === BRAND_COLUMN_KEY) {
    return normalizeCellValue(variant.brand_display ?? variant.brand);
  }
  if (columnKey === VARIANT_LABEL_COLUMN_KEY) {
    return normalizeCellValue(variant.variant_label);
  }
  return variantSpecValueForColumnKey(variant, columnKey);
}

export function resolveDetailVariantColumns(
  master: Pick<ProductMaster, "variant_columns">,
): VariantAttributeColumn[] {
  return master.variant_columns ?? [];
}

/** Spec-only columns for characteristics table — excludes brand/variant name shown in variants panel. */
export function characteristicsVariantColumns(
  master: Pick<ProductMaster, "variant_columns">,
): VariantAttributeColumn[] {
  return (master.variant_columns ?? []).filter(
    (column) => column.key !== BRAND_COLUMN_KEY && column.key !== VARIANT_LABEL_COLUMN_KEY,
  );
}
