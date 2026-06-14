import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { Category } from "@/lib/api";
import { CategoryTreeNode } from "@/components/categories/CategoryTreeNode";
import { CategoryTree } from "@/components/categories/CategoryTree";

function makeCategory(overrides: Partial<Category> = {}): Category {
  return {
    id: "cat-1",
    name: "Raíz",
    parent_id: null,
    children: [],
    ...overrides,
  };
}

describe("CategoriesPage responsive tree", () => {
  const handlers = {
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onAddChild: vi.fn(),
  };

  it("renders CategoryTreeNode overflow menu with min-h-11 trigger, not inline sm buttons", () => {
    const html = renderToStaticMarkup(
      <CategoryTreeNode
        node={makeCategory({ name: "Electrónica" })}
        defaultExpanded={false}
        {...handlers}
      />,
    );
    expect(html).toContain("min-h-11");
    expect(html).toContain("category-tree-node__menu-btn");
    expect(html).toContain('aria-label="Acciones para Electrónica"');
    expect(html).not.toContain('size="sm"');
    expect(html).not.toMatch(/Editar<\/button>/);
  });

  it("renders aria-expanded on accordion toggle for nodes with children", () => {
    const html = renderToStaticMarkup(
      <CategoryTreeNode
        node={makeCategory({
          name: "Padre",
          children: [makeCategory({ id: "cat-2", name: "Hijo", parent_id: "cat-1" })],
        })}
        defaultExpanded={false}
        {...handlers}
      />,
    );
    expect(html).toContain("category-tree-node__toggle");
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain('aria-label="Expandir Padre"');
  });

  it("renders nested tree without table markup", () => {
    const tree: Category[] = [
      makeCategory({
        children: [
          makeCategory({
            id: "cat-2",
            name: "Subcategoría",
            parent_id: "cat-1",
            children: [
              makeCategory({ id: "cat-3", name: "Nieto", parent_id: "cat-2" }),
            ],
          }),
        ],
      }),
    ];

    const html = renderToStaticMarkup(
      <CategoryTree nodes={tree} defaultExpanded={true} {...handlers} />,
    );
    expect(html).toContain("category-tree");
    expect(html).toContain("category-tree-node__children");
    expect(html).toContain("Subcategoría");
    expect(html).toContain("Nieto");
    expect(html).not.toContain("<table");
  });
});
