import type { LucideIcon } from "lucide-react";
import { Settings } from "lucide-react";
import type { CatalogListItem, ProductVariant, Supplier } from "@/lib/api";

export type CommandPaletteGroup = "nav" | "search" | "action";

export type CommandPaletteItem = {
  id: string;
  label: string;
  group: CommandPaletteGroup;
  icon?: LucideIcon;
  hint?: string;
  keywords?: string[];
  onSelect: () => void;
};

export const COMMAND_PALETTE_SEARCH_DEBOUNCE_MS = 300;
export const COMMAND_PALETTE_MIN_QUERY_LENGTH = 3;
export const COMMAND_PALETTE_MAX_SEARCH_RESULTS_PER_KIND = 5;

export function isMacPlatform(): boolean {
  if (typeof navigator === "undefined") return false;
  return /Mac|iPhone|iPad|iPod/i.test(navigator.platform);
}

export function formatPaletteShortcutHint(): string {
  return isMacPlatform() ? "⌘K" : "Ctrl+K";
}

export function isEditableKeyboardTarget(target: EventTarget | null): boolean {
  if (target == null || typeof target !== "object") return false;
  const element = target as HTMLElement;
  if ("isContentEditable" in element && element.isContentEditable) return true;
  const tag = "tagName" in element ? element.tagName : undefined;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (typeof element.closest === "function") {
    return Boolean(element.closest("[contenteditable='true']"));
  }
  return false;
}

export function shouldOpenPaletteFromKeyboard(event: KeyboardEvent): boolean {
  if (event.defaultPrevented) return false;
  if (event.key.toLowerCase() !== "k") return false;
  if (!event.ctrlKey && !event.metaKey) return false;
  if (event.altKey || event.shiftKey) return false;
  if (isEditableKeyboardTarget(event.target)) return false;
  return true;
}

export function buildPaletteActionCommands(handlers: {
  onOpenSettings: () => void;
  onOpenJobsPanel: () => void;
}): CommandPaletteItem[] {
  return [
    {
      id: "action:settings",
      label: "Configuración",
      group: "action",
      icon: Settings,
      keywords: ["settings", "ajustes", "preferencias"],
      onSelect: handlers.onOpenSettings,
    },
    {
      id: "action:jobs-panel",
      label: "Abrir panel de tareas",
      group: "action",
      keywords: ["jobs", "tareas", "procesos", "status"],
      onSelect: handlers.onOpenJobsPanel,
    },
  ];
}

export function filterCatalogSearchResults(
  catalogs: CatalogListItem[],
  query: string,
  limit = COMMAND_PALETTE_MAX_SEARCH_RESULTS_PER_KIND,
): CatalogListItem[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];
  return catalogs
    .filter((catalog) => catalog.name.toLowerCase().includes(normalized))
    .slice(0, limit);
}

export function filterSupplierSearchResults(
  suppliers: Supplier[],
  query: string,
  limit = COMMAND_PALETTE_MAX_SEARCH_RESULTS_PER_KIND,
): Supplier[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];
  return suppliers
    .filter(
      (supplier) =>
        supplier.name.toLowerCase().includes(normalized) ||
        supplier.code.toLowerCase().includes(normalized),
    )
    .slice(0, limit);
}

export function variantSearchLabel(variant: ProductVariant): string {
  const name = variant.display_name ?? variant.master_name ?? variant.sku;
  const brand = variant.brand_display ?? variant.brand;
  return brand ? `${name} · ${brand}` : name;
}

export function filterCommandPaletteItems(
  items: CommandPaletteItem[],
  query: string,
): CommandPaletteItem[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return items;

  return items.filter((item) => {
    if (item.label.toLowerCase().includes(normalized)) return true;
    if (item.hint?.toLowerCase().includes(normalized)) return true;
    return item.keywords?.some((keyword) => keyword.toLowerCase().includes(normalized)) ?? false;
  });
}

export const COMMAND_PALETTE_GROUP_LABELS: Record<CommandPaletteGroup, string> = {
  nav: "Navegar",
  search: "Buscar",
  action: "Acciones",
};

export const COMMAND_PALETTE_GROUP_ORDER: CommandPaletteGroup[] = ["nav", "search", "action"];
