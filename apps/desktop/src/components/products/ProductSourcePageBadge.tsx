import { getProductSourcePageLabel } from "@/lib/productSourcePage";
import { Badge } from "@/components/ui/badge";

type ProductSourcePageBadgeProps = {
  source_page?: number | null;
  source_pages?: readonly (number | null | undefined)[] | null;
};

export function ProductSourcePageBadge({ source_page, source_pages }: ProductSourcePageBadgeProps) {
  const label = getProductSourcePageLabel({ source_page, source_pages });
  if (!label) return null;

  return (
    <Badge
      variant="outline"
      className="whitespace-nowrap px-2 py-0 text-[0.65rem] font-normal tabular-nums shadow-none"
      title={label}
    >
      {label}
    </Badge>
  );
}
