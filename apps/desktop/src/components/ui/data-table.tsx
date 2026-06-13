import * as React from "react";
import { cn } from "@/lib/utils";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export type DataTableProps = {
  children: React.ReactNode;
  className?: string;
  /** Min height for empty/loading parity */
  minHeight?: string;
  maxHeight?: string;
  stickyHeader?: boolean;
};

export function DataTableScroll({
  children,
  className,
  minHeight = "min-h-[var(--table-min-height,480px)]",
  maxHeight,
  stickyHeader = true,
}: DataTableProps) {
  return (
    <div
      className={cn(
        "relative w-full overflow-auto",
        minHeight,
        maxHeight,
        stickyHeader && "[&_thead]:sticky [&_thead]:top-0 [&_thead]:z-10 [&_thead]:bg-card",
        className,
      )}
    >
      {children}
    </div>
  );
}

type DataTableRootProps = React.HTMLAttributes<HTMLTableElement> & {
  layout?: "auto" | "fixed";
  containerClassName?: string;
  scroll?: boolean;
  minHeight?: string;
  maxHeight?: string;
  stickyHeader?: boolean;
};

export function DataTable({
  className,
  layout = "fixed",
  containerClassName,
  scroll = true,
  minHeight,
  maxHeight,
  stickyHeader,
  children,
  ...props
}: DataTableRootProps) {
  const table = (
    <table
      ref={undefined}
      className={cn(
        "w-full caption-bottom text-sm",
        layout === "fixed" && "table-fixed",
        className,
      )}
      {...props}
    >
      {children}
    </table>
  );

  if (!scroll) return table;

  return (
    <DataTableScroll
      className={containerClassName}
      minHeight={minHeight}
      maxHeight={maxHeight}
      stickyHeader={stickyHeader}
    >
      {table}
    </DataTableScroll>
  );
}

export function DataTableEmptyRow({ colSpan, message }: { colSpan: number; message: string }) {
  return (
    <TableRow>
      <TableCell colSpan={colSpan} className="h-32 text-center text-muted-foreground">
        {message}
      </TableCell>
    </TableRow>
  );
}

export { TableHeader, TableBody, TableHead, TableRow, TableCell };
