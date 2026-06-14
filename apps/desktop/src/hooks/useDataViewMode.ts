import { useSyncExternalStore } from "react";

import { BREAKPOINT_PX } from "@/lib/responsive/breakpoints";
import { classifyPlatformWidth } from "@/lib/responsive/platform";
import {
  resolveDataViewMode,
  type DataViewMode,
  type DataViewPolicyInput,
} from "@/lib/responsive/tablePolicy";
import type { Platform } from "@/lib/responsive/breakpoints";

export type DataViewModeResult = {
  platform: Platform;
  mode: DataViewMode;
  showTable: boolean;
  showCards: boolean;
};

export type UseDataViewModeOptions = Omit<DataViewPolicyInput, "platform">;

/** Products list policy — 5 visible columns with multi-variant row detail. */
export const PRODUCTS_LIST_VIEW_POLICY: UseDataViewModeOptions = {
  columnCount: 5,
  complexity: "moderate",
  hasRowDetail: true,
};

/**
 * Suppliers import-profiles panel — cards ≤1023px, table ≥1024px (UX30-D6).
 * columnCount: 5 (not 3) so tablePolicy treats tablet as tooWide and returns cards
 * until desktop; the real profile table has 3 columns.
 */
export const SUPPLIERS_PROFILES_VIEW_POLICY: UseDataViewModeOptions = {
  columnCount: 5,
  complexity: "simple",
  hasRowDetail: false,
};

/** Price list diff — cards ≤1023px, table ≥1024px; 6-column comparison semantics. */
export const PRICE_LIST_DIFF_VIEW_POLICY: UseDataViewModeOptions = {
  columnCount: 6,
  complexity: "moderate",
  requiresComparison: true,
  hasRowDetail: false,
};

export function computeDataViewModeFromWidth(
  widthPx: number,
  options: UseDataViewModeOptions,
): DataViewModeResult {
  const platform = classifyPlatformWidth(widthPx);
  const mode = resolveDataViewMode({ platform, ...options });
  return {
    platform,
    mode,
    showTable: mode === "table",
    showCards: mode !== "table",
  };
}

function getViewportWidth(): number {
  if (typeof window === "undefined") return BREAKPOINT_PX.desktopMin;
  return window.innerWidth;
}

function getServerViewportWidth(): number {
  return BREAKPOINT_PX.desktopMin;
}

function subscribeViewport(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("resize", onStoreChange);
  return () => window.removeEventListener("resize", onStoreChange);
}

export function useDataViewMode(options: UseDataViewModeOptions): DataViewModeResult {
  const width = useSyncExternalStore(subscribeViewport, getViewportWidth, getServerViewportWidth);
  return computeDataViewModeFromWidth(width, options);
}
