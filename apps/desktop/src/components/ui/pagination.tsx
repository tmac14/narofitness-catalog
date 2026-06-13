import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { pageRangeLabel, totalPages } from "@/lib/pagination";
import { cn } from "@/lib/utils";

export type PaginationBarProps = {
  page: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  pageSizeOptions?: number[];
  className?: string;
  /** Always render bar even when single page (stable layout). Default true. */
  alwaysShow?: boolean;
};

export function PaginationBar({
  page,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [25, 50, 100],
  className,
  alwaysShow = true,
}: PaginationBarProps) {
  const pages = totalPages(totalItems, pageSize);
  const showPager = alwaysShow || pages > 1;

  if (!showPager && totalItems === 0) {
    return null;
  }

  if (!showPager) return null;

  return (
    <div
      className={cn(
        "flex h-11 min-h-[2.75rem] flex-wrap items-center justify-between gap-3 border-t border-border px-3",
        className,
      )}
      aria-label="Paginación"
    >
      <span className="text-sm text-muted-foreground tabular-nums">
        {pageRangeLabel(page, pageSize, totalItems)}
      </span>
      <div className="flex items-center gap-2">
        {onPageSizeChange && (
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <span className="hidden sm:inline">Filas</span>
            <Select
              className="h-8 w-[4.5rem] text-sm"
              value={String(pageSize)}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              aria-label="Filas por página"
            >
              {pageSizeOptions.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </Select>
          </div>
        )}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 w-8 p-0"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Página anterior"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="min-w-[4.5rem] text-center text-sm tabular-nums text-muted-foreground">
          {page} / {pages}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 w-8 p-0"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Página siguiente"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
