import { Link } from "react-router-dom";
import { ChevronRight, Eye, ImageIcon } from "lucide-react";

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
  ResponsiveCardHeader,
  ResponsiveDataCard,
  ResponsiveMetaGrid,
  ResponsiveMetaRow,
  ResponsiveTouchMenuTrigger,
} from "@/components/responsive/list";
import {
  isMixedBrandMaster,
  masterBrandDisplay,
  masterBrandTitle,
} from "@/lib/variantRepresentation";

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
    <ResponsiveDataCard index={index}>
      <ResponsiveCardHeader>
        {imageSrc ? (
          <img
            src={imageSrc}
            alt=""
            className="h-12 w-12 shrink-0 rounded border border-border bg-muted/30 object-contain"
          />
        ) : (
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded border border-dashed border-border bg-muted/20 text-muted-foreground"
            aria-hidden="true"
          >
            <ImageIcon className="h-5 w-5" />
          </div>
        )}
        <div className="product-master-card__title-block">
          <h3 className="line-clamp-2 text-sm font-medium" title={master.name}>
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
      </ResponsiveCardHeader>

      <ResponsiveMetaGrid>
        <ResponsiveMetaRow label="Referencia">
          <span
            className="font-mono text-xs font-bold text-primary"
            title={(master.references ?? []).join(", ") || undefined}
          >
            {parentReference(master)}
          </span>
        </ResponsiveMetaRow>
        <ResponsiveMetaRow label="Marca">
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
        </ResponsiveMetaRow>
        <ResponsiveMetaRow label="Categoría">
          <CategoryStack parent={master.category_parent_name} sub={master.category_sub_name} />
        </ResponsiveMetaRow>
      </ResponsiveMetaGrid>

      <div className="responsive-data-card__actions">
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

        <div className="responsive-data-card__icon-actions flex shrink-0 items-center gap-0.5">
          <ProductSourcePageTrigger
            source_page={master.source_page}
            source_pages={master.source_pages}
          />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <ResponsiveTouchMenuTrigger ariaLabel={`Más acciones para ${master.name}`} />
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
    </ResponsiveDataCard>
  );
}
