import { Badge } from "@/components/ui/badge";
import {
  changeTypeLabel,
  priceDiffCardModifier,
  type PriceDiffRow,
} from "@/components/price-lists/priceDiffLabels";
import {
  ResponsiveCardFooter,
  ResponsiveCardHeader,
  ResponsiveDataCard,
  ResponsiveMetaGrid,
  ResponsiveMetaRow,
} from "@/components/responsive/list";

function changeBadgeVariant(
  changeType: string,
): "warning" | "secondary" | "info" | "outline" {
  if (changeType === "changed") return "warning";
  if (changeType === "only_a" || changeType === "only_b") return "info";
  return "secondary";
}

export function PriceDiffCard({ row, index }: { row: PriceDiffRow; index: number }) {
  return (
    <ResponsiveDataCard index={index} modifierClass={priceDiffCardModifier(row.change_type)}>
      <ResponsiveCardHeader className="responsive-data-card__header--stacked">
        <h3 className="line-clamp-2 text-sm font-medium" title={row.name}>
          {row.name}
        </h3>
        <p className="font-mono text-xs text-muted-foreground">{row.sku}</p>
      </ResponsiveCardHeader>

      <ResponsiveMetaGrid>
        <ResponsiveMetaRow label="Precio A">
          <span className="tabular-nums">{row.price_a ?? "—"}</span>
        </ResponsiveMetaRow>
        <ResponsiveMetaRow label="Precio B">
          <span className="tabular-nums">{row.price_b ?? "—"}</span>
        </ResponsiveMetaRow>
        <ResponsiveMetaRow label="Diferencia">
          <span className="tabular-nums">{row.delta_abs ?? "—"}</span>
        </ResponsiveMetaRow>
        <ResponsiveMetaRow label="Diferencia %">
          <span className="tabular-nums">
            {row.delta_pct != null ? `${row.delta_pct}%` : "—"}
          </span>
        </ResponsiveMetaRow>
      </ResponsiveMetaGrid>

      <ResponsiveCardFooter>
        <Badge variant={changeBadgeVariant(row.change_type)}>
          {changeTypeLabel(row.change_type)}
        </Badge>
      </ResponsiveCardFooter>
    </ResponsiveDataCard>
  );
}
