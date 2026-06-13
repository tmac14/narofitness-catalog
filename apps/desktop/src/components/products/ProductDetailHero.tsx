import { Link } from "react-router-dom";
import { ArrowLeft, Package } from "lucide-react";
import type { ProductMasterDetail } from "@/lib/api";
import {
  categoryBreadcrumb,
  masterThumbnailUrl,
  productDetailBadges,
  variantCountLabel,
} from "@/lib/productDetailMeta";
import {
  isMixedBrandMaster,
  masterBrandDisplay,
  masterBrandTitle,
} from "@/lib/variantRepresentation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ProductDetailHeroProps = {
  master: ProductMasterDetail;
  apiBase: string;
  formId: string;
  saving?: boolean;
};

export function ProductDetailHero({ master, apiBase, formId, saving }: ProductDetailHeroProps) {
  const thumbnail = masterThumbnailUrl(master, apiBase);
  const category = categoryBreadcrumb(master);
  const badges = productDetailBadges(master);
  const brandLabel = masterBrandDisplay(master);

  return (
    <header className="product-detail-hero mb-6 rounded-lg border border-border bg-card p-4 shadow-sm sm:p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 flex-1 gap-4">
          <div
            className={cn(
              "product-detail-hero__avatar flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-border sm:h-20 sm:w-20",
              thumbnail ? "bg-muted/30" : "bg-muted/20",
            )}
          >
            {thumbnail ? (
              <img src={thumbnail} alt="" className="h-full w-full object-contain" />
            ) : (
              <Package className="h-8 w-8 text-muted-foreground opacity-70" aria-hidden="true" />
            )}
          </div>

          <div className="min-w-0 flex-1 space-y-2">
            <h1
              className="truncate text-xl font-semibold tracking-tight text-foreground sm:text-2xl"
              title={master.name}
            >
              {master.name}
            </h1>

            <div className="flex flex-wrap items-center gap-2">
              {brandLabel ? (
                <Badge
                  variant={isMixedBrandMaster(master) ? "outline" : "secondary"}
                  className="font-normal"
                  title={masterBrandTitle(master)}
                >
                  {brandLabel}
                </Badge>
              ) : null}
              {category ? (
                <Badge
                  variant="outline"
                  className="max-w-full truncate font-normal"
                  title={category}
                >
                  {category}
                </Badge>
              ) : null}
              <Badge variant="outline" className="font-normal">
                {variantCountLabel(master.variants.length)}
              </Badge>
              {badges.map((badge) => (
                <Badge key={badge.id} variant={badge.variant} className="font-normal">
                  {badge.label}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2 lg:justify-end">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/products">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Volver
            </Link>
          </Button>
          <Button type="submit" form={formId} disabled={saving}>
            {saving ? "Guardando…" : "Guardar cambios"}
          </Button>
        </div>
      </div>
    </header>
  );
}
