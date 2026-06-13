import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import { cn } from "@/lib/utils";

import { TableHead } from "@/components/ui/table";

export type SortDirection = "asc" | "desc";

type SortableTableHeadProps<T extends string> = {
  label: string;
  column: T;
  activeColumn: T;
  direction: SortDirection;
  onSort: (column: T) => void;
  className?: string;
  align?: "left" | "center" | "right";
};

export function SortableTableHead<T extends string>({
  label,
  column,
  activeColumn,
  direction,
  onSort,
  className,
  align = "left",
}: SortableTableHeadProps<T>) {
  const active = activeColumn === column;
  const SortIcon = active ? (direction === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;

  return (
    <TableHead className={className}>
      <button
        type="button"
        onClick={() => onSort(column)}
        aria-sort={active ? (direction === "asc" ? "ascending" : "descending") : "none"}
        className={cn(
          "inline-flex w-full items-center gap-1.5 transition-colors",
          align === "right"
            ? "justify-end text-right"
            : align === "center"
              ? "justify-center text-center"
              : "justify-start text-left",
          "rounded-sm hover:text-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          active ? "text-foreground" : "text-muted-foreground",
        )}
      >
        <span>{label}</span>
        <SortIcon
          className={cn("h-3.5 w-3.5 shrink-0", active ? "text-primary" : "opacity-40")}
          aria-hidden="true"
        />
      </button>
    </TableHead>
  );
}
