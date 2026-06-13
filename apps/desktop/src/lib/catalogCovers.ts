import type { CatalogSectionCover, Category } from "@/lib/api";
import { API_BASE } from "@/lib/api";

/** Resolve API media path to a browser-loadable URL. */
export function resolveCatalogMediaUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${API_BASE}${url.startsWith("/") ? url : `/${url}`}`;
}

export function indexCategoriesByName(nodes: Category[]): Map<string, string> {
  const map = new Map<string, string>();
  function walk(items: Category[]) {
    for (const node of items) {
      map.set(node.name, node.id);
      if (node.children?.length) walk(node.children);
    }
  }
  walk(nodes);
  return map;
}

export type SectionCoverEditorRow = {
  sectionName: string;
  productCount: number;
  categoryId: string | null;
  coverImageUrl: string | null;
  description: string | null;
  canEdit: boolean;
};

export function buildSectionCoverEditorRows(
  bySection: Record<string, number>,
  sectionCovers: CatalogSectionCover[],
  categoryByName: Map<string, string>,
): SectionCoverEditorRow[] {
  const coverByCategoryId = new Map(sectionCovers.map((row) => [row.category_id, row]));

  return Object.entries(bySection)
    .sort(([a], [b]) => a.localeCompare(b, "es"))
    .map(([sectionName, productCount]) => {
      if (sectionName === "General") {
        return {
          sectionName,
          productCount,
          categoryId: null,
          coverImageUrl: null,
          description: null,
          canEdit: false,
        };
      }

      const matchedCover = sectionCovers.find((row) => row.category_name === sectionName);
      const categoryId = matchedCover?.category_id ?? categoryByName.get(sectionName) ?? null;
      const cover = categoryId ? (coverByCategoryId.get(categoryId) ?? matchedCover ?? null) : null;

      return {
        sectionName,
        productCount,
        categoryId,
        coverImageUrl: cover?.cover_image_url ?? null,
        description: cover?.description ?? null,
        canEdit: categoryId !== null,
      };
    });
}
