import { useState } from "react";
import { ChevronRight, MoreVertical } from "lucide-react";
import type { Category } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

export function CategoryTreeNode({
  node,
  defaultExpanded,
  onEdit,
  onDelete,
  onAddChild,
}: {
  node: Category;
  defaultExpanded: boolean;
  onEdit: (c: Category) => void;
  onDelete: (id: string, name: string) => void;
  onAddChild: (parentId: string) => void;
}) {
  const hasChildren = (node.children?.length ?? 0) > 0;
  const [expanded, setExpanded] = useState(defaultExpanded || !hasChildren);

  return (
    <li className="category-tree-node">
      <div className="category-tree-node__row flex min-h-11 items-center gap-1">
        {hasChildren ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="category-tree-node__toggle min-h-11 min-w-11 shrink-0"
            aria-expanded={expanded}
            aria-label={expanded ? `Contraer ${node.name}` : `Expandir ${node.name}`}
            onClick={() => setExpanded((prev) => !prev)}
          >
            <ChevronRight
              className={cn("h-4 w-4 transition-transform", expanded && "rotate-90")}
              aria-hidden="true"
            />
          </Button>
        ) : (
          <span className="min-w-11 shrink-0" aria-hidden="true" />
        )}

        <span className="category-tree-node__label min-w-0 flex-1 truncate font-medium">
          {node.name}
        </span>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="category-tree-node__menu-btn min-h-11 min-w-11 shrink-0 text-muted-foreground"
              aria-label={`Acciones para ${node.name}`}
            >
              <MoreVertical className="h-5 w-5" aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit(node)}>Editar</DropdownMenuItem>
            <DropdownMenuItem onClick={() => onAddChild(node.id)}>+ Hijo</DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => onDelete(node.id, node.name)}
            >
              Eliminar
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {hasChildren && expanded ? (
        <ul className="category-tree-node__children list-none border-l border-border pl-0">
          {node.children.map((child) => (
            <CategoryTreeNode
              key={child.id}
              node={child}
              defaultExpanded={defaultExpanded}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddChild={onAddChild}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}
