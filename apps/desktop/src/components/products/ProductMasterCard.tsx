import { Link } from "react-router-dom";
import { ChevronRight, Eye, ImageIcon, MoreVertical } from "lucide-react";

import { API_BASE, type ProductMaster } from "@/lib/api";
import {
  hasMultipleVariants,
  parentPrice,
  parentReference,
  variantCount,
} from "@/components/products/productMasterCardMeta";
import { ProductSourcePageTrigger } from "@/components/products/ProductSourcePageTrigger";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  isMixedBrandMaster,
  masterBrandDisplay,
  masterBrandTitle,
} from "@/lib/variantRepresentation";
import { cn } from "@/lib/utils";

function CategoryStack({
  parent,
  sub,
}: {
  parent: string | null | undefined;
  sub: string | null | undefined;
}) {
  const parentLabel = parent?.trim() || null;
  const subLabel = sub?.trim() || null;

  if (!parentLabel && !subLabel) {
    return <span className="text-muted-foreground">—</span>;
  }

  if (parentLabel && subLabel && parentLabel.toLowerCase() !== subLabel.toLowerCase()) {
    return (
      <span className="product-master-card__category">
        <span className="product-master-card__category-parent">{parentLabel}</span>
        <span className="product-master-card__category-sub">{subLabel}</span>
      </span>
    );
  }

  return <span className="product-master-card__category-single">{subLabel || parentLabel}</span>;
}

export function ProductMasterCard({
  master,
  index,
  onOpenVariants,
}: {
  master: ProductMaster;
  index: number;
  onOpenVariants: (trigger: HTMLButtonElement) => void;
}) {
  const imageSrc = master.image_url ? `${API_BASE}${master.image_url}` : null;
  const priceLabel = parentPrice(master);
  const showVariantsToggle = hasMultipleVariants(master);
  const count = variantCount(master);
  const brandLabel = masterBrandDisplay(master);

  return (
    <article
      className={cn(
        "product-master-card",
        index % 2 === 0 ? "product-master-card--even" : "product-master-card--odd",
      )}
    >
      <div className="product-master-card__header">
        {imageSrc ? (
          <img
            src={imageSrc}
            alt=""
            className="product-master-card__image h-12 w-12 shrink-0 rounded border border-border bg-muted/30 object-contain"
          />
        ) : (
          <div
            className="product-master-card__image flex h-12 w-12 shrink-0 items-center justify-center rounded border border-dashed border-border bg-muted/20 text-muted-foreground"
            aria-hidden="true"
          >
            <ImageIcon className="h-5 w-5" />
          </div>
        )}
        <div className="product-master-card__title-block min-w-0 flex-1">
          <h3
            className="product-master-card__title line-clamp-2 text-sm font-medium"
            title={master.name}
          >
            {master.name}
          </h3>
          {priceLabel !== "—" ? (
            <Badge
              variant="success"
              className="mt-1 shrink-0 whitespace-nowrap border-success/50 bg-success/10 px-2.5 tabular-nums font-semibold shadow-none"
              title={priceLabel}
            >
              {priceLabel}
            </Badge>
          ) : null}
        </div>
      </div>

      <dl className="product-master-card__meta">
        <div className="product-master-card__meta-row">
          <dt>Referencia</dt>
          <dd
            className="font-mono text-xs font-bold text-primary"
            title={(master.references ?? []).join(", ") || undefined}
          >
            {parentReference(master)}
          </dd>
        </div>
        <div className="product-master-card__meta-row">
          <dt>Marca</dt>
          <dd>
            {brandLabel ? (
              <Badge
                variant={isMixedBrandMaster(master) ? "outline" : "secondary"}
                className="max-w-full truncate font-normal"
                title={masterBrandTitle(master)}
              >
                {brandLabel}
              </Badge>
            ) : (
              <span className="text-muted-foreground">—</span>
            )}
          </dd>
        </div>
        <div className="product-master-card__meta-row">
          <dt>Categoría</dt>
          <dd>
            <CategoryStack parent={master.category_parent_name} sub={master.category_sub_name} />
          </dd>
        </div>
      </dl>

      <div className="product-master-card__actions">
        {showVariantsToggle ? (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="product-master-card__variants-btn min-h-11 flex-1 gap-1.5"
            onClick={(event) => onOpenVariants(event.currentTarget)}
            aria-label={`Mostrar ${count} variantes de ${master.name}`}
          >
            <ChevronRight className="h-4 w-4 shrink-0" aria-hidden="true" />
            {count} variantes
          </Button>
        ) : null}

        <div className="product-master-card__icon-actions flex shrink-0 items-center gap-0.5">
          <ProductSourcePageTrigger
            source_page={master.source_page}
            source_pages={master.source_pages}
          />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="product-master-card__menu-btn h-11 w-11 shrink-0 text-muted-foreground hover:text-foreground"
                aria-label={`Más acciones para ${master.name}`}
              >
                <MoreVertical className="h-5 w-5" aria-hidden="true" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to={`/products/${master.id}`} className="cursor-pointer">
                  <Eye className="h-4 w-4" aria-hidden="true" />
                  Ver ficha
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </article>
  );
}
