import type { CanonicalCategoryNode } from "@/lib/api";
import { cn } from "@/lib/utils";

type Props = {
  nodes: CanonicalCategoryNode[];
  selectedId: string | null;
  onSelect: (node: CanonicalCategoryNode) => void;
};

function TreeNode({
  node,
  selectedId,
  onSelect,
}: {
  node: CanonicalCategoryNode;
  selectedId: string | null;
  onSelect: (node: CanonicalCategoryNode) => void;
}) {
  const selected = selectedId === node.id;
  return (
    <li className="ml-3 mb-1">
      <button
        type="button"
        aria-pressed={selected}
        className={cn(
          "w-full text-left rounded px-2 py-1 text-sm hover:bg-muted",
          selected && "bg-primary/10 font-medium",
        )}
        onClick={() => onSelect(node)}
      >
        {node.full_path}
      </button>
      {node.children.length > 0 && (
        <ul className="list-none pl-0 mt-1 border-l border-border ml-2">
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} selectedId={selectedId} onSelect={onSelect} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function CanonicalCategoryTree({ nodes, selectedId, onSelect }: Props) {
  if (nodes.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No hay categorías creadas. Créelas en la sección Categorías.
      </p>
    );
  }
  return (
    <ul className="list-none pl-0 max-h-[50vh] overflow-auto" aria-label="Árbol de categorías">
      {nodes.map((node) => (
        <TreeNode key={node.id} node={node} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </ul>
  );
}
