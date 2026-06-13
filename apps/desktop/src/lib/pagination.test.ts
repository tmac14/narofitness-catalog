import { describe, expect, it } from "vitest";
import { clampPage, pageRangeLabel, paginate, totalPages } from "@/lib/pagination";

describe("pagination helpers", () => {
  it("paginate returns correct slice", () => {
    const items = [1, 2, 3, 4, 5, 6, 7];
    expect(paginate(items, 1, 3)).toEqual([1, 2, 3]);
    expect(paginate(items, 2, 3)).toEqual([4, 5, 6]);
    expect(paginate(items, 3, 3)).toEqual([7]);
  });

  it("totalPages returns at least 1", () => {
    expect(totalPages(0, 50)).toBe(1);
    expect(totalPages(51, 50)).toBe(2);
  });

  it("clampPage bounds page number", () => {
    expect(clampPage(5, 10, 50)).toBe(1);
    expect(clampPage(0, 100, 50)).toBe(1);
    expect(clampPage(3, 100, 50)).toBe(2);
  });

  it("pageRangeLabel formats range", () => {
    expect(pageRangeLabel(1, 50, 120)).toBe("1–50 de 120");
    expect(pageRangeLabel(3, 50, 120)).toBe("101–120 de 120");
    expect(pageRangeLabel(1, 50, 0)).toBe("0 de 0");
  });
});
