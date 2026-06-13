/** Row selection helpers for builder tables. */

export function isPageFullySelected<T extends { master_id: string }>(
  pageItems: T[],
  selected: Set<string>,
): boolean {
  return pageItems.length > 0 && pageItems.every((p) => selected.has(p.master_id));
}

export function togglePageSelection<T extends { master_id: string }>(
  pageItems: T[],
  selected: Set<string>,
): Set<string> {
  const next = new Set(selected);
  if (isPageFullySelected(pageItems, selected)) {
    for (const p of pageItems) next.delete(p.master_id);
  } else {
    for (const p of pageItems) next.add(p.master_id);
  }
  return next;
}

export function selectAllFiltered<T extends { master_id: string }>(items: T[]): Set<string> {
  return new Set(items.map((p) => p.master_id));
}

export function toggleItemSelection(selected: Set<string>, masterId: string): Set<string> {
  const next = new Set(selected);
  if (next.has(masterId)) next.delete(masterId);
  else next.add(masterId);
  return next;
}

/** Label for bulk bar when selection spans filtered results (may include other pages). */
export function filteredSelectionLabel(
  selectedCount: number,
  filteredCount: number,
  pageItemCount: number,
): string {
  if (selectedCount === 0) {
    return `${filteredCount} visibles`;
  }
  const crossPage = filteredCount > pageItemCount ? " · incluye otras páginas" : "";
  return `${selectedCount} seleccionados (filtro actual${crossPage})`;
}
