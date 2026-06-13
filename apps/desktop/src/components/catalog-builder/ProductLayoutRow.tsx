import { memo } from "react";
import { Badge } from "@/components/ui/badge";
import { TableCell } from "@/components/ui/table";
import {
  layoutById,
  layoutIdDisplayLabel,
  type LayoutProductRow,
  type ProductLayoutDefinition,
} from "@/lib/catalogLayout";
import { cn } from "@/lib/utils";

type RowProps = {
  product: LayoutProductRow;
  layouts: ProductLayoutDefinition[];
  manualOverrideId: string | undefined;
  highlighted?: boolean;
};

export const ProductLayoutRow = memo(function ProductLayoutRow({
  product,
  layouts,
  manualOverrideId,
  highlighted = false,
}: RowProps) {
  const layoutName =
    layoutById(layouts, product.layout_id)?.name ?? layoutIdDisplayLabel(product.layout_id);

  return (
    <>
      <TableCell
        className={cn("max-w-[220px] truncate font-medium", highlighted && "bg-primary/5")}
        title={product.master_name}
      >
        {product.master_name}
      </TableCell>
      <TableCell className="w-[120px] truncate text-muted-foreground" title={product.section_name}>
        {product.section_name}
      </TableCell>
      <TableCell className="w-[80px] whitespace-nowrap tabular-nums">
        {product.has_variants ? `${product.variant_attribute_count} attr.` : "Único"}
      </TableCell>
      <TableCell className="w-[140px] truncate whitespace-nowrap" title={layoutName}>
        {layoutName}
      </TableCell>
      <TableCell className="w-[160px]">
        <div className="flex flex-nowrap gap-1 overflow-hidden">
          {product.layout_selection?.fallback_used ? (
            <Badge variant="warning">Fallback</Badge>
          ) : manualOverrideId ? (
            <Badge variant="default">Manual</Badge>
          ) : (
            <Badge variant="secondary">Auto</Badge>
          )}
          {!product.image_url && <Badge variant="outline">Sin imagen</Badge>}
        </div>
      </TableCell>
    </>
  );
});
