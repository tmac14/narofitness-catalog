import type { Platform } from "./breakpoints";

/** Primary data presentation mode — screen-agnostic policy output. */
export type DataViewMode = "table" | "cards" | "sheet";

/** Declared column/comparison complexity for policy input only. */
export type TableComplexity = "simple" | "moderate" | "complex";

export type DataViewPolicyInput = {
  platform: Platform;
  /** Visible data columns excluding selection/actions. */
  columnCount: number;
  complexity: TableComplexity;
  /** Row comparison across columns is the primary task (e.g. price diff). */
  requiresComparison?: boolean;
  /** Row opens a detail surface (sheet/drawer) on tap. */
  hasRowDetail?: boolean;
  /** Bulk selection/actions are required in the view. */
  hasBulkActions?: boolean;
};

/**
 * Pure policy: choose table vs cards vs sheet from platform + declared complexity.
 * Does not import UI components or screen-specific data shapes.
 *
 * Rules (UX 3.0):
 * - mobile: never default to dense tables; cards (sheet when row detail is primary).
 * - tablet: tables only for moderate width-friendly sets; otherwise cards/sheet.
 * - desktop/wide: tables by default unless excessively wide/complex.
 */
export function resolveDataViewMode(input: DataViewPolicyInput): DataViewMode {
  const {
    platform,
    columnCount,
    complexity,
    requiresComparison = false,
    hasRowDetail = false,
    hasBulkActions = false,
  } = input;

  if (platform === "mobile") {
    if (hasRowDetail || hasBulkActions) return "sheet";
    return "cards";
  }

  if (platform === "tablet") {
    if (requiresComparison && columnCount <= 5) {
      return "table";
    }

    const isComplex = complexity === "complex";
    const tooWide = columnCount > 4 || isComplex;
    if (tooWide) {
      return hasRowDetail ? "sheet" : "cards";
    }
    if (columnCount <= 4) {
      return "table";
    }
    return hasRowDetail ? "sheet" : "cards";
  }

  // desktop | wide
  if (complexity === "complex" && columnCount > 8) {
    return hasRowDetail ? "sheet" : "cards";
  }
  return "table";
}

/** Whether horizontal scroll is an acceptable fallback for the resolved mode. */
export function allowsHorizontalScroll(mode: DataViewMode, platform: Platform): boolean {
  if (mode !== "table") return false;
  return platform === "tablet" || platform === "desktop" || platform === "wide";
}
