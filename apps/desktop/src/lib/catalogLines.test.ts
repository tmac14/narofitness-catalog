import { describe, expect, it, vi } from "vitest";

import {
  applySortOrderUpdates,
  buildSortOrderUpdates,
  filterSortOrderChanges,
  hasOrderChanged,
  mapReorderError,
  orderSaveButtonLabel,
  ORDER_SAVE_COPY,
  reorderLines,
} from "@/lib/catalogLines";

describe("catalogLines reorder", () => {
  const lines = [
    { id: "1", sort_order: 0 },

    { id: "2", sort_order: 1 },

    { id: "3", sort_order: 2 },
  ];

  it("reorderLines moves item", () => {
    const next = reorderLines(lines, 0, 2);

    expect(next.map((l) => l.id)).toEqual(["2", "3", "1"]);
  });

  it("hasOrderChanged detects id sequence change", () => {
    const reordered = reorderLines(lines, 0, 2);

    expect(hasOrderChanged(lines, reordered)).toBe(true);

    expect(hasOrderChanged(lines, lines)).toBe(false);
  });

  it("buildSortOrderUpdates assigns sequential sort_order", () => {
    const updates = buildSortOrderUpdates(reorderLines(lines, 2, 0));

    expect(updates).toEqual([
      { id: "3", sort_order: 0 },

      { id: "1", sort_order: 1 },

      { id: "2", sort_order: 2 },
    ]);
  });

  it("filterSortOrderChanges skips unchanged rows", () => {
    const updates = buildSortOrderUpdates(lines);

    expect(filterSortOrderChanges(updates, lines)).toEqual([]);

    const reordered = buildSortOrderUpdates(reorderLines(lines, 0, 2));

    const changed = filterSortOrderChanges(reordered, lines);

    expect(changed).toHaveLength(3);

    expect(changed.map((c) => c.id).sort()).toEqual(["1", "2", "3"]);
  });

  it("applySortOrderUpdates returns skipped when nothing changed", async () => {
    const result = await applySortOrderUpdates(
      buildSortOrderUpdates(lines),

      lines,

      () => Promise.resolve({ updated: 0 }),
    );

    expect(result).toEqual({ updated: 0, skipped: true });
  });

  it("applySortOrderUpdates calls bulk reorder with changed items", async () => {
    const server = [
      { id: "1", sort_order: 0 },

      { id: "2", sort_order: 1 },

      { id: "3", sort_order: 2 },
    ];

    const updates = buildSortOrderUpdates(reorderLines(server, 0, 2));

    const reordered = vi.fn().mockResolvedValue({ updated: 3 });

    const result = await applySortOrderUpdates(updates, server, reordered);

    expect(reordered).toHaveBeenCalledOnce();

    expect(reordered.mock.calls[0][0]).toHaveLength(3);

    expect(result).toEqual({ updated: 3, skipped: false });
  });

  it("applySortOrderUpdates propagates bulk failure", async () => {
    const server = [
      { id: "1", sort_order: 0 },

      { id: "2", sort_order: 1 },
    ];

    const updates = buildSortOrderUpdates(reorderLines(server, 0, 1));

    const reordered = vi.fn().mockRejectedValue(new Error("Catalog not found"));

    await expect(applySortOrderUpdates(updates, server, reordered)).rejects.toThrow(
      "Catalog not found",
    );
  });

  it("orderSaveButtonLabel reflects saving state", () => {
    expect(orderSaveButtonLabel(false)).toBe("Guardar orden");
    expect(orderSaveButtonLabel(true)).toBe("Guardando orden…");
  });

  it("ORDER_SAVE_COPY provides stable user-facing strings", () => {
    expect(ORDER_SAVE_COPY.toastSuccess).toBe("Orden guardado");
    expect(ORDER_SAVE_COPY.toastNoop).toBe("El orden ya está guardado");
  });

  it("mapReorderError translates known server messages", () => {
    expect(mapReorderError(new Error("Catalog not found"))).toBe("Catálogo no encontrado");

    expect(mapReorderError(new Error("Duplicate item ids in reorder request"))).toBe(
      "La solicitud contiene productos duplicados",
    );

    expect(mapReorderError(new Error("One or more item ids are not in this catalog"))).toBe(
      "Uno o más productos no pertenecen a este catálogo",
    );

    expect(mapReorderError(new Error("network"))).toBe(
      "No se pudo guardar el orden. Inténtalo de nuevo.",
    );
  });
});
