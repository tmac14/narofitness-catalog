import { Minus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const isElectron = typeof window !== "undefined" && window.narocatalog?.isElectron;

export function TitleBar() {
  if (!isElectron) return null;

  return (
    <header
      className={cn(
        "titlebar-drag flex h-12 min-h-11 shrink-0 items-center justify-between border-b border-border bg-card px-3 select-none lg:px-4",
      )}
    >
      <div className="flex min-w-0 items-center gap-2 lg:gap-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground lg:h-7 lg:w-7">
          N
        </div>
        <span className="truncate text-sm font-semibold text-foreground">NaroCatalog</span>
        <span className="hidden text-xs text-muted-foreground lg:inline">
          Generador de catálogos FDL
        </span>
      </div>
      <div className="titlebar-no-drag flex shrink-0 items-center gap-1">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-11 w-11 text-muted-foreground hover:text-foreground lg:h-8 lg:w-8"
          onClick={() => window.narocatalog?.windowControls.minimize()}
          aria-label="Minimizar"
        >
          <Minus className="h-4 w-4" aria-hidden="true" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-11 w-11 text-muted-foreground hover:text-destructive lg:h-8 lg:w-8"
          onClick={() => window.narocatalog?.windowControls.close()}
          aria-label="Cerrar"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </header>
  );
}
