import type { ProductVariant, VariantPriceHistoryItem } from "@/lib/api";

/**
 * Canonical date for a price history point.
 * Priority: effective_date (commercial validity) → imported_at (import timestamp).
 */
export function getPriceHistoryPointDate(item: VariantPriceHistoryItem): string | null {
  const effective = item.effective_date?.trim();
  if (effective) return effective;

  const imported = item.imported_at?.trim();
  return imported || null;
}

/** Human-readable source label from API fields; null when no source metadata exists. */
export function getPriceHistorySourceLabel(item: VariantPriceHistoryItem): string | null {
  const filename = item.source_filename?.trim();
  if (filename) return filename;

  const listId = item.list_id?.trim();
  if (listId) return listId;

  return null;
}

export type VariantPriceHistoryState = {
  status: "loading" | "loaded" | "error";
  items: VariantPriceHistoryItem[];
  errorMessage?: string;
};

export type MonthlyPricePoint = {
  monthKey: string;
  label: string;
  price: number;
  sourceLabel: string | null;
  deltaPct: string | null;
  item: VariantPriceHistoryItem;
};

/** Parse API price strings (e.g. "19,39", "19.39 €") for comparisons and chart scale. */
export function parsePriceAmount(amount: string): number {
  const normalized = amount.replace(/[^\d,.-]/g, "").replace(",", ".");
  const value = Number.parseFloat(normalized);
  return Number.isFinite(value) ? value : 0;
}

const euroPriceFormatter = new Intl.NumberFormat("es-ES", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  useGrouping: true,
});

function parsePriceForDisplay(amount: string): number | null {
  const trimmed = amount
    .trim()
    .replace(/\s*€\s*$/, "")
    .trim();
  if (!/\d/.test(trimmed)) return null;

  if (trimmed.includes(",")) {
    const normalized = trimmed.replace(/\./g, "").replace(",", ".");
    const value = Number.parseFloat(normalized);
    return Number.isFinite(value) ? value : null;
  }

  const value = Number.parseFloat(trimmed.replace(/[^\d.-]/g, ""));
  return Number.isFinite(value) ? value : null;
}

function formatEuroAmount(value: number): string {
  const formatted = euroPriceFormatter.format(value);
  if (value >= 1000 && !formatted.includes(".")) {
    const [intPart, decPart = "00"] = value.toFixed(2).split(".");
    return `${intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${decPart}`;
  }
  return formatted;
}

/** Display price in European format, e.g. "3.381,30 €". Returns null when empty. */
export function formatPriceDisplay(amount: string | null | undefined): string | null {
  const trimmed = amount?.trim();
  if (!trimmed) return null;

  if (/^\d{1,3}(\.\d{3})*,\d{2}\s*€$/.test(trimmed)) {
    return trimmed;
  }

  const value = parsePriceForDisplay(trimmed);
  if (value == null) return null;

  return `${formatEuroAmount(value)} €`;
}

function monthKeyFromDate(dateStr: string): string {
  const isoMatch = dateStr.match(/^(\d{4})-(\d{2})/);
  if (isoMatch) return `${isoMatch[1]}-${isoMatch[2]}`;

  const parsed = Date.parse(dateStr);
  if (!Number.isNaN(parsed)) {
    const d = new Date(parsed);
    const month = String(d.getMonth() + 1).padStart(2, "0");
    return `${d.getFullYear()}-${month}`;
  }

  return dateStr.slice(0, 7);
}

function monthShortLabel(monthKey: string): string {
  const [year, month] = monthKey.split("-").map(Number);
  if (!year || !month) return monthKey;
  const d = new Date(year, month - 1, 1);
  return d.toLocaleDateString("es-ES", { month: "short", year: "2-digit" });
}

function comparePointDates(a: string, b: string): number {
  const ta = Date.parse(a);
  const tb = Date.parse(b);
  if (!Number.isNaN(ta) && !Number.isNaN(tb)) return ta - tb;
  return a.localeCompare(b);
}

/** Group history by calendar month; last point per month wins (by canonical date). */
export function buildMonthlyPriceSeries(items: VariantPriceHistoryItem[]): MonthlyPricePoint[] {
  if (items.length === 0) return [];

  const sorted = [...items].sort((a, b) => {
    const dateA = getPriceHistoryPointDate(a) ?? "";
    const dateB = getPriceHistoryPointDate(b) ?? "";
    return comparePointDates(dateA, dateB);
  });

  const byMonth = new Map<string, VariantPriceHistoryItem>();
  for (const item of sorted) {
    const dateStr = getPriceHistoryPointDate(item);
    if (!dateStr) continue;
    byMonth.set(monthKeyFromDate(dateStr), item);
  }

  return [...byMonth.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([monthKey, item]) => ({
      monthKey,
      label: monthShortLabel(monthKey),
      price: parsePriceAmount(item.price_amount),
      sourceLabel: getPriceHistorySourceLabel(item),
      deltaPct: item.delta_pct_vs_previous,
      item,
    }));
}

export function formatPriceHistoryDisplayDate(item: VariantPriceHistoryItem): string {
  const dateStr = getPriceHistoryPointDate(item);
  if (!dateStr) return "—";
  const parsed = Date.parse(dateStr);
  if (Number.isNaN(parsed)) return dateStr;
  return new Date(parsed).toLocaleDateString("es-ES");
}

export function masterPriceSummaryLabel(variants: ProductVariant[]): string {
  const withPrice = variants.filter((variant) => variant.latest_price?.trim());
  if (withPrice.length === 0) return "Sin precio registrado";

  if (withPrice.length === 1) return withPrice[0].latest_price!.trim();

  let minEntry = withPrice[0];
  let maxEntry = withPrice[0];
  let minNum = parsePriceAmount(withPrice[0].latest_price!);
  let maxNum = minNum;

  for (const variant of withPrice.slice(1)) {
    const value = parsePriceAmount(variant.latest_price!);
    if (value < minNum) {
      minNum = value;
      minEntry = variant;
    }
    if (value > maxNum) {
      maxNum = value;
      maxEntry = variant;
    }
  }

  if (minNum === maxNum) return minEntry.latest_price!.trim();
  return `${minEntry.latest_price!.trim()} – ${maxEntry.latest_price!.trim()}`;
}
