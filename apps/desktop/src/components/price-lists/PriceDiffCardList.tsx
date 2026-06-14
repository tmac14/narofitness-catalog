import { PriceDiffCard } from "@/components/price-lists/PriceDiffCard";
import type { PriceDiffRow } from "@/components/price-lists/priceDiffLabels";
import { ResponsiveDataCardList } from "@/components/responsive/list";

export function PriceDiffCardList({ items }: { items: PriceDiffRow[] }) {
  return (
    <ResponsiveDataCardList>
      {items.map((row, index) => (
        <li key={row.sku}>
          <PriceDiffCard row={row} index={index} />
        </li>
      ))}
    </ResponsiveDataCardList>
  );
}
