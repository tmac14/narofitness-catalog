import type { Category } from "@/lib/api";
import { CategoryTreeNode } from "@/components/categories/CategoryTreeNode";

export function CategoryTree({
  nodes,
  defaultExpanded,
  onEdit,
  onDelete,
  onAddChild,
}: {
  nodes: Category[];
  defaultExpanded: boolean;
  onEdit: (c: Category) => void;
  onDelete: (id: string, name: string) => void;
  onAddChild: (parentId: string) => void;
}) {
  return (
    <ul className="category-tree list-none pl-0">
      {nodes.map((node) => (
        <CategoryTreeNode
          key={node.id}
          node={node}
          defaultExpanded={defaultExpanded}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddChild={onAddChild}
        />
      ))}
    </ul>
  );
}
