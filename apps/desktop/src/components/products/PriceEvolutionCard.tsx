import { useState } from "react";
import { AlertCircle, ChevronDown, ChevronUp, Loader2, TrendingUp } from "lucide-react";
import {
  buildMonthlyPriceSeries,
  formatPriceDisplay,
  formatPriceHistoryDisplayDate,
  getPriceHistorySourceLabel,
  type MonthlyPricePoint,
  type VariantPriceHistoryState,
} from "@/lib/priceHistory";
import {
  priceHistoryEmptyDescription,
  priceHistoryEmptyTitle,
  priceHistoryLoadError,
  priceHistorySingleTitle,
  priceHistoryTableToggle,
  variantPriceEmptyLabel,
} from "@/lib/variantPanelLabels";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTableScroll } from "@/components/ui/data-table";
import { cn } from "@/lib/utils";

type PriceEvolutionCardProps = {
  latestPrice: string | null;
  historyState: VariantPriceHistoryState;
  onRetry?: () => void;
};

function PriceHistoryChart({ series }: { series: MonthlyPricePoint[] }) {
  const maxPrice = Math.max(...series.map((point) => point.price), 0.01);

  return (
    <div className="price-chart" role="img" aria-label="Evolución mensual del precio">
      {series.map((point) => {
        const heightPct = Math.max(4, (point.price / maxPrice) * 100);
        return (
          <div key={point.monthKey} className="bar-wrap">
            <div
              className="bar"
              style={{ height: `${heightPct}%` }}
              title={`${point.label}: ${point.item.price_amount}`}
            />
            <span className="bar-label">{point.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function DeltaBadge({ delta }: { delta: string | null }) {
  if (delta == null || delta.trim() === "") return null;
  const numeric = Number.parseFloat(delta.replace(",", "."));
  const isUp = !Number.isNaN(numeric) && numeric > 0;
  const isDown = !Number.isNaN(numeric) && numeric < 0;

  return (
    <Badge
      variant="outline"
      className={cn(
        "tabular-nums font-medium shadow-none",
        isUp && "border-warning/50 text-warning",
        isDown && "border-success/50 text-success",
      )}
    >
      {delta}%
    </Badge>
  );
}

export function PriceEvolutionCard({
  latestPrice,
  historyState,
  onRetry,
}: PriceEvolutionCardProps) {
  const [tableOpen, setTableOpen] = useState(true);
  const { status, items, errorMessage } = historyState;
  const monthlySeries = status === "loaded" ? buildMonthlyPriceSeries(items) : [];
  const latestHistoryItem = items.length > 0 ? items[0] : null;
  const formattedLatestPrice = formatPriceDisplay(latestPrice);
  const singleItemSourceLabel =
    status === "loaded" && items.length === 1 ? getPriceHistorySourceLabel(items[0]) : null;

  return (
    <section className="price-evolution-card" aria-labelledby="variant-price-heading">
      <div className="mb-3 flex items-center gap-2">
        <TrendingUp className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        <h4
          id="variant-price-heading"
          className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
        >
          Precio y evolución
        </h4>
      </div>

      <div className="variant-price-history__current rounded-md border border-border bg-background/60 px-3 py-3">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Precio actual (PVP)
        </p>
        {formattedLatestPrice ? (
          <p className="mt-1">
            <Badge
              variant="secondary"
              className="whitespace-nowrap px-2.5 text-sm tabular-nums font-semibold shadow-none"
            >
              {formattedLatestPrice}
            </Badge>
          </p>
        ) : (
          <p className="mt-1 text-sm text-muted-foreground">{variantPriceEmptyLabel()}</p>
        )}
      </div>

      {status === "loading" ? (
        <div
          className="mt-3 flex items-center gap-2 rounded-md border border-border/60 bg-muted/10 px-3 py-3 text-sm text-muted-foreground"
          aria-busy="true"
        >
          <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
          Cargando histórico…
        </div>
      ) : null}

      {status === "error" ? (
        <div
          role="alert"
          className="mt-3 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-3"
        >
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" aria-hidden="true" />
            <div className="min-w-0 flex-1 space-y-2">
              <p className="text-sm text-destructive">{errorMessage ?? priceHistoryLoadError()}</p>
              {onRetry ? (
                <Button type="button" variant="outline" size="sm" className="h-8" onClick={onRetry}>
                  Reintentar
                </Button>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}

      {status === "loaded" && items.length === 0 ? (
        <div
          className="mt-3 rounded-md border border-dashed border-border bg-muted/10 px-3 py-4"
          role="status"
        >
          <p className="text-sm font-medium text-foreground">{priceHistoryEmptyTitle()}</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            {priceHistoryEmptyDescription()}
          </p>
        </div>
      ) : null}

      {status === "loaded" && items.length === 1 ? (
        <div className="mt-3 rounded-md border border-border bg-muted/10 px-3 py-3" role="status">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {priceHistorySingleTitle()}
          </p>
          <dl className="mt-2 space-y-1.5 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-muted-foreground">Fecha</dt>
              <dd className="tabular-nums font-medium">
                {formatPriceHistoryDisplayDate(items[0])}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-muted-foreground">Precio</dt>
              <dd className="tabular-nums font-medium">{items[0].price_amount}</dd>
            </div>
            {singleItemSourceLabel ? (
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Fuente</dt>
                <dd className="truncate text-right font-medium" title={singleItemSourceLabel}>
                  {singleItemSourceLabel}
                </dd>
              </div>
            ) : null}
          </dl>
        </div>
      ) : null}

      {status === "loaded" && items.length >= 2 ? (
        <div className="mt-3 space-y-3">
          <div className="rounded-md border border-border bg-muted/10 px-3 py-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Evolución mensual
            </p>
            <PriceHistoryChart series={monthlySeries} />
            {latestHistoryItem?.delta_pct_vs_previous ? (
              <p className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span>Último cambio registrado:</span>
                <DeltaBadge delta={latestHistoryItem.delta_pct_vs_previous} />
              </p>
            ) : null}
          </div>

          <div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 gap-1 px-2 text-xs text-muted-foreground"
              onClick={() => setTableOpen((open) => !open)}
              aria-expanded={tableOpen}
            >
              {tableOpen ? (
                <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              {priceHistoryTableToggle(tableOpen)}
            </Button>

            {tableOpen ? (
              <DataTableScroll maxHeight="max-h-[12rem]" minHeight="min-h-0" className="mt-2">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border bg-muted/20">
                      <th
                        scope="col"
                        className="px-2 py-1.5 text-left font-semibold uppercase tracking-wide text-muted-foreground"
                      >
                        Fecha
                      </th>
                      <th
                        scope="col"
                        className="px-2 py-1.5 text-left font-semibold uppercase tracking-wide text-muted-foreground"
                      >
                        Precio
                      </th>
                      <th
                        scope="col"
                        className="px-2 py-1.5 text-left font-semibold uppercase tracking-wide text-muted-foreground"
                      >
                        Fuente
                      </th>
                      <th
                        scope="col"
                        className="px-2 py-1.5 text-left font-semibold uppercase tracking-wide text-muted-foreground"
                      >
                        Cambio %
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item, index) => {
                      const source = getPriceHistorySourceLabel(item);
                      return (
                        <tr
                          key={`${item.list_id}-${item.imported_at}-${index}`}
                          className={index % 2 === 0 ? "bg-background" : "bg-muted/10"}
                        >
                          <td className="whitespace-nowrap px-2 py-1.5">
                            {formatPriceHistoryDisplayDate(item)}
                          </td>
                          <td className="whitespace-nowrap px-2 py-1.5 tabular-nums">
                            {item.price_amount}
                          </td>
                          <td
                            className="max-w-[8rem] truncate px-2 py-1.5"
                            title={source ?? undefined}
                          >
                            {source ?? "—"}
                          </td>
                          <td className="whitespace-nowrap px-2 py-1.5 tabular-nums">
                            {item.delta_pct_vs_previous != null
                              ? `${item.delta_pct_vs_previous}%`
                              : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </DataTableScroll>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
