export type SortableLine = {
  id: string;

  sort_order: number;
};

export function reorderLines<T extends SortableLine>(
  items: T[],
  fromIndex: number,
  toIndex: number,
): T[] {
  if (
    fromIndex === toIndex ||
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= items.length ||
    toIndex >= items.length
  ) {
    return items;
  }

  const next = [...items];

  const [moved] = next.splice(fromIndex, 1);

  next.splice(toIndex, 0, moved);

  return next;
}

export function hasOrderChanged(original: SortableLine[], current: SortableLine[]): boolean {
  if (original.length !== current.length) return true;

  return original.some((item, i) => item.id !== current[i]?.id);
}

export function buildSortOrderUpdates(
  current: SortableLine[],
): { id: string; sort_order: number }[] {
  return current.map((item, index) => ({
    id: item.id,

    sort_order: index,
  }));
}

export function filterSortOrderChanges(
  updates: { id: string; sort_order: number }[],

  serverSorted: SortableLine[],
): { id: string; sort_order: number }[] {
  const serverById = new Map(serverSorted.map((i) => [i.id, i.sort_order]));

  return updates.filter((u) => serverById.get(u.id) !== u.sort_order);
}

export type BulkSortOrderResult = {
  updated: number;

  skipped: boolean;
};

export async function applySortOrderUpdates(
  updates: { id: string; sort_order: number }[],

  serverSorted: SortableLine[],

  reorder: (items: { id: string; sort_order: number }[]) => Promise<{ updated: number }>,
): Promise<BulkSortOrderResult> {
  const changed = filterSortOrderChanges(updates, serverSorted);

  if (changed.length === 0) return { updated: 0, skipped: true };

  const result = await reorder(changed);

  return { updated: result.updated, skipped: false };
}

const REORDER_ERROR_MESSAGES: Record<string, string> = {
  "Catalog not found": "Catálogo no encontrado",

  "Duplicate item ids in reorder request": "La solicitud contiene productos duplicados",

  "One or more item ids are not in this catalog":
    "Uno o más productos no pertenecen a este catálogo",
};

export function mapReorderError(error: unknown): string {
  const message = error instanceof Error ? error.message : "";

  return REORDER_ERROR_MESSAGES[message] ?? "No se pudo guardar el orden. Inténtalo de nuevo.";
}

/** Sonner toast id — prevents duplicate order-save toasts on rapid clicks. */
export const ORDER_SAVE_TOAST_ID = "catalog-line-order-save";

export function orderSaveButtonLabel(saving: boolean): string {
  return saving ? "Guardando orden…" : "Guardar orden";
}

export const ORDER_SAVE_COPY = {
  bannerTitle: "Orden modificado sin guardar",
  bannerHintIdle:
    "Guarda para persistir el cambio. La vista previa PDF quedará desactualizada hasta que la regeneres.",
  bannerHintSaving: "Guardando el nuevo orden en el catálogo…",
  discardLabel: "Descartar cambios",
  discardDisabledTitle: "Espera a que termine el guardado",
  dndDisabledReason: "Guardando orden…",
  toastSuccess: "Orden guardado",
  toastNoop: "El orden ya está guardado",
} as const;
