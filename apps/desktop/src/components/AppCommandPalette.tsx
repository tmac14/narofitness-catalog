import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, Loader2, Package, Truck } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useCommandPalette } from "@/context/CommandPaletteContext";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useDelayedLoading } from "@/hooks/useDelayedLoading";
import { listCatalogs, listSuppliers, searchVariants } from "@/lib/api";
import {
  COMMAND_PALETTE_MAX_SEARCH_RESULTS_PER_KIND,
  COMMAND_PALETTE_MIN_QUERY_LENGTH,
  COMMAND_PALETTE_SEARCH_DEBOUNCE_MS,
  filterCatalogSearchResults,
  filterSupplierSearchResults,
  shouldOpenPaletteFromKeyboard,
  variantSearchLabel,
  type CommandPaletteItem,
} from "@/lib/commandPalette";
import { cn } from "@/lib/utils";

export function AppCommandPalette() {
  const navigate = useNavigate();
  const { open, setOpen } = useCommandPalette();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isFetching, setIsFetching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchItems, setSearchItems] = useState<CommandPaletteItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchRequestIdRef = useRef(0);
  const debouncedQuery = useDebouncedValue(query, COMMAND_PALETTE_SEARCH_DEBOUNCE_MS);
  const showSearchSpinner = useDelayedLoading(isFetching, { delayMs: 200, minShowMs: 300 });

  const closePalette = useCallback(() => {
    setOpen(false);
  }, [setOpen]);

  const runNavigate = useCallback(
    (to: string) => {
      closePalette();
      navigate(to);
    },
    [closePalette, navigate],
  );

  useEffect(() => {
    if (!open) return;
    const timer = window.setTimeout(() => {
      setQuery("");
      setActiveIndex(-1);
      setSearchItems([]);
      setSearchError(null);
      setIsFetching(false);
      searchRequestIdRef.current += 1;
      inputRef.current?.focus();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [open]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (shouldOpenPaletteFromKeyboard(event)) {
        event.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [setOpen]);

  useEffect(() => {
    const trimmed = debouncedQuery.trim();
    if (trimmed.length < COMMAND_PALETTE_MIN_QUERY_LENGTH) {
      setSearchItems([]);
      setSearchError(null);
      setIsFetching(false);
      return;
    }

    const requestId = ++searchRequestIdRef.current;
    setIsFetching(true);
    setSearchError(null);

    void (async () => {
      try {
        const [catalogsResponse, variantsResponse, suppliers] = await Promise.all([
          listCatalogs(),
          searchVariants({ q: trimmed }),
          listSuppliers(),
        ]);

        if (requestId !== searchRequestIdRef.current) return;

        const nextSearchItems: CommandPaletteItem[] = [];

        for (const catalog of filterCatalogSearchResults(catalogsResponse.items, trimmed)) {
          nextSearchItems.push({
            id: `search:catalog:${catalog.id}`,
            label: catalog.name,
            group: "search",
            icon: BookOpen,
            hint: "Catálogo",
            keywords: [catalog.name, "catalog", "catálogo"],
            onSelect: () => runNavigate(`/catalogs/${catalog.id}`),
          });
        }

        for (const variant of variantsResponse.items.slice(
          0,
          COMMAND_PALETTE_MAX_SEARCH_RESULTS_PER_KIND,
        )) {
          nextSearchItems.push({
            id: `search:variant:${variant.id}`,
            label: variantSearchLabel(variant),
            group: "search",
            icon: Package,
            hint: variant.sku,
            keywords: [variant.sku, variant.display_name ?? "", variant.master_name ?? ""],
            onSelect: () => runNavigate(`/products/${variant.product_master_id}`),
          });
        }

        for (const supplier of filterSupplierSearchResults(suppliers, trimmed)) {
          nextSearchItems.push({
            id: `search:supplier:${supplier.id}`,
            label: supplier.name,
            group: "search",
            icon: Truck,
            hint: supplier.code,
            keywords: [supplier.name, supplier.code, "proveedor"],
            onSelect: () => runNavigate("/suppliers"),
          });
        }

        setSearchItems(nextSearchItems);
        setSearchError(null);
      } catch {
        if (requestId !== searchRequestIdRef.current) return;
        setSearchItems([]);
        setSearchError("No se pudieron cargar los resultados de búsqueda");
      } finally {
        if (requestId === searchRequestIdRef.current) {
          setIsFetching(false);
        }
      }
    })();
  }, [debouncedQuery, runNavigate]);

  useEffect(() => {
    setActiveIndex(searchItems.length > 0 ? 0 : -1);
  }, [searchItems]);

  const executeItem = useCallback((item: CommandPaletteItem) => {
    item.onSelect();
  }, []);

  const onInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((prev) =>
        searchItems.length === 0 ? -1 : (prev + 1) % searchItems.length,
      );
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((prev) =>
        searchItems.length === 0 ? -1 : (prev - 1 + searchItems.length) % searchItems.length,
      );
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const item = searchItems[activeIndex];
      if (item) executeItem(item);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      closePalette();
    }
  };

  const trimmedDebouncedQuery = debouncedQuery.trim();
  const showSearchEmpty = useMemo(
    () =>
      trimmedDebouncedQuery.length >= COMMAND_PALETTE_MIN_QUERY_LENGTH &&
      !isFetching &&
      !searchError &&
      searchItems.length === 0,
    [trimmedDebouncedQuery, isFetching, searchError, searchItems.length],
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        className="app-command-palette max-w-xl gap-0 overflow-hidden p-0 sm:rounded-lg [&>button:last-child]:hidden"
        onOpenAutoFocus={(event) => {
          event.preventDefault();
          inputRef.current?.focus();
        }}
      >
        <DialogHeader className="sr-only">
          <DialogTitle>Búsqueda global</DialogTitle>
          <DialogDescription>Buscar catálogos, productos y proveedores.</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2 border-b border-border px-3 py-2">
          <Input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Buscar catálogos, productos, proveedores…"
            aria-label="Buscar en la aplicación"
            className="h-10 flex-1 border-0 bg-transparent px-1 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
            autoComplete="off"
            spellCheck={false}
          />
          {showSearchSpinner ? (
            <Loader2
              className="h-4 w-4 shrink-0 animate-spin text-muted-foreground"
              aria-hidden="true"
            />
          ) : null}
          <span className="sr-only" aria-live="polite">
            {showSearchSpinner ? "Buscando" : ""}
          </span>
        </div>

        <div
          className="app-command-palette__results max-h-[min(24rem,60vh)] overflow-y-auto p-2"
          role="listbox"
          aria-label="Resultados de búsqueda"
        >
          {searchItems.length > 0 ? (
            <ul className="flex flex-col gap-0.5">
              {searchItems.map((item, index) => {
                const Icon = item.icon;
                const isActive = index === activeIndex;

                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={isActive}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors",
                        isActive
                          ? "bg-accent text-accent-foreground"
                          : "text-foreground hover:bg-muted",
                      )}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => executeItem(item)}
                    >
                      {Icon ? (
                        <Icon className="h-4 w-4 shrink-0 opacity-80" aria-hidden="true" />
                      ) : (
                        <span className="h-4 w-4 shrink-0" aria-hidden="true" />
                      )}
                      <span className="min-w-0 flex-1 truncate">{item.label}</span>
                      {item.hint ? (
                        <span className="shrink-0 text-xs text-muted-foreground">{item.hint}</span>
                      ) : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : null}

          {searchError ? (
            <p className="px-2 py-3 text-sm text-destructive" role="alert">
              {searchError}
            </p>
          ) : null}

          {showSearchEmpty ? (
            <p className="px-2 py-3 text-sm text-muted-foreground">
              Sin coincidencias para «{trimmedDebouncedQuery}».
            </p>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
