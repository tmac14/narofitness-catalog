import { FileText } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { getProductSourcePagePopoverBody } from "@/lib/productSourcePage";
import { cn } from "@/lib/utils";

type ProductSourcePageTriggerProps = {
  source_page?: number | null;
  source_pages?: readonly (number | null | undefined)[] | null;
  openOnHover?: boolean;
};

export function ProductSourcePagePopoverPanel({
  body,
  panelId,
  titleId,
}: {
  body: string;
  panelId: string;
  titleId: string;
}) {
  return (
    <div
      id={panelId}
      role="dialog"
      aria-labelledby={titleId}
      className="absolute right-0 top-full z-50 mt-1 w-max max-w-[14rem] rounded-md border border-border bg-card p-3 text-sm shadow-md"
    >
      <p
        id={titleId}
        className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
      >
        Origen PDF
      </p>
      <p className="mt-1 text-foreground">{body}</p>
    </div>
  );
}

export function ProductSourcePageTrigger({
  source_page,
  source_pages,
  openOnHover = false,
}: ProductSourcePageTriggerProps) {
  const body = getProductSourcePagePopoverBody({ source_page, source_pages });
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const titleId = useId();
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    const onPointerDown = (event: PointerEvent) => {
      if (
        rootRef.current &&
        event.target instanceof Node &&
        !rootRef.current.contains(event.target)
      ) {
        setOpen(false);
      }
    };

    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [open]);

  if (!body) return null;

  return (
    <div
      ref={rootRef}
      className="relative"
      onMouseEnter={openOnHover ? () => setOpen(true) : undefined}
      onMouseLeave={openOnHover ? () => setOpen(false) : undefined}
    >
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className={cn(
          "h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground",
          open && "text-foreground",
        )}
        aria-label="Ver origen PDF"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((prev) => !prev)}
        onFocus={openOnHover ? () => setOpen(true) : undefined}
        onBlur={
          openOnHover
            ? (event) => {
                if (
                  !(event.relatedTarget instanceof Node) ||
                  !rootRef.current?.contains(event.relatedTarget)
                ) {
                  setOpen(false);
                }
              }
            : undefined
        }
      >
        <FileText className="h-4 w-4" aria-hidden="true" />
      </Button>
      {open ? (
        <ProductSourcePagePopoverPanel body={body} panelId={panelId} titleId={titleId} />
      ) : null}
    </div>
  );
}
