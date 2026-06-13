import { useRef, type RefObject } from "react";
import { Link } from "react-router-dom";
import { Eye, X } from "lucide-react";

import { API_BASE, type ProductMaster } from "@/lib/api";
import { listVariantsInApiOrder } from "@/lib/productSpecs";
import {
  getListVariantAttributeValue,
  layoutListVariantColumns,
} from "@/lib/variantRepresentation";
import { ProductSourcePageTrigger } from "@/components/products/ProductSourcePageTrigger";
import { restoreVariantSheetFocus } from "@/components/products/productVariantExpandSheetFocus";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

function VariantImageThumb({ imageUrl }: { imageUrl: string | null | undefined }) {
  if (imageUrl) {
    return (
      <img
        src={`${API_BASE}${imageUrl}`}
        alt=""
        className="product-variant-card__image h-12 w-12 shrink-0 rounded border border-border bg-muted/30 object-contain"
      />
    );
  }

  return (
    <div
      className="product-variant-card__image h-12 w-12 shrink-0 rounded border border-dashed border-border/60 bg-muted/15"
      aria-hidden="true"
    />
  );
}

function ProductVariantCard({
  master,
  variant,
  index,
}: {
  master: ProductMaster;
  variant: ProductMaster["variants"][number];
  index: number;
}) {
  const { leadingColumns, identityColumns, specColumns } = layoutListVariantColumns(master);
  const attributeColumns = [...leadingColumns, ...identityColumns, ...specColumns];

  return (
    <article
      className={cn(
        "product-variant-card",
        index % 2 === 0 ? "product-variant-card--even" : "product-variant-card--odd",
      )}
    >
      <div className="product-variant-card__header">
        <VariantImageThumb imageUrl={variant.image_url} />
        <div className="product-variant-card__price">
          {variant.price ? (
            <Badge
              variant="secondary"
              className="whitespace-nowrap px-2.5 font-semibold tabular-nums shadow-none"
              title={variant.price}
            >
              {variant.price}
            </Badge>
          ) : (
            <span className="text-sm text-muted-foreground">—</span>
          )}
        </div>
      </div>

      <dl className="product-variant-card__attrs">
        {attributeColumns.map((column) => {
          const value = getListVariantAttributeValue(variant, column.key);
          return (
            <div key={column.key} className="product-variant-card__attr">
              <dt>{column.label}</dt>
              <dd title={value === "—" ? undefined : value}>{value}</dd>
            </div>
          );
        })}
        <div className="product-variant-card__attr">
          <dt>Referencia</dt>
          <dd className="font-mono text-xs font-bold text-primary">{variant.sku}</dd>
        </div>
      </dl>

      <div className="product-variant-card__actions">
        <ProductSourcePageTrigger
          source_page={variant.source_page}
          source_pages={variant.source_pages}
        />
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="product-variant-card__detail-btn min-h-11 flex-1"
          asChild
        >
          <Link to={`/products/${master.id}`}>
            <Eye className="h-4 w-4" aria-hidden="true" />
            Ver ficha
          </Link>
        </Button>
      </div>
    </article>
  );
}

export function ProductVariantExpandSheetBody({ master }: { master: ProductMaster }) {
  const variants = listVariantsInApiOrder(master.variants);

  if (variants.length === 0) {
    return <p className="px-6 text-sm text-muted-foreground">Este producto no tiene variantes.</p>;
  }

  return (
    <ul className="product-variant-expand-sheet__list flex flex-col gap-3 px-6 pb-6">
      {variants.map((variant, index) => (
        <li key={variant.id}>
          <ProductVariantCard master={master} variant={variant} index={index} />
        </li>
      ))}
    </ul>
  );
}

export function ProductVariantExpandSheet({
  master,
  open,
  onOpenChange,
  restoreFocusTo,
}: {
  master: ProductMaster | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  restoreFocusTo?: RefObject<HTMLButtonElement | null>;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);

  if (!master) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        showClose={false}
        className="product-variant-expand-sheet max-h-[min(85vh,40rem)] overflow-y-auto"
        onOpenAutoFocus={(event) => {
          event.preventDefault();
          closeRef.current?.focus();
        }}
        onCloseAutoFocus={(event) => {
          restoreVariantSheetFocus(event, restoreFocusTo?.current);
        }}
      >
        <SheetClose asChild>
          <Button
            ref={closeRef}
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4 h-11 w-11 shrink-0 text-muted-foreground hover:text-foreground"
            aria-label="Cerrar variantes"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </Button>
        </SheetClose>

        <SheetHeader className="pr-14 text-left">
          <SheetTitle className="line-clamp-2">{master.name}</SheetTitle>
          <SheetDescription>
            {listVariantsInApiOrder(master.variants).length} variantes — toque una fila o use Ver
            ficha para abrir el detalle.
          </SheetDescription>
        </SheetHeader>

        <ProductVariantExpandSheetBody master={master} />
      </SheetContent>
    </Sheet>
  );
}
