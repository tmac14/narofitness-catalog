import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCommandPalette } from "@/context/CommandPaletteContext";
import { formatPaletteShortcutHint } from "@/lib/commandPalette";
import { cn } from "@/lib/utils";

export function PaletteTrigger() {
  const { setOpen } = useCommandPalette();
  const shortcut = formatPaletteShortcutHint();

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={cn(
        "titlebar-no-drag app-topbar__palette-trigger h-9 shrink-0 gap-2 border-border/60 bg-secondary/40 px-3 text-muted-foreground hover:text-foreground lg:h-8",
      )}
      onClick={() => setOpen(true)}
      aria-label={`Abrir búsqueda (${shortcut})`}
    >
      <span className="flex min-w-0 items-center gap-1.5">
        <Search className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        <span className="hidden text-xs font-medium sm:inline">Buscar</span>
      </span>
      <kbd className="ml-auto hidden shrink-0 rounded border border-border/80 bg-background/60 px-1.5 py-0.5 font-mono text-[0.65rem] leading-none text-muted-foreground md:inline">
        {shortcut}
      </kbd>
    </Button>
  );
}
