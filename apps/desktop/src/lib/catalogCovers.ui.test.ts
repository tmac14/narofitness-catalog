import { describe, expect, it } from "vitest";
import type { CatalogSectionCover } from "./api";
import {
  buildSectionCoverEditorRows,
  indexCategoriesByName,
  resolveCatalogMediaUrl,
} from "./catalogCovers";

describe("catalogCovers helpers", () => {
  it("resolveCatalogMediaUrl prefixes relative API paths", () => {
    expect(resolveCatalogMediaUrl("/api/v1/media/cover.jpg")).toContain("/api/v1/media/cover.jpg");
    expect(resolveCatalogMediaUrl(null)).toBeNull();
    expect(resolveCatalogMediaUrl("https://cdn.example/cover.jpg")).toBe(
      "https://cdn.example/cover.jpg",
    );
  });

  it("buildSectionCoverEditorRows marks General as non-editable", () => {
    const rows = buildSectionCoverEditorRows(
      { General: 5, Discos: 10 },
      [],
      new Map([["Discos", "cat-discos"]]),
    );
    const general = rows.find((r) => r.sectionName === "General");
    const discos = rows.find((r) => r.sectionName === "Discos");
    expect(general?.canEdit).toBe(false);
    expect(general?.categoryId).toBeNull();
    expect(discos?.canEdit).toBe(true);
    expect(discos?.categoryId).toBe("cat-discos");
  });

  it("buildSectionCoverEditorRows merges existing section cover data", () => {
    const sectionCovers: CatalogSectionCover[] = [
      {
        category_id: "cat-discos",
        category_name: "Discos",
        cover_image_url: "/api/v1/media/section.png",
        description: "Texto",
      },
    ];
    const rows = buildSectionCoverEditorRows({ Discos: 3 }, sectionCovers, new Map());
    expect(rows[0].coverImageUrl).toContain("section.png");
    expect(rows[0].description).toBe("Texto");
  });

  it("indexCategoriesByName maps leaf category names to ids", () => {
    const map = indexCategoriesByName([
      {
        id: "root",
        name: "Fitness",
        parent_id: null,
        children: [{ id: "leaf", name: "Discos", parent_id: "root", children: [] }],
      },
    ]);
    expect(map.get("Discos")).toBe("leaf");
    expect(map.get("Fitness")).toBe("root");
  });
});
