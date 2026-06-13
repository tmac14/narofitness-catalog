import { describe, expect, it } from "vitest";
import {
  isPageFullySelected,
  selectAllFiltered,
  toggleItemSelection,
  togglePageSelection,
  filteredSelectionLabel,
} from "@/lib/selection";

const rows = [{ master_id: "a" }, { master_id: "b" }, { master_id: "c" }];

describe("selection helpers", () => {
  it("togglePageSelection selects and clears page", () => {
    let selected = togglePageSelection(rows.slice(0, 2), new Set());
    expect([...selected]).toEqual(["a", "b"]);

    selected = togglePageSelection(rows.slice(0, 2), selected);
    expect(selected.size).toBe(0);
  });

  it("isPageFullySelected detects full page selection", () => {
    expect(isPageFullySelected(rows.slice(0, 2), new Set(["a", "b"]))).toBe(true);
    expect(isPageFullySelected(rows.slice(0, 2), new Set(["a"]))).toBe(false);
  });

  it("selectAllFiltered returns all master ids", () => {
    const all = selectAllFiltered(rows);
    expect(all.size).toBe(3);
  });

  it("toggleItemSelection toggles single id", () => {
    let s = toggleItemSelection(new Set(), "a");
    expect(s.has("a")).toBe(true);
    s = toggleItemSelection(s, "a");
    expect(s.has("a")).toBe(false);
  });

  it("filteredSelectionLabel clarifies cross-page selection", () => {
    expect(filteredSelectionLabel(0, 120, 50)).toBe("120 visibles");
    expect(filteredSelectionLabel(3, 120, 50)).toContain("incluye otras páginas");
    expect(filteredSelectionLabel(2, 10, 10)).not.toContain("incluye otras páginas");
  });
});
