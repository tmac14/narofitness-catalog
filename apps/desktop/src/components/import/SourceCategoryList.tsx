import { Badge } from "@/components/ui/badge";
import {
  formatCategoryPath,
  labelMappingStatus,
  labelProposalSource,
} from "@/lib/importMappingLabels";
import type { SourceCategoryDiscovery } from "@/lib/api";
import { cn } from "@/lib/utils";

type Props = {
  items: SourceCategoryDiscovery[];
  selectedPath: string | null;
  onSelect: (item: SourceCategoryDiscovery) => void;
};

export function SourceCategoryList({ items, selectedPath, onSelect }: Props) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No se detectaron categorías en el PDF.</p>;
  }

  return (
    <div
      className="space-y-2 max-h-[55vh] overflow-auto"
      role="list"
      aria-label="Categorías del PDF"
    >
      {items.map((item) => {
        const selected = selectedPath === item.source_category_path_raw;
        return (
          <button
            key={item.normalized_source_category_key}
            type="button"
            role="listitem"
            aria-pressed={selected}
            className={cn(
              "w-full text-left rounded border p-3 hover:bg-muted/50 transition-colors",
              selected && "border-primary bg-primary/5",
            )}
            onClick={() => onSelect(item)}
          >
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="font-medium text-sm">{item.source_category_path_raw}</span>
              <Badge variant="secondary">{item.row_count} filas</Badge>
              <Badge variant={item.mapping_status === "mapped" ? "default" : "outline"}>
                {labelMappingStatus(item.mapping_status)}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground truncate">
              {(item.example_rows || [])
                .map((r) => r.normalized_name || r.sku || "")
                .filter(Boolean)
                .join(" · ")}
            </p>
            {item.currently_mapped_category_slug && (
              <p className="text-xs mt-1">
                Asignada a: {formatCategoryPath(item.currently_mapped_category_slug)}
              </p>
            )}
            {item.proposed_category_slug && item.mapping_status !== "mapped" && (
              <p className="text-xs mt-1 text-muted-foreground">
                Categoría propuesta: {formatCategoryPath(item.proposed_category_slug)}
                {item.proposal_source ? ` · ${labelProposalSource(item.proposal_source)}` : ""}
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}
