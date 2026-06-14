import { describe, expect, it, vi } from "vitest";
import {
  buildPaletteActionCommands,
  COMMAND_PALETTE_MAX_SEARCH_RESULTS_PER_KIND,
  filterCatalogSearchResults,
  filterCommandPaletteItems,
  filterSupplierSearchResults,
  isEditableKeyboardTarget,
  shouldOpenPaletteFromKeyboard,
  variantSearchLabel,
} from "./commandPalette";
import type { CatalogListItem, ProductVariant, Supplier } from "@/lib/api";

function makeKeyboardEvent(init: {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  defaultPrevented?: boolean;
  target?: EventTarget | null;
}): KeyboardEvent {
  return init as unknown as KeyboardEvent;
}

describe("commandPalette", () => {
  describe("shouldOpenPaletteFromKeyboard", () => {
    it("opens on Ctrl+K and Meta+K outside editable targets", () => {
      expect(
        shouldOpenPaletteFromKeyboard(
          makeKeyboardEvent({ key: "k", ctrlKey: true }),
        ),
      ).toBe(true);
      expect(
        shouldOpenPaletteFromKeyboard(
          makeKeyboardEvent({ key: "k", metaKey: true }),
        ),
      ).toBe(true);
    });

    it("ignores modified shortcuts and plain K", () => {
      expect(
        shouldOpenPaletteFromKeyboard(
          makeKeyboardEvent({ key: "k", altKey: true, ctrlKey: true }),
        ),
      ).toBe(false);
      expect(shouldOpenPaletteFromKeyboard(makeKeyboardEvent({ key: "k" }))).toBe(false);
    });

    it("suppresses when focus is in an input", () => {
      const input = {
        tagName: "INPUT",
        isContentEditable: false,
        closest: () => null,
      } as unknown as EventTarget;

      expect(
        shouldOpenPaletteFromKeyboard(
          makeKeyboardEvent({ key: "k", ctrlKey: true, target: input }),
        ),
      ).toBe(false);
      expect(isEditableKeyboardTarget(input)).toBe(true);
    });

    it("suppresses when focus is in contenteditable", () => {
      const editable = {
        tagName: "DIV",
        isContentEditable: true,
        closest: () => null,
      } as unknown as EventTarget;

      expect(
        shouldOpenPaletteFromKeyboard(
          makeKeyboardEvent({ key: "k", ctrlKey: true, target: editable }),
        ),
      ).toBe(false);
    });
  });

  describe("filterCommandPaletteItems", () => {
    it("filters by label and keywords", () => {
      const items = buildPaletteActionCommands({
        onOpenSettings: vi.fn(),
        onOpenJobsPanel: vi.fn(),
      });

      const filtered = filterCommandPaletteItems(items, "tareas");
      expect(filtered).toHaveLength(1);
      expect(filtered[0]?.label).toBe("Abrir panel de tareas");
    });
  });

  describe("entity search helpers", () => {
    const catalogs: CatalogListItem[] = [
      { id: "1", name: "Verano 2026", default_markup_percent: "10" },
      { id: "2", name: "Invierno", default_markup_percent: "12" },
    ];

    const suppliers: Supplier[] = [
      {
        id: "s1",
        code: "FDL",
        name: "Fitness Delivery",
        notes: null,
        is_active: true,
      },
      {
        id: "s2",
        code: "ACME",
        name: "Acme Supply",
        notes: null,
        is_active: true,
      },
    ];

    it("filters catalogs and suppliers with caps", () => {
      expect(filterCatalogSearchResults(catalogs, "ver")).toEqual([catalogs[0]]);
      expect(filterSupplierSearchResults(suppliers, "fdl")).toEqual([suppliers[0]]);

      const manyCatalogs = Array.from({ length: 8 }, (_, index) => ({
        id: String(index),
        name: `Catálogo ${index}`,
        default_markup_percent: "10",
      }));
      expect(filterCatalogSearchResults(manyCatalogs, "catálogo")).toHaveLength(
        COMMAND_PALETTE_MAX_SEARCH_RESULTS_PER_KIND,
      );
    });

    it("builds a readable variant label", () => {
      const variant = {
        id: "v1",
        product_master_id: "m1",
        supplier_id: "s1",
        sku: "SKU-1",
        ean: null,
        display_name: "Mancuerna 10 kg",
        brand: "ProFit",
        brand_display: null,
        specs: [],
        latest_price: null,
        source_page: null,
        source_pages: [],
      } satisfies ProductVariant;

      expect(variantSearchLabel(variant)).toBe("Mancuerna 10 kg · ProFit");
    });
  });
});
