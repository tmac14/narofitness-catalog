import type { SpecValue } from "@/lib/api";
import { formatSpecLabel, formatSpecValue } from "@/lib/productSpecs";
import { cn } from "@/lib/utils";

type ProductSpecChipProps = {
  spec: Pick<SpecValue, "key" | "label" | "value">;
  className?: string;
  size?: "default" | "compact";
};

export function ProductSpecChip({ spec, className, size = "default" }: ProductSpecChipProps) {
  const compact = size === "compact";

  return (
    <div
      className={cn(
        "product-spec-chip rounded-lg border border-border bg-muted/20",
        compact ? "px-2 py-1.5" : "px-3 py-2.5",
        className,
      )}
    >
      <p
        className={cn(
          "font-medium uppercase tracking-wide text-muted-foreground",
          compact ? "text-[0.6rem]" : "text-[0.65rem]",
        )}
      >
        {formatSpecLabel(spec)}
      </p>
      <p className={cn("mt-0.5 font-semibold text-foreground", compact ? "text-xs" : "text-sm")}>
        {formatSpecValue(spec)}
      </p>
    </div>
  );
}
