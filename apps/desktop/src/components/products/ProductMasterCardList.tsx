import { useRef } from "react";
import type { MasterSortKey, ProductMaster, SortDirection } from "@/lib/api";
import { ProductMasterCard } from "@/components/products/ProductMasterCard";
import { hasMultipleVariants } from "@/components/products/productMasterCardMeta";
import { ProductVariantExpandSheet } from "@/components/products/ProductVariantExpandSheet";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ArrowDown, ArrowUp } from "lucide-react";

const SORT_OPTIONS: { value: MasterSortKey; label: string }[] = [
  { value: "name", label: "Producto" },
  { value: "reference", label: "Referencia" },
  { value: "brand", label: "Marca" },
  { value: "category", label: "Categoría" },
  { value: "price", label: "PVP" },
];

function ProductMasterCardListSortBar({
  sortBy,
  sortDir,
  onSort,
}: {
  sortBy: MasterSortKey;
  sortDir: SortDirection;
  onSort: (column: MasterSortKey) => void;
}) {
  const toggleDirectionLabel =
    sortDir === "asc" ? "Cambiar a orden descendente" : "Cambiar a orden ascendente";

  return (
    <div className="product-master-card-list__sort flex flex-wrap items-center gap-2 border-b border-border px-4 py-3">
      <Label htmlFor="products-card-sort" className="sr-only">
        Ordenar productos
      </Label>
      <span className="text-xs font-medium text-muted-foreground" aria-hidden="true">
        Ordenar por
      </span>
      <select
        id="products-card-sort"
        value={sortBy}
        onChange={(event) => onSort(event.target.value as MasterSortKey)}
        className="product-master-card-list__sort-select min-h-11 flex-1 rounded-md border border-input bg-background px-3 text-sm"
        aria-label="Campo de ordenación"
      >
        {SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <Button
        type="button"
        variant="secondary"
        size="icon"
        className="product-master-card-list__sort-dir min-h-11 min-w-11 shrink-0"
        aria-label={toggleDirectionLabel}
        onClick={() => onSort(sortBy)}
      >
        {sortDir === "asc" ? (
          <ArrowUp className="h-4 w-4" aria-hidden="true" />
        ) : (
          <ArrowDown className="h-4 w-4" aria-hidden="true" />
        )}
      </Button>
    </div>
  );
}

export function ProductMasterCardList({
  items,
  sortBy,
  sortDir,
  onSort,
  variantSheetMasterId,
  onOpenVariants,
  onVariantSheetOpenChange,
}: {
  items: ProductMaster[];
  sortBy: MasterSortKey;
  sortDir: SortDirection;
  onSort: (column: MasterSortKey) => void;
  variantSheetMasterId: string | null;
  onOpenVariants: (master: ProductMaster) => void;
  onVariantSheetOpenChange: (open: boolean) => void;
}) {
  const variantSheetTriggerRef = useRef<HTMLButtonElement | null>(null);

  const sheetMaster =
    variantSheetMasterId != null
      ? (items.find((item) => item.id === variantSheetMasterId) ?? null)
      : null;

  return (
    <div className="product-master-card-list">
      <ProductMasterCardListSortBar sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
      <ul className="product-master-card-list__items flex flex-col gap-0">
        {items.map((master, index) => (
          <li key={master.id}>
            <ProductMasterCard
              master={master}
              index={index}
              onOpenVariants={(trigger) => {
                if (!hasMultipleVariants(master)) return;
                variantSheetTriggerRef.current = trigger;
                onOpenVariants(master);
              }}
            />
          </li>
        ))}
      </ul>
      <ProductVariantExpandSheet
        master={sheetMaster}
        open={sheetMaster != null}
        onOpenChange={onVariantSheetOpenChange}
        restoreFocusTo={variantSheetTriggerRef}
      />
    </div>
  );
}
